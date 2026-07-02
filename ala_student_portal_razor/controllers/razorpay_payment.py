# -*- coding: utf-8 -*-
import json
import logging

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    import razorpay
except ImportError:  # pragma: no cover
    razorpay = None
    _logger.warning("python 'razorpay' not installed: run `pip install razorpay`")

LINE_MODEL = "ala.student.fee.line"


class AlaRazorpayController(http.Controller):
    """One Razorpay integration serving both website and Android.

    Website : /my/fees/pay/<id>  -> renders auto-opening checkout (Checkout.js)
              /my/fees/pay/return -> browser redirect after payment (UX)
    Android : /api/razorpay/order -> JSON, returns order for the native SDK
              /api/razorpay/verify -> JSON, verifies signature post-payment
    Both    : /razorpay/webhook  -> AUTHORITATIVE settlement (server-to-server)

    Every confirmation path ends in line._razorpay_settle(), which is
    idempotent, so duplicates across channels never create a second invoice.
    """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _rzp_client(self):
        if razorpay is None:
            raise ValueError("razorpay library not installed")
        icp = request.env["ir.config_parameter"].sudo()
        key_id = icp.get_param("razorpay.key_id")
        key_secret = icp.get_param("razorpay.key_secret")
        if not (key_id and key_secret):
            raise ValueError("Razorpay credentials not configured")
        return razorpay.Client(auth=(key_id, key_secret)), key_id

    def _owned_line(self, line_id):
        """Return the fee line only if it belongs to the logged-in parent."""
        line = request.env[LINE_MODEL].sudo().browse(int(line_id))
        if not line.exists():
            return False
        if line.student_id.partner_id.id != request.env.user.partner_id.id:
            _logger.warning("User %s tried to pay foreign fee line %s",
                            request.env.user.id, line.id)
            return False
        return line

    def _create_order(self, line):
        """Create a Razorpay order for a line and stamp it as pending."""
        client, key_id = self._rzp_client()
        amount_paise = line._razorpay_amount_paise()
        if amount_paise <= 0:
            raise ValueError("Invalid payable amount")
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": "feeline-%s" % line.id,
            "payment_capture": 1,
            "notes": {"fee_line_id": str(line.id)},
        })
        line._razorpay_set_pending(order["id"])
        return order, key_id, amount_paise

    def _verify_payment_signature(self, order_id, payment_id, signature):
        client, _ = self._rzp_client()
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })

    # ==================================================================
    # WEBSITE  (Checkout.js)
    # ==================================================================
    @http.route(["/my/fees/pay/<int:line_id>"], type="http",
                auth="user", website=True)
    def fees_pay(self, line_id, **kw):
        line = self._owned_line(line_id)
        if not line:
            return request.redirect("/my/fees")
        if line.invoice_id or line.payment_status == "paid":
            return request.redirect("/my/fees?payment=already")
        try:
            order, key_id, amount_paise = self._create_order(line)
        except ValueError as e:
            _logger.warning("Razorpay order failed: %s", e)
            return request.redirect("/my/fees?payment=config")

        base_url = request.env["ir.config_parameter"].sudo().get_param(
            "web.base.url")
        partner = request.env.user.partner_id
        return request.render("ala_student_portal.razorpay_checkout_page", {
            "key_id": key_id,
            "order_id": order["id"],
            "amount": amount_paise,
            "school_name": "St. Anne's Convent School",
            "description": line.fee_description or "School Fee",
            "callback_url": "%s/my/fees/pay/return" % base_url,
            "prefill_email": partner.email or "",
            "prefill_contact": partner.phone or "",
        })

    @http.route(["/my/fees/pay/return"], type="http", auth="user",
                methods=["POST"], csrf=False, website=True)
    def fees_pay_return(self, **post):
        order_id = post.get("razorpay_order_id")
        try:
            self._verify_payment_signature(
                order_id, post.get("razorpay_payment_id"),
                post.get("razorpay_signature"))
        except Exception:
            _logger.warning("Razorpay redirect signature failed (order %s)",
                            order_id)
            return request.redirect("/my/fees?payment=failed")
        line = request.env[LINE_MODEL].sudo()._razorpay_line_from_order(order_id)
        if line:
            line._razorpay_settle(post.get("razorpay_payment_id"))
        return request.redirect("/my/fees?payment=success")

    # ==================================================================
    # ANDROID  (native Razorpay SDK)
    # ==================================================================
    @http.route(["/api/razorpay/order"], type="json", auth="user",
                methods=["POST"], csrf=False)
    def api_create_order(self, **kw):
        """App calls this, then opens the Razorpay Android Checkout with the
        returned order_id + key_id. Body: {"fee_line_id": <id>}."""
        params = kw or {}
        line = self._owned_line(params.get("fee_line_id"))
        if not line:
            return {"status": "error", "message": "Fee line not found"}
        if line.invoice_id or line.payment_status == "paid":
            return {"status": "already_paid", "fee_line_id": line.id}
        try:
            order, key_id, amount_paise = self._create_order(line)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        partner = request.env.user.partner_id
        return {
            "status": "ok",
            "key_id": key_id,
            "order_id": order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "name": "St. Anne's Convent School",
            "description": line.fee_description or "School Fee",
            "fee_line_id": line.id,
            "prefill": {
                "email": partner.email or "",
                "contact": partner.phone or partner.mobile or "",
            },
        }

    @http.route(["/api/razorpay/verify"], type="json", auth="user",
                methods=["POST"], csrf=False)
    def api_verify(self, **kw):
        """App posts the SDK result here for immediate UX confirmation.
        Settlement is still idempotent (webhook may have run first).
        Body: {razorpay_order_id, razorpay_payment_id, razorpay_signature}."""
        params = kw or {}
        order_id = params.get("razorpay_order_id")
        payment_id = params.get("razorpay_payment_id")
        try:
            self._verify_payment_signature(
                order_id, payment_id, params.get("razorpay_signature"))
        except Exception:
            line = request.env[LINE_MODEL].sudo()._razorpay_line_from_order(
                order_id)
            if line:
                line._razorpay_mark_failed()
            return {"status": "failed", "paid": False}
        line = request.env[LINE_MODEL].sudo()._razorpay_line_from_order(order_id)
        if not line:
            return {"status": "failed", "paid": False}
        line._razorpay_settle(payment_id)
        return {
            "status": "success",
            "paid": line.payment_status == "paid",
            "invoice_id": line.invoice_id.id or False,
            "fee_line_id": line.id,
        }

    # ==================================================================
    # WEBHOOK  (authoritative, server-to-server, works for web AND app)
    # ==================================================================
    @http.route(["/razorpay/webhook"], type="http", auth="public",
                methods=["POST"], csrf=False)
    def razorpay_webhook(self, **kw):
        icp = request.env["ir.config_parameter"].sudo()
        webhook_secret = icp.get_param("razorpay.webhook_secret")
        raw = request.httprequest.data
        signature = request.httprequest.headers.get("X-Razorpay-Signature")
        try:
            client, _ = self._rzp_client()
            client.utility.verify_webhook_signature(
                raw.decode("utf-8"), signature, webhook_secret)
        except Exception:
            _logger.warning("Razorpay webhook signature verification failed")
            return request.make_response("invalid signature", status=400)

        try:
            event = json.loads(raw)
        except (ValueError, TypeError):
            return request.make_response("bad payload", status=400)

        evt = event.get("event")
        entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = entity.get("order_id")
        Line = request.env[LINE_MODEL].sudo()
        if evt in ("payment.captured", "order.paid"):
            line = Line._razorpay_line_from_order(order_id)
            if line:
                line._razorpay_settle(entity.get("id"))
        elif evt == "payment.failed":
            line = Line._razorpay_line_from_order(order_id)
            if line:
                line._razorpay_mark_failed()
        return request.make_response("ok", status=200)
