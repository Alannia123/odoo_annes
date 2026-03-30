# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AlaTimetablePeriod(models.Model):
    _name = 'ala.timetable.period'
    _description = 'Timetable Period'
    _order = 'time_from, id'

    name = fields.Char(string='Name', required=True)
    time_from = fields.Float(string='From', required=True, index=True)
    time_to = fields.Float(string='To', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.constrains('time_from', 'time_to')
    def _check_time_range(self):
        for rec in self:
            if rec.time_from >= rec.time_to:
                raise ValidationError(_('Start time must be before end time.'))
