# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AlaDashboardAnnouncement(models.Model):
    """Announcements published by the office / principal and shown as a
    running ticker on the teacher dashboard (web + Android WebView)."""
    _name = "ala.dashboard.announcement"
    _description = "Teacher Dashboard Announcement"
    _order = "sequence, id desc"

    name = fields.Char(string="Title", required=True)
    message = fields.Text(string="Announcement", required=True)
    sequence = fields.Integer(default=10)
    priority = fields.Selection([
        ('normal', 'Normal'),
        ('high', 'Important'),
    ], default='normal', required=True,
        help="Important announcements are highlighted in the ticker.")
    date_start = fields.Date(
        string="Display From", required=True,
        default=fields.Date.context_today)
    date_end = fields.Date(
        string="Display Until",
        help="Leave empty to keep the announcement running indefinitely.")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env.company)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_end and rec.date_start and \
                    rec.date_end < rec.date_start:
                raise ValidationError(
                    "'Display Until' cannot be earlier than 'Display From'.")

    @api.model
    def get_running_announcements(self):
        """Active announcements inside their display window, ordered for
        the ticker. Called from the dashboard payload builder; safe for
        REST/mobile consumption (plain dicts only)."""
        today = fields.Date.context_today(self)
        announcements = self.sudo().search([
            ('date_start', '<=', today),
            '|', ('date_end', '=', False), ('date_end', '>=', today),
            ('company_id', 'in', (False, self.env.company.id)),
        ], order='sequence, id desc', limit=20)
        return [{
            'id': announcement.id,
            'name': announcement.name,
            'message': announcement.message,
            'priority': announcement.priority,
        } for announcement in announcements]
