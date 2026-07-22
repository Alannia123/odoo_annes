# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    faculty_check_in_time = fields.Float(
        string='Faculty Check In', default=9.0,
        help='Local time (school timezone) used as check-in when a faculty '
             'attendance sheet is validated. 9.5 = 09:30.')
    faculty_check_out_time = fields.Float(
        string='Faculty Check Out', default=16.0,
        help='Local time used as check-out for a full Present day.')
    faculty_half_day_out_time = fields.Float(
        string='Faculty Half Day Out', default=12.5,
        help='Local time used as check-out for a Half Day. 12.5 = 12:30.')
