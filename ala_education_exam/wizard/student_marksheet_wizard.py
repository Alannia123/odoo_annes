from odoo import api, fields, models

class StudentMarksheetWizard(models.TransientModel):
    _name = 'ala.student.marksheet.wizard'
    _description = 'Student Marksheet Wizard'

    student_id = fields.Many2one(
        'ala.education.student',
        string='Student',
        required=True,
        readonly=True
    )

    academic_year_id = fields.Many2one(
        'ala.education.academic.year',
        string='Academic Year',
        required=True,
        default=lambda self: self.env['ala.education.academic.year'].search(
            [('enable', '=', True)],
            limit=1
        )
    )

    def action_print_marksheet(self):
        data = {
            'student_id': self.student_id.id,
            'academic_year_id': self.academic_year_id.id,
        }
        return self.env.ref(
            'ala_education_exam.action_generate_rank_student_card'
        ).report_action(self.student_id, data=data)