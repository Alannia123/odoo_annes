# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EducationAcademicYear(models.Model):
    """For managing academic year of institution"""
    _name = 'ala.education.academic.year'
    _description = 'Academic Year'
    _order = 'sequence asc'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create and assign sequence for new academic year"""
        for vals in vals_list:
            if not vals.get('sequence'):
                vals['sequence'] = self.env['ir.sequence'].next_by_code(
                    'ala.education.academic.year'
                ) or '/'
        return super(EducationAcademicYear, self).create(vals_list)

    def unlink(self):
        """Return validation error on deleting the academic year"""
        for rec in self:
            raise ValidationError(
                _("Academic Year can not be deleted, You only can "
                  "Archive it."))

    name = fields.Char(string='Name', required=True,
                       help='Name of academic year')
    sequence = fields.Integer(string='Sequence', required=True, readonly=True,
                              help="Sequence of academic year")
    ay_start_date = fields.Date(string='Start date', required=True,
                                help='Starting date of academic year')
    ay_end_date = fields.Date(string='End date', required=True,
                              help='Ending of academic year')
    ay_description = fields.Text(string='Description',
                                 help="Description about the academic year")
    enable = fields.Boolean(
        string='Active', default=True,
        help="If unchecked, it will allow you to hide the Academic "
             "Year without removing it.")
    next_academic_year = fields.Boolean(
        string="Next Academic Year",
        help="Enable this flag for the upcoming academic year to use as default in forms."
    )
    total_no_of_working_days = fields.Integer('Total No of Working Days', required=True, tracking=True)

    _sql_constraints = [
        ('unique_enabled_year', 'UNIQUE(enable)',
         'Only one Academic Year can be enabled at a time.')
    ]

    _sql_constraints = [
        ('unique_next_academic_year', 'UNIQUE(next_academic_year)',
         'Only one Next Academic Year can be enabled at a time.')
    ]

    @api.constrains('ay_start_date', 'ay_end_date')
    def validate_date(self):
        """Checking the start and end dates of the syllabus,
        raise warning if start date is not anterior"""
        for rec in self:
            if rec.ay_start_date >= rec.ay_end_date:
                raise ValidationError(
                    _('Start date must be Anterior to End date'))
