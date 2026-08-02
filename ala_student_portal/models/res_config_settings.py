# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    razorpay_test_mode = fields.Boolean(
        string="Razorpay Test Mode",
        config_parameter="razorpay.test_mode", default=True)
    razorpay_key_id = fields.Char(
        string="Razorpay Key ID",
        config_parameter="razorpay.key_id")
    razorpay_key_secret = fields.Char(
        string="Razorpay Key Secret",
        config_parameter="razorpay.key_secret")
    razorpay_webhook_secret = fields.Char(
        string="Razorpay Webhook Secret",
        config_parameter="razorpay.webhook_secret")
    razorpay_journal_id = fields.Many2one(
        "account.journal",
        string="Razorpay Bank Journal",
        domain="[('type', '=', 'bank')]",
        config_parameter="razorpay.journal_id",
        help="Bank journal used to record online payments received via "
             "Razorpay. Leave empty to use the first bank journal.")
    razorpay_fee_bearer = fields.Selection(
        selection=[
            ("platform", "School absorbs gateway fee"),
            ("customer", "Payer pays gateway fee"),
        ],
        string="Gateway Fee Bearer",
        default="platform",
        config_parameter="razorpay.fee_bearer",
        help="Customer = Razorpay adds its fee on top at checkout and collects it "
             "from the payer; the school is settled the full face value. Requires "
             "Customer Fee Bearer to be enabled on the Razorpay account.",
    )

    ala_principal_user_id = fields.Many2one(
        "res.users",
        string="Principal",
        config_parameter="ala_student_portal.principal_user_id",
        domain="[('share', '=', False)]",
        help="Internal user notified whenever a parent submits feedback "
             "from the student portal.")
