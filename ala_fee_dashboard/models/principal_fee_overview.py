# -*- coding: utf-8 -*-
"""Principal Fee Overview.

Two lenses over the same collection data:

* ``detail``  -- one row per receipt, for reconciling a day's cash box.
* ``summary`` -- one row per day, one column per payment mode, for the
  month-end collection statement.

Both share :meth:`_collection_domain` so the screen, the XLSX export and
the PDF can never disagree about what "collected" means.
"""

from collections import defaultdict

from odoo import api, fields, models

from .fee_dashboard import MODE_LABELS


class StudentFeeLinePrincipalOverview(models.Model):
    _inherit = 'ala.student.fee.line'

    # =================================================================
    # Shared domain
    # =================================================================
    @api.model
    def _collection_domain(self, date_from=False, date_to=False,
                           payment_mode=False, division_id=False):
        """Lines that represent money actually received in the window.

        Only ``paid`` lines count -- an unpaid line has no collection date
        and would skew every total on this screen.
        """
        domain = [('payment_status', '=', 'paid')]
        if date_from:
            domain.append(('invoice_date', '>=', date_from))
        if date_to:
            domain.append(('invoice_date', '<=', date_to))
        if payment_mode:
            domain.append(('payment_mode', '=', payment_mode))
        if division_id:
            domain.append(('student_division_id', '=', int(division_id)))
        return domain

    @api.model
    def _mode_columns(self):
        """Payment-mode columns in a stable order for grid and export."""
        return [{'key': key, 'label': label}
                for key, label in MODE_LABELS.items()]

    # =================================================================
    # Detail view -- one row per receipt
    # =================================================================
    @api.model
    def get_principal_fee_overview(self, date_from=False, date_to=False,
                                   payment_mode=False, division_id=False,
                                   limit=1000):
        domain = self._collection_domain(
            date_from, date_to, payment_mode, division_id)
        records = self.search(domain, order='invoice_date, id', limit=limit)

        lines = []
        by_mode = defaultdict(float)
        for rec in records:
            amount = rec.amount_to_paid or 0.0
            by_mode[rec.payment_mode or ''] += amount
            lines.append({
                'id': rec.id,
                'date': fields.Date.to_string(rec.invoice_date) or '',
                'student': rec.student_id.name or '',
                'register_number': rec.register_number or '',
                'division': rec.student_division_id.name or '',
                'description': rec.fee_description or (
                    rec.product_id.name or ''),
                'mode': rec.payment_mode or '',
                'mode_label': MODE_LABELS.get(rec.payment_mode, '-'),
                'amount': amount,
                'fine': rec.fine_amount or 0.0,
                'concession': rec.concession_amount or 0.0,
            })

        for idx, line in enumerate(lines, start=1):
            line['sno'] = idx

        return {
            'lines': lines,
            'mode_columns': self._mode_columns(),
            'totals': {
                'amount': sum(line['amount'] for line in lines),
                'fine': sum(line['fine'] for line in lines),
                'concession': sum(line['concession'] for line in lines),
                'count': len(lines),
                'by_mode': {
                    col['key']: by_mode.get(col['key'], 0.0)
                    for col in self._mode_columns()
                },
                'truncated': len(records) >= limit,
            },
            'currency_symbol': self.env.company.currency_id.symbol or '\u20B9',
        }

    # =================================================================
    # Summary view -- one row per day, one column per mode
    # =================================================================
    @api.model
    def get_principal_fee_summary(self, date_from=False, date_to=False,
                                  payment_mode=False, division_id=False):
        domain = self._collection_domain(
            date_from, date_to, payment_mode, division_id)
        mode_cols = self._mode_columns()

        # Aggregate in SQL rather than pulling every line into Python: a
        # full-year range can be tens of thousands of receipts.
        groups = self._read_group(
            domain,
            groupby=['invoice_date:day', 'payment_mode'],
            aggregates=['amount_to_paid:sum', '__count'],
        )

        per_day = defaultdict(lambda: {
            'modes': {col['key']: 0.0 for col in mode_cols},
            'total': 0.0,
            'count': 0,
        })
        by_mode = {col['key']: 0.0 for col in mode_cols}
        grand_total = 0.0
        grand_count = 0

        for day, mode, amount_sum, count in groups:
            if not day:
                continue
            key = fields.Date.to_string(day)
            amount = amount_sum or 0.0
            bucket = per_day[key]
            if mode in bucket['modes']:
                bucket['modes'][mode] += amount
                by_mode[mode] += amount
            bucket['total'] += amount
            bucket['count'] += count
            grand_total += amount
            grand_count += count

        rows = []
        for idx, day_key in enumerate(sorted(per_day), start=1):
            bucket = per_day[day_key]
            rows.append({
                'sno': idx,
                'date': day_key,
                'modes': bucket['modes'],
                'total': bucket['total'],
                'count': bucket['count'],
            })

        return {
            'rows': rows,
            'mode_columns': mode_cols,
            'totals': {
                'by_mode': by_mode,
                'amount': grand_total,
                'count': grand_count,
                'days': len(rows),
                'best_day': max(rows, key=lambda r: r['total'])['date']
                if rows else '',
                'average': (grand_total / len(rows)) if rows else 0.0,
            },
            'currency_symbol': self.env.company.currency_id.symbol or '\u20B9',
        }

    # =================================================================
    # Filter metadata
    # =================================================================
    @api.model
    def get_principal_overview_filters(self):
        division_model = self._fields['student_division_id'].comodel_name
        return {
            'divisions': self.env[division_model].search_read(
                [], ['name'], order='name'),
            'payment_modes': self._mode_columns(),
            'currency_symbol': self.env.company.currency_id.symbol or '\u20B9',
            'company_name': self.env.company.name,
        }
