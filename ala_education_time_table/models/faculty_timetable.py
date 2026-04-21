# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
import logging
import requests

_logger = logging.getLogger(__name__)


class AlaEducationFacTimetable(models.Model):
    _name = 'ala.education.faculty.timetable'
    _description = 'Timetable'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', tracking=True, help='Generated name based on class, division and academic year.')

    faculty_id = fields.Many2one(
        'ala.education.faculty',
        string='Faculty',
        required=True,
        help='Select the class and division for the timetable.',
    )
    class_division_id = fields.Many2one(
        'ala.education.class.division',
        string='Incharge On Division',
        required=False,
        help='Select the class and division for the timetable.',
    )
    academic_year_id = fields.Many2one(
        'ala.education.academic.year',
        string='Academic Year',
        help="Select the Academic Year",
        required=True,
        default=lambda self: self.env['ala.education.academic.year'].search(
            [('enable', '=', True)], limit=1
        )
    )

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    pdf_file = fields.Binary(string='Upload Timetable', attachment=True)
    file_name = fields.Char('File Name')
    preview_image = fields.Binary(string='PDF Preview', readonly=True)
    pre_file_name = fields.Char('Preview File Name')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft', tracking=True)

    def action_set_to_post(self):
        for rec in self:
            if rec.pdf_file:
                rec.state = 'done'
            else:
                raise ValidationError('Please Upload Faculty timetable file.')

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})


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
        AcademicYear = self.env['ala.education.academic.year']
        Faculty = self.env['ala.education.faculty']

        default_academic_year = AcademicYear.search([('enable', '=', True)], limit=1)

        for vals in vals_list:
            if not vals.get('name') or vals.get('name') in ('/', 'New'):
                faculty = Faculty.browse(vals.get('faculty_id'))
                academic_year = AcademicYear.browse(vals.get('academic_year_id')) if vals.get(
                    'academic_year_id') else default_academic_year

                faculty_code = (faculty.name or '')[:4].upper().strip()
                year_name = (academic_year.name or '')[:4].upper().strip()

                vals['name'] = '/'.join(filter(None, [
                    faculty_code,
                    year_name,
                ]))

                division_id = self.env['ala.education.class.division'].search([('faculty_id', '=', faculty.id), ('academic_year_id', '=', academic_year.id)])

                # optional: ensure academic_year_id is also set in vals if missing
                if not vals.get('academic_year_id') and default_academic_year:
                    vals['academic_year_id'] = default_academic_year.id

                # optional: ensure academic_year_id is also set in vals if missing
                if division_id:
                    vals['class_division_id'] = division_id.id

        return super().create(vals_list)

    @api.constrains('faculty_id', 'academic_year_id')
    def _check_class_division_id(self):
        for record in self:
            duplicate_records = self.search([
                ('faculty_id', '=', record.faculty_id.id),
                ('academic_year_id', '=', record.academic_year_id.id),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate_records:
                raise ValidationError(_('Timetable for %s already exists') % record.faculty_id.display_name)




class AlaEducationFaculty(models.Model):
    _inherit = 'ala.education.faculty'


    def view_faculty_time_table(self):

        timetables = self.env['ala.education.faculty.timetable'].search([
            ('faculty_id', '=', self.id)
        ])

        if not timetables:
            raise ValidationError(_("No timetable found for your faculty."))

        if len(timetables) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('My Timetable'),
                'res_model': 'ala.education.faculty.timetable',
                'view_mode': 'form',
                'res_id': timetables.id,
                'target': 'current',
            }

        return {
            'type': 'ir.actions.act_window',
            'name': _('My Timetables'),
            'res_model': 'ala.education.faculty.timetable',
            'view_mode': 'tree,form',
            'domain': [('faculty_id', '=', self.id)],
            'target': 'current',
        }