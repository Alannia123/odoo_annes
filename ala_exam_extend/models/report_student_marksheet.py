from odoo import models

class ReportStudentMarksheet(models.AbstractModel):
    _name = 'report.ala_exam_extend.report_student_rank_card_template'
    _description = 'Student Marksheet Report'

    def _get_report_values(self, docids, data=None):
        data = data or {}
        student_id = data.get('student_id')
        academic_year_id = data.get('academic_year_id')

        student = self.env['ala.education.student'].browse(student_id)
        academic_year = self.env['ala.education.academic.year'].browse(academic_year_id)
        exam_types = self.env['ala.education.exam.type'].sudo().search([])

        division = False
        if academic_year and academic_year.enable:
            division = student.class_division_id

        else:
            class_history = student.class_history_ids.filtered(
                lambda h: h.academic_year_id.id == academic_year.id
            )[:1]
            division = class_history.class_id

        aca_exams = self.env['ala.education.exam']
        if division :
            aca_exams = self.env['ala.education.exam'].search([
                ('academic_year_id', '=', academic_year.id),
                ('class_id', '=', division.class_id.id),
            ])

        exam_results = self.env['ala.education.exam.results'].search([
            ('academic_year_id', '=', academic_year.id),
            ('division_id', '=', division.id),
            ('student_id', '=', student.id),
        ])

        print('111111111111111111111academic_year',academic_year)
        print('111111111111111111111',exam_types)
        print('111111111111111111111division',division)
        print('111111111111111111111',aca_exams)
        print('111111111111111111111',exam_results)

        return {
            'doc_ids': docids,
            'doc_model': 'ala.education.student',
            'docs': student,
            'student': student,
            'academic_year': academic_year,
            'exam_types': exam_types,
            'class_div': division,
            'aca_exams': aca_exams,
            'student_aca_exam_results': exam_results,
        }