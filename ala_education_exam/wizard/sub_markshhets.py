# -*- coding: utf-8 -*-

from odoo import fields, models, _
import xlwt
import io
from datetime import datetime
import base64
from odoo.exceptions import ValidationError, UserError


class SubGenerateMArk(models.TransientModel):
    _name = 'ala.subject.marksheet.wizard'
    _description = 'Subject Marksheet'


    exam_valuation_id = fields.Many2one('ala.education.exam.valuation', string='Select Validated Exam', required=True, domain=[('state', '=', 'completed')])
    # generate_empty = fields.Boolean(default=False, help='Generate empty marksheet')

    def action_generate_subject_marksheet(self):
        # data = {
        #     'generate_empty': self.generate_empty
        # }

        return self.env.ref(
            'ala_education_exam.exam_subject_marksheet_pdf'
        ).report_action(self.exam_valuation_id)


