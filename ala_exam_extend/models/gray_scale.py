# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# Report-card bands, identical to the selection already used on
# ala.education.subject / ala.education.class.
REPORT_CARD_BANDS = [
    ('nur', 'NUR'), ('lkg', 'LKG'), ('ukg', 'UKG'),
    ('onetwo', '1-2 STD'), ('threefour', '3-4 STD'), ('five', '5 STD'),
    ('sixeight', '6-8 STD'), ('ninten', '9-10 STD'),
]


class EducationGradeScale(models.Model):
    """Configurable grade band (replaces the hard-coded AA/A+/A/B/C/D ladder).

    A scale row with an empty ``type`` applies to every band; a row with a
    ``type`` overrides the generic row for that band only.
    """
    _name = 'ala.education.grade.scale'
    _description = 'Grade Scale'
    _order = 'type, min_percent desc'

    name = fields.Char(string='Grade', required=True, help='Grade label, e.g. A+.')
    sequence = fields.Integer(default=10)
    type = fields.Selection(
        REPORT_CARD_BANDS, string='Report Card Band',
        help='Leave empty to apply this grade to all bands.')
    min_percent = fields.Float(
        string='Min %', required=True,
        help='Lowest percentage (inclusive) that earns this grade.')
    max_percent = fields.Float(
        string='Max %', default=100.0,
        help='Highest percentage for this grade (display only).')
    remark = fields.Char(string='Remark', help='Optional descriptor, e.g. Outstanding.')
    is_pass = fields.Boolean(string='Is Pass', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    @api.constrains('min_percent', 'max_percent')
    def _check_range(self):
        for rec in self:
            if rec.min_percent > rec.max_percent:
                raise ValidationError(
                    _('Grade "%s": Min %% cannot be greater than Max %%.') % rec.name)

    @api.model
    def get_grade(self, percent, band=False):
        """Resolve the grade record for ``percent`` within a band.

        Picks the highest band-specific bracket whose ``min_percent`` is at
        or below ``percent``; falls back to the generic (no-band) scale.
        Boundary-overlap-safe because matching ignores ``max_percent``.
        """
        base = [('min_percent', '<=', percent)]
        if band:
            grade = self.search(
                [('type', '=', band)] + base, order='min_percent desc', limit=1)
            if grade:
                return grade
        return self.search(
            [('type', '=', False)] + base, order='min_percent desc', limit=1)