# -*- coding: utf-8 -*-

from odoo import models


class EducationExam(models.Model):
    _inherit = 'ala.education.exam'

    def action_confirm_exam(self):
        """Create one valuation per division x subject, using each subject's
        own pattern resolved by the exam type's cycle (exam_order) instead of
        a single uniform max/pass mark.
        """
        self.ensure_one()
        exam_order = self.exam_type_id.exam_order
        self.name = '%s - %s %s' % (
            self.class_id.name, self.exam_type_id.name, self.academic_year_id.name)

        Valuation = self.env['ala.education.exam.valuation']
        divisions = self.env['ala.education.class.division'].search([
            ('class_id', '=', self.class_id.id),
            ('current_year', '=', True),
        ])

        for subject in self.subject_line_ids:
            curr_subject = self.class_id.subject_ids.filtered(
                lambda s: s.subject_id.id == subject.subject_id.id)[:1]
            if not curr_subject:
                continue
            pattern = curr_subject.get_pattern(exam_order)
            for div in divisions:
                valuation = Valuation.create({
                    'exam_id': self.id,
                    'division_id': div.id,
                    'class_id': self.class_id.id,
                    'subject_id': subject.subject_id.id,
                    'mark': pattern['max_mark'],
                    'pass_mark': pattern['pass_mark'],
                    'exam_max': pattern['exam_max'],
                    'assign_max': pattern['assign_max'],
                    'evaluation_mode': pattern['mode'],
                    'faculty_ids': [(6, 0, curr_subject.faculty_ids.ids)],
                })
                valuation.action_create_mark_sheet()
        self.state = 'ongoing'