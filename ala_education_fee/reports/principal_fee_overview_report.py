# -*- coding: utf-8 -*-
from odoo import api, models


class PrincipalFeeOverviewReport(models.AbstractModel):
    _name = 'report.mis_education_fee.report_principal_fee_overview'
    _description = 'Principal Fee Overview Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        Line = self.env['student.fee.line']
        result = Line.get_principal_fee_overview(
            data.get('date_from'), data.get('date_to'), data.get('payment_mode'),
        )
        return {
            'doc_ids': docids,
            'doc_model': 'student.fee.line',
            'docs': result['lines'],
            'totals': result['totals'],
            'company': self.env.company,
            'date_from': data.get('date_from'),
            'date_to': data.get('date_to'),
        }