# -*- coding: utf-8 -*-
from email.policy import default

from odoo import fields, models, api


from odoo import models, fields, api


class IdCard(models.TransientModel):
    _name = 'ala.id.wizard'
    _description = 'Admit Card'

    div_individual = fields.Selection(
        [('division', 'Division'), ('individual', 'Individual')],
        string='Type',
        default='division'
    )

    class_div_id = fields.Many2one(
        'ala.education.class.division',
        string='Select Class',
        domain="[('id', 'in', id_allowed_class_ids)]"
    )

    student_id = fields.Many2one(
        'ala.education.student',
        string='Select Student',
        domain="[('tc_issued','=',False), ('drop_out','=',False)]",
        copy=False
    )

    id_allowed_class_ids = fields.Many2many(
        'ala.education.class.division',
        compute="_compute_allowed_class_ids",
        string="Allowed Classes"
    )

    @api.depends('div_individual')
    def _compute_allowed_class_ids(self):
        for rec in self:
            students = self.env['ala.education.student'].search([
                ('tc_issued', '=', False),
                ('drop_out', '=', False)
            ])
            rec.id_allowed_class_ids = students.mapped('class_division_id')



    def action_generate_id_division(self):
        data = {
            'class_div_id': self.class_div_id.id,
        }
        return self.env.ref(
            'ala_education_core.action_id_card_print_division'
        ).report_action([], data=data)


    def action_generate_id_student(self):
        data = {
            'student_id': self.student_id.id,
        }
        return self.env.ref(
            'ala_education_core.action_id_card_print_student'
        ).report_action([], data=data)


class ReportIdCardDivision(models.AbstractModel):
    _name = 'report.ala_education_core.student_id_card_division_template'
    _description = 'Id Card Report by Division'

    @api.model
    def _get_report_values(self, docids, data=None):
        class_div_id = data.get('class_div_id')

        class_div = self.env['ala.education.class.division'].browse(class_div_id) if class_div_id else False

        return {
            'docs': class_div,
            'class_div': class_div,
        }

class ReportIdCardStudent(models.AbstractModel):
    _name = 'report.ala_education_core.student_id_card_student_template'
    _description = 'Id Card Report by Student'

    @api.model
    def _get_report_values(self, docids, data=None):
        student_id = data.get('student_id')

        student = self.env['ala.education.student'].browse(student_id) if student_id else False

        return {
            'docs': student,
            'student': student,
            'company': self.env.company,
        }

