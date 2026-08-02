# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models

# ---------------------------------------------------------------------
# Academic-year month order (April -> March) shared by UI, XLSX and PDF
# ---------------------------------------------------------------------
MONTHS = [
    {'key': 'apr', 'label': 'April',     'short': 'Apr', 'num': 4},
    {'key': 'may', 'label': 'May',       'short': 'May', 'num': 5},
    {'key': 'jun', 'label': 'June',      'short': 'Jun', 'num': 6},
    {'key': 'jul', 'label': 'July',      'short': 'Jul', 'num': 7},
    {'key': 'aug', 'label': 'August',    'short': 'Aug', 'num': 8},
    {'key': 'sep', 'label': 'September', 'short': 'Sep', 'num': 9},
    {'key': 'oct', 'label': 'October',   'short': 'Oct', 'num': 10},
    {'key': 'nov', 'label': 'November',  'short': 'Nov', 'num': 11},
    {'key': 'dec', 'label': 'December',  'short': 'Dec', 'num': 12},
    {'key': 'jan', 'label': 'January',   'short': 'Jan', 'num': 1},
    {'key': 'feb', 'label': 'February',  'short': 'Feb', 'num': 2},
    {'key': 'mar', 'label': 'March',     'short': 'Mar', 'num': 3},
]
MONTH_NUM_TO_IDX = {m['num']: i for i, m in enumerate(MONTHS)}

# Word-boundary matching, longest alternatives first so 'september' wins
# over 'sep' and 'march' over 'mar'.
_MONTH_RE = re.compile(
    r'\b(september|sept|sep|february|feb|november|nov|december|dec'
    r'|january|jan|october|oct|august|aug|april|apr|march|mar'
    r'|june|jun|july|jul|may)\b',
    re.IGNORECASE,
)
_TOKEN_IDX = {
    'april': 0, 'apr': 0, 'may': 1, 'june': 2, 'jun': 2, 'july': 3, 'jul': 3,
    'august': 4, 'aug': 4, 'september': 5, 'sept': 5, 'sep': 5,
    'october': 6, 'oct': 6, 'november': 7, 'nov': 7, 'december': 8, 'dec': 8,
    'january': 9, 'jan': 9, 'february': 10, 'feb': 10, 'march': 11, 'mar': 11,
}

# A range separator is only honoured when it sits *between* two month tokens,
# so 'Total Fee April, December' is never mistaken for 'April to December'.
_RANGE_SEP = re.compile(r'^\s*(?:-|–|—|to|till|until|thru|through)\s*$',
                        re.IGNORECASE)

STATUS_LABELS = {
    'upcoming': 'Upcoming',
    'unpaid': 'Unpaid',
    'over_due': 'Overdue',
    'paid': 'Paid',
}

MODE_LABELS = {
    'bank': 'Bank Transfer',
    'cash': 'Cash',
    'online': 'Online',
}

# Buckets shown as fixed columns before the month grid
BUCKETS = [
    {'key': 'admission', 'label': 'Admission Fee'},
    {'key': 'activity', 'label': 'Activity Fee'},
    {'key': 'misc', 'label': 'Miscellaneous'},
]

DEFAULT_ACTIVITY_KEYWORDS = 'activity'
DEFAULT_MISC_KEYWORDS = 'miscellaneous,misc,fine'


def _empty_cell():
    return {
        'amount': 0.0,
        'status': '',
        'status_label': '',
        'mode_label': '',
        'date': '',
        'has': False,
        'ids': [],
    }


class StudentFeeLineDashboard(models.Model):
    _inherit = 'ala.student.fee.line'

    # =================================================================
    # Configuration helpers
    # =================================================================
    @api.model
    def _bucket_keywords(self):
        icp = self.env['ir.config_parameter'].sudo()
        activity = icp.get_param(
            'ala_fee_dashboard.activity_keywords', DEFAULT_ACTIVITY_KEYWORDS)
        misc = icp.get_param(
            'ala_fee_dashboard.misc_keywords', DEFAULT_MISC_KEYWORDS)
        split = lambda s: [k.strip().lower() for k in (s or '').split(',') if k.strip()]
        return split(activity), split(misc)

    @api.model
    def _resolve_bucket(self, line, activity_kw, misc_kw):
        """Map a fee line to admission / activity / misc / monthly."""
        if line.fee_type == 'monthly':
            return 'monthly'
        if line.fee_type in ('admission', 're_admission'):
            return 'admission'
        name = ((line.product_id.name or '') + ' ' + (line.fee_description or '')).lower()
        if any(k in name for k in activity_kw):
            return 'activity'
        if any(k in name for k in misc_kw):
            return 'misc'
        # Any other one-time fee falls into Miscellaneous so nothing is lost.
        return 'misc'

    # =================================================================
    # Month resolution for monthly fee lines
    # =================================================================
    @api.model
    def _months_for_line(self, line):
        """Return the academic-month indices (0=April .. 11=March) a monthly
        fee line belongs to.

        Resolution order: fee_month_range -> fee_description -> product name
        -> overdue_date. Ranges such as 'April - June' are expanded.
        """
        for source in (line.fee_month_range, line.fee_description,
                       line.product_id.name):
            if not source:
                continue
            hits = []
            for m in _MONTH_RE.finditer(source):
                idx = _TOKEN_IDX[m.group(1).lower()]
                if not hits or hits[-1][2] != idx:
                    hits.append((m.start(), m.end(), idx))
            if not hits:
                continue

            # 'April - June' / 'April to June' -> expand the whole span
            if len(hits) == 2:
                gap = source[hits[0][1]:hits[1][0]]
                if _RANGE_SEP.match(gap):
                    start, end = hits[0][2], hits[1][2]
                    if start <= end:
                        return list(range(start, end + 1))
                    return list(range(start, 12)) + list(range(0, end + 1))

            seen, indices = set(), []
            for _s, _e, idx in hits:
                if idx not in seen:
                    seen.add(idx)
                    indices.append(idx)
            return indices

        if line.overdue_date:
            return [MONTH_NUM_TO_IDX.get(line.overdue_date.month, 0)]
        return []

    # =================================================================
    # Filter metadata for the OWL component
    # =================================================================
    @api.model
    def get_dashboard_filters(self):
        division_model = self._fields['student_division_id'].comodel_name
        divisions = self.env[division_model].search_read([], ['name'], order='name')

        # ay_model = self._fields['academic_year'].comodel_name
        academic_years = self.env['ala.education.academic.year'].search_read([('enable', '=', True)], ['name'], order='name desc')

        return {
            'divisions': divisions,
            'academic_years': academic_years,
            'payment_statuses': [{'value': k, 'label': v} for k, v in STATUS_LABELS.items()],
            'payment_modes': [{'value': k, 'label': v} for k, v in MODE_LABELS.items()],
            'months': MONTHS,
            'buckets': BUCKETS,
            'currency_symbol': self.env.company.currency_id.symbol or '₹',
            'company_name': self.env.company.name,
        }

    # =================================================================
    # Domain builder (shared by dashboard, XLSX controller and PDF report)
    # =================================================================
    @api.model
    def _dashboard_domain(self, f):
        f = f or {}
        domain = []
        if f.get('division_id'):
            domain.append(('student_division_id', '=', int(f['division_id'])))
        if f.get('academic_year_id'):
            domain.append(('academic_year', '=', int(f['academic_year_id'])))
        if f.get('roll_no'):
            domain.append(('student_id.roll_no', '=', str(f['roll_no']).strip()))
        if f.get('search'):
            domain += [
                '|',
                ('student_id.name', 'ilike', f['search']),
                ('register_number', 'ilike', f['search']),
            ]
        if f.get('payment_status'):
            domain.append(('payment_status', '=', f['payment_status']))
        if f.get('payment_mode'):
            domain.append(('payment_mode', '=', f['payment_mode']))
        if f.get('date_from'):
            domain.append(('invoice_date', '>=', f['date_from']))
        if f.get('date_to'):
            domain.append(('invoice_date', '<=', f['date_to']))
        return domain

    # =================================================================
    # Main payload — one row per student, April..March matrix
    # =================================================================
    @api.model
    def get_dashboard_data(self, filters=None, limit=200):
        filters = filters or {}
        domain = self._dashboard_domain(filters)
        activity_kw, misc_kw = self._bucket_keywords()

        # Odoo 19: read_group() is gone. _read_group() returns a list of
        # tuples of the grouped values -- here [(student_recordset,), ...].
        student_groups = self._read_group(
            domain, groupby=['student_id'], limit=limit,
        )
        student_ids = [g[0].id for g in student_groups if g[0]]

        # Deliberately unfiltered: the filter picks *which students* to show,
        # then the grid shows their complete April-March year. Adding the
        # domain here would blank out months outside a date filter.
        lines = self.search(
            [('student_id', 'in', student_ids)], order='student_id, id',
        )

        rows = {}
        for line in lines:
            sid = line.student_id.id
            if sid not in rows:
                sf = line.student_fee_id
                rows[sid] = {
                    'id': sid,
                    'student': line.student_id.name or '',
                    'register_number': line.register_number or '',
                    'roll_no': line.student_id.roll_no or '',
                    'division': line.student_division_id.name or '',
                    'academic_year': line.academic_year.name or '',
                    'buckets': {b['key']: _empty_cell() for b in BUCKETS},
                    'months': [_empty_cell() for _ in MONTHS],
                    'total_payable': sf.final_amount_total if sf else 0.0,
                    'total_paid': sf.amount_paid if sf else 0.0,
                    'total_balance': sf.amount_unpaid if sf else 0.0,
                    'total_overdue': sf.amount_due if sf else 0.0,
                    'months_paid': 0,
                    'months_total': 0,
                }
            row = rows[sid]

            bucket = self._resolve_bucket(line, activity_kw, misc_kw)
            payload = {
                'amount': line.amount_to_paid,
                'status': line.payment_status or '',
                'status_label': STATUS_LABELS.get(line.payment_status, ''),
                'mode_label': MODE_LABELS.get(line.payment_mode, ''),
                'date': fields.Date.to_string(line.invoice_date) if line.invoice_date else '',
                'due': fields.Date.to_string(line.overdue_date) if line.overdue_date else '',
                'fine': line.fine_amount,
                'concession': line.concession_amount,
            }

            if bucket == 'monthly':
                indices = self._months_for_line(line)
                span = len(indices) or 1
                for idx in indices:
                    if not 0 <= idx < 12:
                        continue
                    cell = row['months'][idx]
                    cell['has'] = True
                    cell['ids'].append(line.id)
                    # Split evenly when one line covers a range of months
                    cell['amount'] += payload['amount'] / span
                    cell['status'] = payload['status']
                    cell['status_label'] = payload['status_label']
                    cell['mode_label'] = payload['mode_label']
                    cell['date'] = payload['date']
                    cell['due'] = payload.get('due', '')
            else:
                cell = row['buckets'][bucket]
                cell['has'] = True
                cell['ids'].append(line.id)
                cell['amount'] += payload['amount']
                # Worst status wins when a bucket aggregates several lines
                cell['status'] = self._worse_status(cell['status'], payload['status'])
                cell['status_label'] = STATUS_LABELS.get(cell['status'], '')
                cell['mode_label'] = payload['mode_label'] or cell['mode_label']
                cell['date'] = payload['date'] or cell['date']
                cell['due'] = payload.get('due', '') or cell.get('due', '')

        # Month counters
        for row in rows.values():
            present = [c for c in row['months'] if c['has']]
            row['months_total'] = len(present)
            row['months_paid'] = len([c for c in present if c['status'] == 'paid'])

        students = list(rows.values())
        students.sort(key=lambda s: (
            s['division'],
            int(s['roll_no']) if str(s['roll_no']).isdigit() else 9999,
            s['student'],
        ))
        for idx, st in enumerate(students, start=1):
            st['sno'] = idx

        kpi = {
            'students': len(students),
            'payable': sum(s['total_payable'] for s in students),
            'paid': sum(s['total_paid'] for s in students),
            'balance': sum(s['total_balance'] for s in students),
            'overdue': sum(s['total_overdue'] for s in students),
            'admission_paid': len([
                s for s in students
                if s['buckets']['admission']['has']
                and s['buckets']['admission']['status'] == 'paid'
            ]),
            'admission_unpaid': len([
                s for s in students
                if s['buckets']['admission']['has']
                and s['buckets']['admission']['status'] != 'paid'
            ]),
        }

        return {
            'students': students,
            'kpi': kpi,
            'months': MONTHS,
            'buckets': BUCKETS,
            'currency_symbol': self.env.company.currency_id.symbol or '₹',
        }

    @api.model
    def _worse_status(self, current, new):
        rank = {'': 0, 'paid': 1, 'upcoming': 2, 'unpaid': 3, 'over_due': 4}
        return new if rank.get(new, 0) > rank.get(current, 0) else (current or new)
