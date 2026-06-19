# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class SchoolPolicyPages(http.Controller):
    """Public routes for the policy pages Razorpay requires.

    Each route uses website=True so the page is wrapped in the active
    website theme/layout, auth='public' so logged-out visitors (and the
    Razorpay reviewer) can open it, and sitemap=True so it is discoverable.
    """

    @http.route("/fees", type="http", auth="public", website=True, sitemap=True)
    def fees(self, **kwargs):
        return request.render("ala_website.fees_page")

    @http.route(
        "/refund-policy", type="http", auth="public", website=True, sitemap=True
    )
    def refund_policy(self, **kwargs):
        return request.render("ala_website.refund_policy_page")

    @http.route(
        "/privacy-policy-razor", type="http", auth="public", website=True, sitemap=True
    )
    def privacy_policy(self, **kwargs):
        return request.render("ala_website.privacy_policy_page")

    @http.route(
        "/terms-and-conditions",
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def terms_and_conditions(self, **kwargs):
        return request.render("ala_website.terms_page")

    @http.route(
        "/shipping-policy", type="http", auth="public", website=True, sitemap=True
    )
    def shipping_policy(self, **kwargs):
        return request.render("ala_website.shipping_policy_page")