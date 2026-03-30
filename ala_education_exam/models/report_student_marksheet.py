from odoo import models

class ReportStudentMarksheet(models.AbstractModel):
    _name = 'report.ala_education_exam.report_student_rank_card_template'
    _description = 'Student Marksheet Report'

    def _get_report_values(self, docids, data=None):
        data = data or {}
        student_id = data.get('student_id')
        academic_year_id = data.get('academic_year_id')

        student = self.env['ala.education.student'].browse(student_id)
        academic_year = self.env['ala.education.academic.year'].browse(academic_year_id)
        exam_types = self.env['ala.education.exam.type'].sudo().search([])

        # Get student's class history for selected academic year
        class_history = student.class_history_ids.filtered(
            lambda h: h.academic_year_id.id == academic_year.id
        )[:1]

        aca_exams = self.env['ala.education.exam']
        if class_history and class_history.class_id:
            aca_exams = self.env['ala.education.exam'].search([
                ('academic_year_id', '=', academic_year.id),
                ('class_id', '=', class_history.class_id.class_id.id),
            ])

        exam_results = self.env['ala.education.exam.results'].search([
            ('academic_year_id', '=', academic_year.id),
            ('division_id', '=', class_history.class_id.id),
            ('student_id', '=', student.id),
        ])

        print('111111111111111111111',student)
        print('111111111111111111111',exam_types)
        print('111111111111111111111',class_history.class_id)
        print('111111111111111111111',aca_exams)
        print('111111111111111111111',exam_results)

        return {
            'doc_ids': docids,
            'doc_model': 'ala.education.student',
            'docs': student,
            'student': student,
            'academic_year': academic_year,
            'exam_types': exam_types,
            'class_div': class_history.class_id,
            'aca_exams': aca_exams,
            'student_aca_exam_results': exam_results,
        }