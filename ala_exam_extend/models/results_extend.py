# -*- coding: utf-8 -*-

from odoo import api, fields, models

# Modes whose marks are excluded from the overall percentage / totals.
NO_CALC_MODES = ('grade_no_calc',)


class EducationExamResults(models.Model):
    _inherit = 'ala.education.exam.results'

    def _apply_result_totals(self):
        """Aggregate the result, EXCLUDING no-calc subjects.

        grade_no_calc subjects still carry marks and a per-subject grade on
        their own result line, but must not influence the total pass/max/
        scored marks, the overall pass flag, or the overall percentage/grade.
        """
        self.ensure_one()
        total_pass_mark = total_max_mark = total_mark_scored = 0.0
        overall_pass = True
        for line in self.subject_line_ids:
            if line.evaluation_mode in NO_CALC_MODES:
                continue
            total_pass_mark += line.pass_mark
            total_max_mark += line.max_mark
            total_mark_scored += line.mark_scored
            if not line.pass_or_fail:
                overall_pass = False

        self.total_pass_mark = total_pass_mark
        self.total_max_mark = total_max_mark
        self.total_mark_scored = total_mark_scored
        self.overall_pass = overall_pass

        percentage = (total_mark_scored / total_max_mark * 100.0) \
            if total_max_mark else 0.0
        self.total_mark_percentage = percentage

        if total_max_mark:
            grade = self.env['ala.education.grade.scale'].get_grade(
                percentage, self.class_id.type)
            self.grade = grade.name if grade else False
        else:
            # Every subject is no-calc (e.g. a fully graded band): no overall
            # percentage or grade to report.
            self.grade = False

    @api.depends('subject_line_ids.mark_scored',
                 'subject_line_ids.pass_or_fail',
                 'subject_line_ids.evaluation_mode')
    def _total_marks_all(self):
        for results in self:
            results._apply_result_totals()

    def _total_marks_calculate_percentage(self):
        # Called explicitly from action_valuation_completed. Kept consistent
        # with the stored compute above (same exclusion, same grade scale).
        for results in self:
            results._apply_result_totals()


class ResultsSubjectLine(models.Model):
    _inherit = 'ala.results.subject.line'

    evaluation_mode = fields.Selection(
        [('mark', 'Marks'),
         ('grade', 'Grade Only'),
         ('grade_no_calc', 'Grade Only(No Calc)')],
        string='Evaluation Mode',
        compute='_compute_evaluation_mode', store=True, readonly=True)
    grade_label = fields.Char(
        string='Grade', compute='_compute_grade_label', store=True,
        help='Grade derived from this subject\'s own marks. Used for '
             'grade-only and no-calc subjects on the report card.')

    @api.depends('subject_id', 'class_id')
    def _compute_evaluation_mode(self):
        ClassSubject = self.env['ala.education.class.subject']
        for line in self:
            mode = 'mark'
            if line.subject_id and line.class_id:
                cs = ClassSubject.search([
                    ('class_id', '=', line.class_id.id),
                    ('subject_id', '=', line.subject_id.id),
                ], limit=1)
                mode = cs.evaluation_mode or 'mark'
            line.evaluation_mode = mode

    @api.depends('mark_scored', 'max_mark', 'subject_id.type')
    def _compute_grade_label(self):
        Grade = self.env['ala.education.grade.scale']
        for line in self:
            percent = (line.mark_scored / line.max_mark * 100.0) \
                if line.max_mark else 0.0
            grade = Grade.get_grade(percent, line.subject_id.type)
            line.grade_label = grade.name if grade else False