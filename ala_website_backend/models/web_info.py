# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, date
from random import randint


class WebAnouInfo(models.Model):
    _name = 'ala.web.info'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=False, default='New')
    date = fields.Date('Date', default=lambda self: date.today())
    anounce = fields.Char('Annoucements')
    enable = fields.Boolean('Enable/Disable')
    color = fields.Char(string="Color HEX", default='#4d0000')

    def publish_announce(self):
        for rec in self:
            rec.enable = True

            # 🎓 Formal notification body
            message_body = (
                "Dear Parents,\n\n"
                f"{rec.anounce}\n\n"
                "Regards,\n"
                "SAS School"
            )

            response = self.env['firebase.notification'].send_android_notification(
                            title="📢 ST.ANNE'S School Announcement",
                            body=message_body
                                )
            print('222222222222------------------',response)

    def unpublish_announce(self):
        self.enable = False



class BanInfo(models.Model):
    _name = 'ala.banner.info'

    name = fields.Char('Name', required=False, default='New')
    date = fields.Datetime('Date', default=lambda self: fields.Datetime.now())
    info = fields.Char('Annoucements')
    enable = fields.Boolean('Enable/Disable')
