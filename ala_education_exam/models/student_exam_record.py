from odoo import models, fields, api
from odoo.exceptions import ValidationError



class StudentExamRecord(models.Model):
    _name = 'ala.student.exam.record'
    _description = 'Student Exam Record'

    student_id = fields.Many2one('res.partner', string='Student', domain="[('is_student','=',True)]", required=True)
    division = fields.Char(string='Division')
    academic_year = fields.Many2one('ala.education.academic.year', string='Academic Year')
    register_number = fields.Char(string='Register Number')
    roll_number = fields.Char(string='Roll Number')

    exam_line_ids = fields.One2many('ala.student.exam.line', 'record_id', string='Exam Lines')

    _sql_constraints = [
        ('student_year_unique', 'unique(student_id, academic_year)',
         'This student already has a record for the selected academic year!')
    ]

    @api.constrains('student_id', 'academic_year')
    def _check_unique_student_year(self):
        for rec in self:
            domain = [
                ('student_id', '=', rec.student_id.id),
                ('academic_year', '=', rec.academic_year.id),
                ('id', '!=', rec.id)
            ]
            if self.search_count(domain):
                raise ValidationError("Student already has an exam record for this academic year.")


class StudentExamLine(models.Model):
    _name = 'ala.student.exam.line'
    _description = 'Student Exam Line'

    record_id = fields.Many2one('ala.student.exam.record', string='Exam Record', ondelete='cascade')

    exam = fields.Char(string='Exam / Subject')
    term1_total = fields.Float(string='Term 1 Total')
    half_assign_mark = fields.Float(string='Half Yearly Assignment Mark')
    half_exam_mark = fields.Float(string='Half Yearly Exam Mark')
    half_total_mark = fields.Float(string='Half Yearly Total', compute="_compute_half_total", store=True)

    @api.depends('half_assign_mark', 'half_exam_mark')
    def _compute_half_total(self):
        for rec in self:
            rec.half_total_mark = rec.half_assign_mark + rec.half_exam_mark
