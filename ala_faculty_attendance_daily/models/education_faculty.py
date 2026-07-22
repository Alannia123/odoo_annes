# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

WORKED = ('present', 'on_duty')


class EducationFaculty(models.Model):
    _inherit = 'ala.education.faculty'

    attendance_rate = fields.Float(
        string='Attendance %', compute='_compute_attendance_rate',
        help='Attendance rate of the related employee for the current month '
             '(Present + On Duty over marked days)')

    def _compute_attendance_rate(self):
        Line = self.env['ala.faculty.attendance.sheet.line'].sudo()
        today = fields.Date.context_today(self)
        for rec in self:
            rate = 0.0
            if rec.employee_id:
                groups = Line._read_group(
                    [('employee_id', '=', rec.employee_id.id),
                     ('date', '>=', today.replace(day=1)),
                     ('date', '<=', today)],
                    ['status'], ['__count'])
                counts = {status: count for status, count in groups}
                total = sum(counts.values())
                if total:
                    worked = sum(counts.get(s, 0) for s in WORKED)
                    rate = round(worked / total * 100, 1)
            rec.attendance_rate = rate

    @api.constrains('roll_seq', 'employee_id')
    def _check_roll_seq_unique(self):
        for rec in self:
            if not rec.roll_seq or not rec.employee_id:
                continue
            duplicate = self.search([
                ('id', '!=', rec.id),
                ('roll_seq', '=', rec.roll_seq),
                ('employee_id', '!=', False),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    'Roll Seq %(roll)s is already assigned to faculty '
                    '%(name)s.', roll=rec.roll_seq, name=duplicate.name))

    def action_open_attendance_dashboard(self):
        self.ensure_one()
        if not self.employee_id:
            raise UserError(_('Link a Related Employee first.'))
        return {
            'type': 'ir.actions.client',
            'tag': 'ala_faculty_attendance_dashboard',
            'name': _('%s — Attendance') % self.name,
            'context': {
                'mfa_employee_id': self.employee_id.id,
                'mfa_employee_name': self.employee_id.name,
            },
        }
