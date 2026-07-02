# -*- coding: utf-8 -*-
"""Razorpay glue for ``ala.student.fee.line``.

Design: Razorpay does NOT implement its own accounting. When a payment is
confirmed it calls the fee module's existing ``action_create_invoice`` so the
invoice + account.payment + reconciliation + ``payment_status = 'paid'`` are
produced exactly like a manual payment. The only Razorpay-specific bits are the
order/payment ids and an idempotency guard.

Settlement is triggered from three channels (website redirect, webhook, Android
verify) and must run at most once per line -> a DB row lock serialises them.
"""

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class AlaStudentFeeLine(models.Model):
    _inherit = "ala.student.fee.line"

    razorpay_order_id = fields.Char(
        string="Razorpay Order ID", index=True, copy=False)
    razorpay_payment_id = fields.Char(
        string="Razorpay Payment ID", copy=False)
    razorpay_payment_state = fields.Selection(
        selection=[
            ("none", "Not Started"),
            ("pending", "Pending"),
            ("paid", "Paid"),
            ("failed", "Failed"),
        ],
        string="Razorpay State", default="none", index=True, copy=False)

    # ------------------------------------------------------------------
    # Amount actually charged online  (must match what the invoice bills)
    # action_create_invoice bills amount_to_paid + fine_amount, so charge that.
    # ------------------------------------------------------------------
    def _razorpay_amount_paise(self):
        self.ensure_one()
        payable = (self.amount_to_paid or 0.0) + (self.fine_amount or 0.0)
        return int(round(payable * 100))

    def _razorpay_journal(self):
        """Bank journal used for the online payment.

        Prefer a dedicated journal set in Settings (razorpay.journal_id); else
        fall back to the first bank journal of the company.
        """
        icp = self.env["ir.config_parameter"].sudo()
        jid = icp.get_param("razorpay.journal_id")
        if jid:
            journal = self.env["account.journal"].browse(int(jid)).exists()
            if journal:
                return journal
        return self.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", self.env.company.id)],
            limit=1)

    def _razorpay_set_pending(self, order_id):
        self.ensure_one()
        self.write({
            "razorpay_order_id": order_id,
            "razorpay_payment_state": "pending",
        })

    def _razorpay_mark_failed(self):
        for line in self:
            if not line.invoice_id and line.payment_status != "paid":
                line.razorpay_payment_state = "failed"

    @api.model
    def _razorpay_line_from_order(self, order_id):
        if not order_id:
            return self.browse()
        return self.search([("razorpay_order_id", "=", order_id)], limit=1)

    # ------------------------------------------------------------------
    # The single, idempotent settlement entry point
    # ------------------------------------------------------------------
    def _razorpay_settle(self, payment_id):
        """Create the invoice/payment for this line, exactly once.

        Returns True if this call performed the settlement, False if it was
        already settled (so callers can stay quiet on the duplicate).
        """
        self.ensure_one()

        # Serialise concurrent settlement (webhook vs browser redirect vs app
        # verify). The row lock blocks the other transaction until this one
        # commits; the loser then re-reads invoice_id and bails.
        self.env.cr.execute(
            "SELECT id FROM ala_student_fee_line WHERE id = %s FOR UPDATE",
            [self.id])
        self.invalidate_recordset(
            ["invoice_id", "payment_status", "razorpay_payment_state"])

        if self.invoice_id or self.payment_status == "paid":
            if payment_id and not self.razorpay_payment_id:
                self.razorpay_payment_id = payment_id
            if self.razorpay_payment_state != "paid":
                self.razorpay_payment_state = "paid"
            return False

        # Mirror the manual flow's pre-step: set mode + journal, then reuse the
        # module's own invoice builder so accounting stays identical.
        journal = self._razorpay_journal()
        self.write({
            "payment_mode": "online",
            "journal_id": journal.id if journal else self.journal_id.id,
            "razorpay_payment_id": payment_id,
            "razorpay_payment_state": "paid",
        })

        today = fields.Date.context_today(self)
        self.action_create_invoice([self.id], today)  # sets invoice_id + paid

        if self.invoice_id and payment_id:
            self.invoice_id.message_post(
                body=_("Paid online via Razorpay. Payment ID: %s") % payment_id)
            # Helps bank reconciliation: stamp the gateway reference.
            if "payment_reference" in self.invoice_id._fields:
                self.invoice_id.payment_reference = payment_id
        _logger.info("Razorpay settled fee line %s (payment %s, invoice %s)",
                     self.id, payment_id, self.invoice_id.id)
        return True
