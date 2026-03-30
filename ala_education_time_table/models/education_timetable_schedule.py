# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AlaEducationTimetableSchedule(models.Model):
    _name = 'ala.education.timetable.schedule'
    _description = 'Timetable Schedule'
    _rec_name = 'period_id'

    period_id = fields.Many2one('ala.timetable.period', string='Period', required=True)
    time_from = fields.Float(string='From', required=True, index=True)
    time_till = fields.Float(string='Till', required=True)
    subject_id = fields.Many2one('ala.education.subject', string='Subject', required=True)
    faculty_id = fields.Many2one('ala.education.faculty', string='Faculty', required=True)
    week_day = fields.Selection([
        ('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'), ('3', 'Thursday'),
        ('4', 'Friday'), ('5', 'Saturday'), ('6', 'Sunday'),
    ], string='Week', required=True)
    timetable_id = fields.Many2one('ala.education.timetable', string='Timetable', required=True)
    class_division_id = fields.Many2one('ala.education.class.division', string='Class', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.timetable_id and rec.class_division_id != rec.timetable_id.class_division_id:
                rec.class_division_id = rec.timetable_id.class_division_id.id
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'timetable_id' in vals:
            for rec in self:
                rec.class_division_id = rec.timetable_id.class_division_id.id
        return res

    @api.onchange('period_id')
    def _onchange_period_id(self):
        for rec in self:
            rec.time_from = rec.period_id.time_from
            rec.time_till = rec.period_id.time_to

    @api.constrains('time_from', 'time_till', 'timetable_id', 'week_day')
    def _check_overlapping_schedules(self):
        for record in self:
            if record.time_from >= record.time_till:
                raise ValidationError(_('The start time must be before the end time.'))
            overlapping_schedules = self.search([
                ('timetable_id', '=', record.timetable_id.id),
                ('week_day', '=', record.week_day),
                ('id', '!=', record.id),
                ('time_from', '<', record.time_till),
                ('time_till', '>', record.time_from),
            ], limit=1)
            if overlapping_schedules:
                raise ValidationError(_('The schedule times overlap with another schedule.'))
