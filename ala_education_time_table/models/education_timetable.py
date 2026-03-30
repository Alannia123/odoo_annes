# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
import logging
import requests

_logger = logging.getLogger(__name__)


class AlaEducationTimetable(models.Model):
    _name = 'ala.education.timetable'
    _description = 'Timetable'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(string='Active', default=True, help='Set to False to deactivate the timetable.')
    name = fields.Char(string='Name', tracking=True, help='Generated name based on class, division and academic year.')
    class_division_id = fields.Many2one(
        'ala.education.class.division',
        string='Class',
        required=True,
        help='Select the class and division for the timetable.',
    )
    class_name_id = fields.Many2one(
        'ala.education.class',
        string='Standard',
        related='class_division_id.class_id',
        store=True,
        readonly=True,
    )
    division_name_id = fields.Many2one(
        'ala.education.division',
        string='Division',
        related='class_division_id.division_id',
        store=True,
        readonly=True,
    )
    academic_year_id = fields.Many2one(
        'ala.education.academic.year',
        string='Academic Year',
        related='class_division_id.academic_year_id',
        store=True,
        readonly=True,
        help='Academic year of the class.',
    )
    timetable_mon_ids = fields.One2many('ala.education.timetable.schedule', 'timetable_id', string='Monday Timetable', domain=[('week_day', '=', '0')])
    timetable_tue_ids = fields.One2many('ala.education.timetable.schedule', 'timetable_id', string='Tuesday Timetable', domain=[('week_day', '=', '1')])
    timetable_wed_ids = fields.One2many('ala.education.timetable.schedule', 'timetable_id', string='Wednesday Timetable', domain=[('week_day', '=', '2')])
    timetable_thur_ids = fields.One2many('ala.education.timetable.schedule', 'timetable_id', string='Thursday Timetable', domain=[('week_day', '=', '3')])
    timetable_fri_ids = fields.One2many('ala.education.timetable.schedule', 'timetable_id', string='Friday Timetable', domain=[('week_day', '=', '4')])
    timetable_sat_ids = fields.One2many('ala.education.timetable.schedule', 'timetable_id', string='Saturday Timetable', domain=[('week_day', '=', '5')])
    timetable_sun_ids = fields.One2many('ala.education.timetable.schedule', 'timetable_id', string='Sunday Timetable', domain=[('week_day', '=', '6')])
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    pdf_file = fields.Binary(string='Upload Timetable', attachment=True)
    file_name = fields.Char('File Name')
    preview_image = fields.Binary(string='PDF Preview', readonly=True)
    pre_file_name = fields.Char('Preview File Name')
    facebook_photo_url = fields.Char('Facebook Photo URL')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft', tracking=True)

    def action_set_to_post(self):
        for rec in self:
            if rec.pdf_file:
                rec.state = 'done'

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def upload_photo_to_facebook(self, image_data, caption=''):
        page_access_token = 'YOUR_PAGE_ACCESS_TOKEN'
        page_id = 'YOUR_PAGE_ID'
        base64.b64encode(image_data).decode('utf-8')
        url = f'https://graph.facebook.com/{page_id}/photos'
        payload = {
            'caption': caption,
            'access_token': page_access_token,
            'published': 'true',
        }
        files = {'source': image_data}
        response = requests.post(url, data=payload, files=files, timeout=60)
        if response.status_code == 200:
            res_json = response.json()
            photo_id = res_json.get('id')
            return f'https://www.facebook.com/{photo_id}' if photo_id else None
        _logger.error('Facebook upload failed: %s', response.text)
        return None

    @api.onchange('pdf_file')
    def _generate_preview(self):
        for rec in self:
            if rec.pdf_file:
                rec.preview_image = rec.pdf_file
                rec.pre_file_name = rec.file_name
            else:
                rec.preview_image = False
                rec.pre_file_name = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('class_division_id') and (not vals.get('name') or vals.get('name') in ('/', 'New')):
                class_division = self.env['ala.education.class.division'].browse(vals['class_division_id'])
                vals['name'] = '/'.join(filter(None, [
                    class_division.class_id.name,
                    class_division.name,
                    class_division.academic_year_id.name,
                ]))
        return super().create(vals_list)

    @api.constrains('class_division_id', 'academic_year_id')
    def _check_class_division_id(self):
        for record in self:
            duplicate_records = self.search([
                ('class_division_id', '=', record.class_division_id.id),
                ('academic_year_id', '=', record.academic_year_id.id),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate_records:
                raise ValidationError(_('Timetable for %s already exists') % record.class_division_id.display_name)
