# -*- coding: utf-8 -*-
from odoo import models, fields

class ResUsers(models.Model):
    _inherit = "res.users"

    fcm_token_ids = fields.One2many(
        "ala.fcm.token",
        "user_id",
        string="ALA FCM Tokens",
        readonly=True,
    )
    fcm_token_count = fields.Integer(
        string="FCM Token Count",
        compute="_compute_fcm_token_count",
    )

    # fcm_token = fields.Char("FCM Token")

    def _compute_fcm_token_count(self):
        for user in self:
            user.fcm_token_count = len(user.fcm_token_ids)
