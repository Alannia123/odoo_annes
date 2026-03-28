# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AlaFcmToken(models.Model):
    _name = "ala.fcm.token"
    _description = "ALA FCM Device Token"
    _rec_name = "token"
    _order = "write_date desc"

    token = fields.Char(required=True, index=True)
    os = fields.Selection(
        [("android", "Android"), ("ios", "iOS"), ("web", "Web")],
        default="android",
        required=True,
        index=True,
    )
    device_name = fields.Char()
    user_id = fields.Many2one("res.users", ondelete="cascade", index=True)
    active = fields.Boolean(default=True, index=True)
    last_seen = fields.Datetime(default=fields.Datetime.now, index=True)

    _sql_constraints = [
        ("uniq_token", "unique(token)", "This FCM token already exists."),
    ]

    def action_deactivate(self):
        self.write({"active": False})

    def action_activate(self):
        self.write({"active": True})
