# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    faculty_ids = fields.One2many(
        'ala.education.faculty', 'employee_id', string='Faculty Records',
        help='Technical inverse used to track roll seq changes')
    faculty_roll_no = fields.Integer(
        string='Faculty Roll Seq', copy=False, store=True, index=True,
        compute='_compute_faculty_details',
        help='Attendance roll sequence, synced from the linked '
             'Faculty record (roll_seq). Stored so sheets and dashboards '
             'can search and sort on it.')
    date_of_join = fields.Date(
        string='Date of Joining', store=True,
        compute='_compute_faculty_details',
        help='Synced from the linked Faculty record')
    faculty_attendance_active = fields.Boolean(
        string='Include in Faculty Attendance', default=False,
        help='Enable to include this employee in daily faculty '
             'attendance sheets.')

    @api.depends('faculty_ids.roll_seq', 'faculty_ids.date_of_join')
    def _compute_faculty_details(self):
        for rec in self:
            faculty = rec.faculty_ids[:1]
            rec.faculty_roll_no = faculty.roll_seq if faculty else 0
            rec.date_of_join = faculty.date_of_join if faculty else False
