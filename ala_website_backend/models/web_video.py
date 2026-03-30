# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime
import boto3
import base64
import logging
from odoo import models, fields
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WebVideo(models.Model):
    _name = 'ala.web.video'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', readonly=True,  default='New')
    date = fields.Datetime('Date', default=lambda self: fields.Datetime.now())
    user_id = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user, readonly=True)
    show_website = fields.Boolean('Show On Website')
    image_ids = fields.One2many('ala.web.video.image', 'video_id', string='Slider Images')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('web.vide') or _('New')
        return super().create(vals_list)

class WebVideoImages(models.Model):
    _name = 'ala.web.video.image'
    _description = 'Web Video Slider Images'

    video_id = fields.Many2one('ala.web.video', string="Web Video", ondelete='cascade')
    name = fields.Char('Name', required=True)
    image = fields.Binary('Image', required=True)
    sequence = fields.Integer('Sequence', default=1)



class WebVideoYt(models.Model):
    _name = 'ala.web.video.youtube'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', readonly=False,  default='New')
    date = fields.Datetime('Date', default=lambda self: fields.Datetime.now(), readonly=True)
    user_id = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user, readonly=True)
    media_url = fields.Char('Media Url', copy=False)
    school_video_url = fields.Char('School Video Url', copy=False)
    show_website = fields.Boolean('Show On Website')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('web.vide') or _('New')
        return super().create(vals_list)




