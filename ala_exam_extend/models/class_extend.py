# -*- coding: utf-8 -*-

from odoo import api, fields, models

# exam_order values (from ala.education.exam.type) grouped by assessment cycle.
UNIT_ORDERS = ('first', 'second')        # Unit 1 / Unit 2  -> periodic pattern
TERM_ORDERS = ('half', 'annual')         # Half-Yearly / Annual -> terminal pattern


class EducationClassSubject(models.Model):
    """Per-subject assessment pattern for the new grade configuration.

    Each class-subject carries TWO patterns because the spreadsheet defines a
    different split per cycle (e.g. English: Unit 30+20, Terminal 80+20). The
    evaluation mode is constant for the subject across both cycles.
    """
    _inherit = 'ala.education.class.subject'

    evaluation_mode = fields.Selection(
        [('mark', 'Marks'), ('grade', 'Grade Only'), ('grade_no_calc', 'Grade Only(No Calc)')],
        string='Evaluation Mode', default='mark', required=True,
        help='Grade Only subjects are still entered as raw marks; only the '
             'report card shows the derived grade instead of the number.')

    # --- Periodic / Unit pattern -------------------------------------------
    unit_exam_max = fields.Float(string='Unit Written', default=30.0)
    unit_assign_max = fields.Float(string='Unit Internal', default=20.0)
    unit_max_mark = fields.Float(
        string='Unit Total', compute='_compute_unit_max', store=True)
    unit_pass_mark = fields.Float(string='Unit Pass', default=0.0)

    # --- Terminal (Half-Yearly / Annual) pattern ---------------------------
    term_exam_max = fields.Float(string='Term Written', default=80.0)
    term_assign_max = fields.Float(string='Term Internal', default=20.0)
    term_max_mark = fields.Float(
        string='Term Total', compute='_compute_term_max', store=True)
    term_pass_mark = fields.Float(string='Term Pass', default=0.0)

    @api.depends('unit_exam_max', 'unit_assign_max')
    def _compute_unit_max(self):
        for rec in self:
            rec.unit_max_mark = rec.unit_exam_max + rec.unit_assign_max

    @api.depends('term_exam_max', 'term_assign_max')
    def _compute_term_max(self):
        for rec in self:
            rec.term_max_mark = rec.term_exam_max + rec.term_assign_max

    def get_pattern(self, exam_order):
        """Return the resolved pattern dict for a given exam_order."""
        self.ensure_one()
        if exam_order in TERM_ORDERS:
            return {
                'mode': self.evaluation_mode,
                'exam_max': self.term_exam_max,
                'assign_max': self.term_assign_max,
                'max_mark': self.term_max_mark,
                'pass_mark': self.term_pass_mark,
            }
        # default to the unit/periodic pattern for first/second (or unset)
        return {
            'mode': self.evaluation_mode,
            'exam_max': self.unit_exam_max,
            'assign_max': self.unit_assign_max,
            'max_mark': self.unit_max_mark,
            'pass_mark': self.unit_pass_mark,
        }