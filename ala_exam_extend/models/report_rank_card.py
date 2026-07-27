from odoo import api, models


class ReportRankCard(models.AbstractModel):
    _name = 'report.ala_exam_extend.report_rank_card_template'
    _description = 'Rank Card Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        class_div_id = data.get('class_div_id')
        academic_year_id = data.get('academic_year_id')

        class_div = self.env['ala.education.class.division'].browse(class_div_id)
        academic_year = self.env['ala.education.academic.year'].browse(academic_year_id)
        exam_types = self.env['ala.education.exam.type'].sudo().search([])

        aca_exams = self.env['ala.education.exam'].search([
            ('academic_year_id', '=', academic_year.id),
            ('class_id', '=', class_div.class_id.id),
        ])

        exam_results = self.env['ala.education.exam.results'].search([
            ('academic_year_id', '=', academic_year.id),
            ('division_id', '=', class_div.id),
            ('student_id', '!=', False),
            ('exam_id', '!=', False),
        ])
        print('yyyyyyyyyyyyyyyyyyyyyyyy',academic_year)
        print('yyyyyyyyyyyyyyyyyyyyyyyy',exam_results)

        students = exam_results.mapped('student_id')
        print('students-------------------',students)
        print('students-------------------',aca_exams)
        print('students-------------------',exam_types)

        return {
            'doc_ids': docids,
            'doc_model': 'ala.education.class.division',
            'docs': class_div,
            'students': students,
            'aca_exams': aca_exams,
            'exam_types': exam_types,
            'academic_year_id': academic_year,
            'exam_results': exam_results,
        }