# -*- coding: utf-8 -*-
from email.policy import default

from odoo import fields, models, api


class AdmitCard(models.TransientModel):
    _name = 'ala.admit.wizard'
    _description = 'Admit Card'


    div_individual = fields.Selection([('division', 'Division'), ('individual', 'Individual')], 'Type', default='division')
    class_div_id = fields.Many2one('ala.education.class.division', string='Select Class', required=False ,domain="[('id', 'in', allowed_class_ids)]")
    exam_id = fields.Many2one('ala.education.exam', string='Select Exam', required=True, domain=[('state', '=', 'ongoing')])
    student_id = fields.Many2one('ala.education.student', string='Select Student' ,copy=False)
    allowed_class_ids = fields.Many2many(
        'ala.education.class.division',
        compute="_compute_allowed_class_ids",
        store=False
    )

    @api.depends('exam_id')
    def _compute_allowed_class_ids(self):
        for rec in self:
            if rec.exam_id:
                # here link exam to its allowed divisions
                rec.allowed_class_ids = self.env['ala.education.class.division'].search([('class_id', '=', rec.exam_id.class_id.id)]).ids
            else:
                rec.allowed_class_ids = []



    def action_generate_pdf_divisions(self):
        data = {
            'class_div_id': self.class_div_id.id,
            'exam_id': self.exam_id.id,
        }
        return self.env.ref(
            'ala_education_exam.action_admit_card_print_division'
        ).report_action([], data=data)

    def action_generate_pdf_student(self):
        data = {
            'student_id': self.student_id.id,
            'exam_id': self.exam_id.id,
        }
        return self.env.ref(
            'ala_education_exam.action_admit_card_print_student'
        ).report_action([], data=data)


class ReportAdmitCardDivision(models.AbstractModel):
    _name = 'report.ala_education_exam.admit_card_division'
    _description = 'Admit Card Report by Division'

    @api.model
    def _get_report_values(self, docids, data=None):
        exam_id = data.get('exam_id')
        class_div_id = data.get('class_div_id')

        exam = self.env['ala.education.exam'].browse(exam_id) if exam_id else False
        class_div = self.env['ala.education.class.division'].browse(class_div_id) if class_div_id else False

        return {
            'docs': exam,
            'exam': exam,
            'class_div': class_div,
        }

class ReportAdmitCardStudent(models.AbstractModel):
    _name = 'report.ala_education_exam.admit_card_student_report'
    _description = 'Admit Card Report by Student'

    @api.model
    def _get_report_values(self, docids, data=None):
        exam_id = data.get('exam_id')
        student_id = data.get('student_id')

        exam = self.env['ala.education.exam'].browse(exam_id) if exam_id else False
        student = self.env['ala.education.student'].browse(student_id) if student_id else False

        return {
            'docs': exam,
            'exam': exam,
            'student': student,
        }

