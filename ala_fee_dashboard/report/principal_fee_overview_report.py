# -*- coding: utf-8 -*-
"""PDF for the Principal Fee Overview.

Re-runs the same model methods as the screen from the filter values passed
in ``data``; nothing is carried over from the client except the filters.
"""

from datetime import datetime

from odoo import api, fields, models

MODE_LABELS_FALLBACK = {'bank': 'Bank Transfer', 'cash': 'Cash',
                        'online': 'Online'}


class ReportPrincipalFeeOverview(models.AbstractModel):
    _name = 'report.ala_fee_dashboard.report_principal_fee_overview'
    _description = 'Principal Fee Overview PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        date_from = data.get('date_from') or False
        date_to = data.get('date_to') or False
        payment_mode = data.get('payment_mode') or False
        division_id = data.get('division_id') or False
        view_type = data.get('view_type') or 'summary'

        FeeLine = self.env['ala.student.fee.line']
        try:
            if view_type == 'summary':
                payload = FeeLine.get_principal_fee_summary(
                    date_from, date_to, payment_mode, division_id)
            else:
                payload = FeeLine.get_principal_fee_overview(
                    date_from, date_to, payment_mode, division_id, limit=5000)
        except Exception:
            payload = {}

        filter_bits = []
        if date_from or date_to:
            filter_bits.append('Period: %s to %s' % (
                date_from or 'start', date_to or 'today'))
        if payment_mode:
            filter_bits.append('Mode: %s' % MODE_LABELS_FALLBACK.get(
                payment_mode, payment_mode))
        if division_id:
            division_model = FeeLine._fields['student_division_id'].comodel_name
            division = self.env[division_model].browse(int(division_id)).exists()
            if division:
                filter_bits.append('Division: %s' % division.name)

        return {
            'doc_ids': docids or [],
            'doc_model': 'ala.student.fee.line',
            'docs': FeeLine.browse(docids or []),
            'view_type': view_type,
            'rows': payload.get('rows') or [],
            'lines': payload.get('lines') or [],
            'mode_columns': payload.get('mode_columns') or [],
            'totals': payload.get('totals') or {},
            'currency_symbol': payload.get('currency_symbol')
            or self.env.company.currency_id.symbol or '\u20B9',
            'filter_text': ' | '.join(filter_bits) or 'All collections',
            'company': self.env.company,
            'print_datetime': fields.Datetime.context_timestamp(
                FeeLine, datetime.now()).strftime('%d-%m-%Y %H:%M'),
        }
