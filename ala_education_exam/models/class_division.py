# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class EducationClassDivision(models.Model):
    """
        Model representing Education Exams.

        This model stores information about education exams, including details like exam name,
        associated class, division, exam type, start and end dates, and related subjects.
    """
    _inherit = 'ala.education.class.division'
    _description = 'Education Class Division'

    def get_all_class_students(self):
        academic_year_id = self.env['ala.education.academic.year'].search([('enable', '=', True)], limit=1).id
        return academic_year_id

    def get_current_exam(self):
        marksheet_exam_type = self.env['ala.education.exam.type'].search([('prepare_marksheet', '=', True)], limit=1)
        marksheet_exam = self.env['ala.education.exam'].search([('exam_type_id', '=', marksheet_exam_type.id),
                                                            ('class_id', '=', self.class_id.id)], limit=1)
        return marksheet_exam

    def get_current_exam_lines(self, exam):
        # exam_lines = self.env['ala.education.exam.results'].search([('exam_id', '=', exam.id),
        #                                                     ('division_id', '=', self.id)], order='total_mark_scored desc')
        # return exam_lines
        exam_lines = self.env['ala.education.exam.results'].search([
            ('exam_id', '=', exam.id),
            ('division_id', '=', self.id)
        ])

        # Custom sort by numeric roll_no if possible
        exam_lines = sorted(
            exam_lines,
            key=lambda r: int(
                r.student_id.roll_no) if r.student_id.roll_no and r.student_id.roll_no.isdigit() else r.student_id.roll_no
        )
        return exam_lines



class EducationStudent(models.Model):
    """
        Model representing Education Exams.

        This model stores information about education exams, including details like exam name,
        associated class, division, exam type, start and end dates, and related subjects.
    """
    _inherit = 'ala.education.student'
    _description = 'Education Student'


    def _get_exams_type(self):
        return self.env['ala.education.exam.type'].sudo().search([])

    def get_members(self):
        return self.env['ala.school.members'].search([])



    def _get_exams_aca_class(self):
        # Execute SQL to get exam IDs
        class_id = self.class_division_id.class_id.id
        self.env.cr.execute("""
                    SELECT id
                    FROM ala_education_exam
                    WHERE class_id = %s
                """, (class_id,))
        # Fetch all IDs as a tuple
        exam_ids_tuple = tuple(row[0] for row in self.env.cr.fetchall())
        # Convert IDs to a recordset (like ORM search result)
        q_all_exams = self.env['ala.education.exam'].sudo().browse(exam_ids_tuple)
        print('-------------',q_all_exams)
        return q_all_exams



    # def _get_exam_academic_year(self):
    #     # Execute SQL to get exam result IDs
    #     student_id = self.id
    #     self.env.cr.execute("""
    #                     SELECT e.id
    #                     FROM education_exam_results e
    #                     JOIN education_academic_year y ON e.academic_year_id = y.id
    #                     WHERE y.enable = TRUE
    #                       AND e.student_id = %s
    #                       AND e.exam_id IS NOT NULL
    #                 """, (student_id,))
    #     # Fetch all IDs
    #     exam_result_ids = [row[0] for row in self.env.cr.fetchall()]
    #     # Convert IDs to a recordset (like ORM search result)
    #     q_all_exams = self.env['ala.education.exam.results'].sudo().browse(exam_result_ids)
    #     print('dddddddddddddd', q_all_exams)
    #     return q_all_exams

    def _get_exam_academic_year(self, academic_year_id=False, class_div_id=False):
        domain = [
            ('student_id', '=', self.id),
            ('exam_id', '!=', False),
        ]
        print('errrrrrrrrrrrrrrrrrrr--------',self)
        if academic_year_id:
            domain.append(('academic_year_id', '=', academic_year_id))
        if class_div_id:
            domain.append(('class_division_id', '=', class_div_id))
        print('444444444444444444444444',self.env['ala.education.exam.results'].sudo().search(domain))

        return self.env['ala.education.exam.results'].sudo().search(domain)


    def get_gruop_marks_assign(self, group_id, half_result, annual_result):
        group_subjects = self.env['ala.education.subject'].sudo().search([('group_id', '=', group_id.id)])
        mark_sum_half = 0
        mark_sum_annual = 0
        data = {}
        if group_subjects:
            for group_sub in group_subjects:
                result_half_subject_id = half_result.subject_line_ids.filtered(lambda sub: sub.subject_id.id ==  group_sub.id)
                mark_sum_half = mark_sum_half + result_half_subject_id.mark_scored
                result_annal_subject_id = annual_result.subject_line_ids.filtered(lambda sub: sub.subject_id.id ==  group_sub.id)
                mark_sum_annual = mark_sum_annual + result_annal_subject_id.mark_scored
            halfly_mark = round(mark_sum_half / len(group_subjects), 2)
            annual_mark = round(mark_sum_annual / len(group_subjects), 2)

            data = { 'halfly_mark' : halfly_mark, 'annual_mark': annual_mark, 'gr_id': group_id.id}
        print('DDDDDDDDDDDDDDDDDDD',data)
        return data

    def get_student_marksheet(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Academic Year',
            'res_model': 'ala.student.marksheet.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
            },
        }

    # def get_student_marksheet(self):
    #     data = {
    #         'student': self.id,
    #         # 'exam': self.exam_id.id,
    #     }
    #     return self.env.ref('ala_education_exam.action_generate_rank_student_card').report_action(self.id)

    def get_half_evaluations(self):
        currect_aca_id = self.env['ala.education.academic.year'].search(
            [('enable', '=', True)], limit=1)

        stu_half_evalaution_id = self.env['ala.education.half.evaluation.line'].search([
            ('student_id', '=', self.id),
            ('academic_year_id', '=', currect_aca_id.id),
            ('evaluation_id.state', '=', 'done')
        ], limit=1)

        return stu_half_evalaution_id

    def get_annual_evaluations(self):
        currect_aca_id = self.env['ala.education.academic.year'].search(
            [('enable', '=', True)], limit=1
        )

        stu_annual_evalaution_id = self.env['ala.education.annual.evaluation.line'].search([
            ('student_id', '=', self.id),
            ('academic_year_id', '=', currect_aca_id.id),
            ('evaluation_id.state', '=', 'done')
        ], limit=1)

        return stu_annual_evalaution_id