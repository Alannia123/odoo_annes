# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models

# (background, font colour, single-letter code) — mirrors the XLSX/CSS palette
STATUS_STYLE = {
    'paid':     ('#DCFCE7', '#15803D', 'P'),
    'unpaid':   ('#FEF3C7', '#B45309', 'U'),
    'over_due': ('#FEE2E2', '#B91C1C', 'O'),
    'upcoming': ('#F1F5F9', '#475569', 'C'),
    '':         ('#FFFFFF', '#94A3B8', '\u2013'),
}


class ReportFeeDashboard(models.AbstractModel):
    _name = 'report.ala_fee_dashboard.report_fee_dashboard'
    _description = 'Student Fee Payment Tracker PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Hardened: every template variable gets a safe default regardless of
        # entry point (OWL button, direct URL, print-queue re-run).
        data = data or {}
        filters = data.get('filters') or {}

        FeeLine = self.env['ala.student.fee.line']
        try:
            payload = FeeLine.get_dashboard_data(filters, limit=800)
        except Exception:
            payload = {}

        students = payload.get('students') or []
        months = payload.get('months') or []
        buckets = payload.get('buckets') or []
        kpi = payload.get('kpi') or {
            'students': 0, 'payable': 0.0, 'paid': 0.0, 'balance': 0.0,
            'overdue': 0.0, 'admission_paid': 0, 'admission_unpaid': 0,
        }

        # Admission fee paid / unpaid split
        admission_paid, admission_unpaid = [], []
        for st in students:
            cell = (st.get('buckets') or {}).get('admission') or {}
            if not cell.get('has'):
                continue
            entry = {
                'student': st.get('student', ''),
                'register_number': st.get('register_number', ''),
                'roll_no': st.get('roll_no', ''),
                'division': st.get('division', ''),
                'amount': cell.get('amount', 0.0),
                'date': cell.get('date') or '-',
                'due': cell.get('due') or '-',
                'mode_label': cell.get('mode_label') or '-',
            }
            if cell.get('status') == 'paid':
                admission_paid.append(entry)
            else:
                admission_unpaid.append(entry)

        filter_bits = []
        for key, label in [
            ('search', 'Search'), ('roll_no', 'Roll No'),
            ('payment_status', 'Status'), ('payment_mode', 'Mode'),
            ('date_from', 'Paid From'), ('date_to', 'Paid To'),
        ]:
            if filters.get(key):
                filter_bits.append('%s: %s' % (label, filters[key]))

        return {
            'doc_ids': docids or [],
            'doc_model': 'ala.student.fee.line',
            'docs': FeeLine.browse(docids or []),
            'students': students,
            'months': months,
            'buckets': buckets,
            'kpi': kpi,
            'status_style': STATUS_STYLE,
            'admission_paid': admission_paid,
            'admission_unpaid': admission_unpaid,
            'filter_text': ' | '.join(filter_bits) or 'All records',
            'currency_symbol': payload.get('currency_symbol')
            or self.env.company.currency_id.symbol or '\u20B9',
            'company': self.env.company,
            'print_datetime': fields.Datetime.context_timestamp(
                FeeLine, datetime.now()).strftime('%d-%m-%Y %H:%M'),
            'len': len,
        }
