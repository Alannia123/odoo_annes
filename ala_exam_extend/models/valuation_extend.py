# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EducationExamValuation(models.Model):
    """Carry the resolved per-subject pattern onto the valuation so each
    subject can have its own caps (50 vs 100 vs grade-only)."""
    _inherit = 'ala.education.exam.valuation'

    evaluation_mode = fields.Selection(
        [('mark', 'Marks'), ('grade', 'Grade Only'), ('grade_no_calc', 'Grade Only(No Calc)')],
        string='Evaluation Mode', default='mark')
    exam_max = fields.Float(string='Written Max')
    assign_max = fields.Float(string='Internal Max')


class StudentsExamValuationLine(models.Model):
    """Mobile/REST-safe rework of the per-student mark line.

    Totals, pass/fail and grade are COMPUTED + STORED so they are correct on
    direct ORM/REST writes (the mobile app path), where onchange never fires.
    Caps are enforced with @api.constrains for the same reason.
    """
    _inherit = 'ala.exam.valuation.line'

    evaluation_mode = fields.Selection(
        related='valuation_id.evaluation_mode', store=True, readonly=True)
    percentage = fields.Float(
        string='Percentage', compute='_compute_grade', store=True)
    grade_id = fields.Many2one(
        'ala.education.grade.scale', string='Grade',
        compute='_compute_grade', store=True)
    grade_label = fields.Char(
        related='grade_id.name', string='Grade', store=True, readonly=True)
    grade = fields.Char( string='Grade', readonly=False)

    # mark_scored / pass_or_fail redefined as computed+stored (were plain
    # fields set via onchange in the base module).
    mark_scored = fields.Integer(
        string='Total Mark', compute='_compute_mark_scored',
        store=True, readonly=True)
    pass_or_fail = fields.Boolean(
        string='Pass/Fail', compute='_compute_grade', store=True, readonly=True)

    @api.depends('exam_mark', 'assign_mark')
    def _compute_mark_scored(self):
        for line in self:
            line.mark_scored = (line.exam_mark or 0) + (line.assign_mark or 0)

    @api.depends('mark_scored', 'valuation_id.mark', 'valuation_id.pass_mark',
                 'valuation_id.subject_id.type')
    def _compute_grade(self):
        Grade = self.env['ala.education.grade.scale']
        for line in self:
            valuation = line.valuation_id
            max_mark = valuation.mark or 0.0
            line.percentage = (line.mark_scored / max_mark * 100.0) if max_mark else 0.0
            line.pass_or_fail = line.mark_scored >= valuation.pass_mark
            band = valuation.subject_id.type
            line.grade_id = Grade.get_grade(line.percentage, band)

    @api.constrains('exam_mark', 'assign_mark')
    def _check_component_caps(self):
        for line in self:
            valuation = line.valuation_id
            if valuation.exam_max and line.exam_mark > valuation.exam_max:
                raise ValidationError(_(
                    'Written mark (%(got)s) exceeds the maximum of %(max)s for %(sub)s.',
                    got=line.exam_mark, max=int(valuation.exam_max),
                    sub=valuation.subject_id.name))
            if valuation.assign_max and line.assign_mark > valuation.assign_max:
                raise ValidationError(_(
                    'Internal mark (%(got)s) exceeds the maximum of %(max)s for %(sub)s.',
                    got=line.assign_mark, max=int(valuation.assign_max),
                    sub=valuation.subject_id.name))
            if not valuation.exam_max and valuation.mark \
                    and line.mark_scored > valuation.mark:
                raise ValidationError(_(
                    'Total (%(got)s) exceeds the maximum of %(max)s for %(sub)s.',
                    got=line.mark_scored, max=int(valuation.mark),
                    sub=valuation.subject_id.name))

    def _onchange_mark_scored(self):
        # Superseded by computed fields above. Kept as a plain (non-onchange)
        # method so the base module's onchange logic no longer double-runs.
        return