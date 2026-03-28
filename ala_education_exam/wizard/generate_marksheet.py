# -*- coding: utf-8 -*-

from odoo import fields, models, _
import xlwt
import io
from datetime import datetime
import base64
from odoo.exceptions import ValidationError, UserError


class GenerateMArk(models.TransientModel):
    _name = 'ala.marksheet.wizard'
    _description = 'Marksheet'


    # exam_id = fields.Many2one('ala.education.exam.type', string='Select Exam', required=True)
    class_div_id = fields.Many2one('ala.education.class.division', string='Select Class', required=True)

    def action_generate_marksheet_xlsx(self):
        pre_marksheet = self.env['ala.education.exam.type'].search([('prepare_marksheet', '=', True)])
        if len(pre_marksheet) > 1:
            raise UserError(_("Please select any one exam on Exam Configuration."))
        if not pre_marksheet:
            raise UserError(_("No exams selected for Marksheet on Exam Configuration."))

        data = {
            'division': self.class_div_id.id,
            # 'exam': self.exam_id.id,
        }
        return self.env.ref('ala_education_exam.exam_marksheet_pdf').report_action(self.class_div_id.id)

