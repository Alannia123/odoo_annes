# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import RedirectWarning


class EducationAttendanceEntry(models.Model):
    """For managing attendance details of class"""
    _name = 'ala.education.attendance.entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Students Attendance Entry'

    name = fields.Char(string='Name', default='New',
                       help="Name of the attendance")
    division_id = fields.Many2one('ala.education.class.division', domain=[('current_year', '=', True)],
                                  string='Division', required=True, tracking=True,
                                  help="Class division for attendance")
    class_id = fields.Many2one('ala.education.class', string='Class', help="Class of the attendance")
    date = fields.Date(string='Date', default=fields.Date.today, required=True, tracking=True,
                       help="Attendance date", readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             default='draft', string="State", tracking=True,
                             help="Stages of attendance")
    academic_year_id = fields.Many2one(
        'ala.education.academic.year',
        string='Academic Year',
        domain=[('enable', '=', True)],
        default=lambda self: self.env['ala.education.academic.year'].search([('enable', '=', True)], limit=1),
    )
    faculty_id = fields.Many2one('ala.education.faculty',
                                 string='Faculty',
                                 related='division_id.faculty_id',
                                 help="Faculty of the class")
    attendance_id = fields.Many2one('ala.education.attendance',
                                 string='Attendance',
                                 help="Attendance of the Division")
    company_id = fields.Many2one(
        'res.company', string='Company', help="Current Company",
        default=lambda self: self.env.company)

    @api.constrains('division_id', 'date')
    def _check_duplicate_attendance(self):
        for rec in self:
            if not rec.division_id or not rec.date:
                continue

            domain = [
                ('division_id', '=', rec.division_id.id),
                ('date', '=', rec.date),
                ('id', '!=', rec.id),
            ]

            if self.search_count(domain):
                raise ValidationError(_(
                    "Attendance Entry is already created for Division '%s' on %s."
                ) % (rec.division_id.name, rec.date))

    @api.constrains('date')
    def _check_not_holiday(self):
        for rec in self:
            holiday = self.env['ala.school.event'].search([
                ('event_date', '=', rec.date),
                ('is_holiday', '=', True)
            ], limit=1)
            if holiday:
                raise ValidationError(
                    "You cannot take attendance on %s because it is marked as a holiday (%s)."
                    % (rec.date, holiday.display_name))


    def action_attendance_done(self):
        data = {}
        self.class_id = self.division_id.class_id.id
        attendance_id = self.env['ala.education.attendance'].create({
                                                                    'division_id' : self.division_id.id,
                                                                    'class_id' : self.class_id.id,
                                                                    'academic_year_id' : self.academic_year_id.id,
                                                                    'faculty_id' : self.faculty_id.id,
                                                                                                                                        'date' : self.date,
                                                                })
        attendance_id.action_create_attendance_line()
        attendance_id.action_attendance_done()
        self.attendance_id = attendance_id.id
        self.state = 'done'

    def action_set_to_draft(self):
        for att_line in self.attendance_id.attendance_line_ids:
            att_line.state = 'draft'
            att_line.present = False
        self.attendance_id.state = 'draft'
        self.state = 'draft'

    def unlink(self):
        for record in self:
            if record.state == 'done':
                raise UserError("You cannot delete a record that is marked as Done.")
        return super().unlink()
