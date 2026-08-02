# -*- coding: utf-8 -*-
import io
import json
from datetime import datetime

from odoo import http, fields
from odoo.http import request, content_disposition

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

# Fill / font pairs shared with the dashboard and the PDF
STATUS_STYLE = {
    'paid':     ('#DCFCE7', '#15803D'),
    'unpaid':   ('#FEF3C7', '#B45309'),
    'over_due': ('#FEE2E2', '#B91C1C'),
    'upcoming': ('#F1F5F9', '#475569'),
    '':         ('#FFFFFF', '#CBD5E1'),
}


class FeeDashboardController(http.Controller):

    # -----------------------------------------------------------------
    def _filter_text(self, filters):
        bits = []
        labels = [
            ('search', 'Search'), ('roll_no', 'Roll No'),
            ('payment_status', 'Status'), ('payment_mode', 'Mode'),
            ('date_from', 'Paid From'), ('date_to', 'Paid To'),
        ]
        for key, label in labels:
            if filters.get(key):
                bits.append('%s: %s' % (label, filters[key]))
        return ' | '.join(bits) or 'Filters: All records'

    # -----------------------------------------------------------------
    @http.route('/ala_fee_dashboard/export_xlsx', type='http', auth='user', methods=['POST'])
    def export_xlsx(self, filters='{}', **kwargs):
        if xlsxwriter is None:
            return request.not_found()

        try:
            filters = json.loads(filters or '{}')
        except (ValueError, TypeError):
            filters = {}

        FeeLine = request.env['ala.student.fee.line']
        payload = FeeLine.get_dashboard_data(filters, limit=2000)
        students = payload['students']
        kpi = payload['kpi']
        months = payload['months']
        buckets = payload['buckets']
        symbol = payload['currency_symbol']

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        money_num = '%s#,##0.00' % symbol

        # ---------------- formats ----------------
        f_title = wb.add_format({'bold': True, 'font_size': 15, 'font_color': '#0F766E'})
        f_sub = wb.add_format({'font_size': 9, 'font_color': '#64748B'})
        f_grp = wb.add_format({
            'bold': True, 'bg_color': '#134E4A', 'font_color': '#FFFFFF',
            'border': 1, 'align': 'center', 'valign': 'vcenter',
        })
        f_grp_m = wb.add_format({
            'bold': True, 'bg_color': '#0F172A', 'font_color': '#FFFFFF',
            'border': 1, 'align': 'center', 'valign': 'vcenter',
        })
        f_head = wb.add_format({
            'bold': True, 'bg_color': '#0F766E', 'font_color': '#FFFFFF',
            'border': 1, 'align': 'center', 'valign': 'vcenter',
            'text_wrap': True, 'font_size': 9,
        })
        f_cell = wb.add_format({'border': 1, 'valign': 'vcenter', 'font_size': 10})
        f_cell_c = wb.add_format({
            'border': 1, 'valign': 'vcenter', 'align': 'center', 'font_size': 10})
        f_money = wb.add_format({
            'border': 1, 'num_format': money_num, 'valign': 'vcenter', 'font_size': 10})
        f_total_lbl = wb.add_format({
            'bold': True, 'border': 1, 'bg_color': '#FDE68A', 'align': 'right'})
        f_total = wb.add_format({
            'bold': True, 'border': 1, 'bg_color': '#FDE68A', 'num_format': money_num})
        f_status = {}
        for key, (bg, fg) in STATUS_STYLE.items():
            f_status[key] = wb.add_format({
                'border': 1, 'bg_color': bg, 'font_color': fg, 'bold': True,
                'align': 'center', 'valign': 'vcenter', 'font_size': 9,
            })

        # =================================================================
        # Sheet 1 — Fee Tracker (the 16 required fields)
        # =================================================================
        ws = wb.add_worksheet('Fee Tracker')
        ws.set_zoom(85)

        n_bucket_cols = len(buckets) * 2
        first_bucket_col = 5
        first_month_col = first_bucket_col + n_bucket_cols
        first_tail_col = first_month_col + len(months)
        last_col = first_tail_col + 3

        # widths
        ws.set_column(0, 0, 5)                       # S.No
        ws.set_column(1, 1, 26)                      # Student
        ws.set_column(2, 2, 14)                      # Register No
        ws.set_column(3, 3, 8)                       # Roll No
        ws.set_column(4, 4, 12)                      # Division
        for i in range(len(buckets)):
            ws.set_column(first_bucket_col + i * 2, first_bucket_col + i * 2, 13)
            ws.set_column(first_bucket_col + i * 2 + 1, first_bucket_col + i * 2 + 1, 10)
        ws.set_column(first_month_col, first_month_col + len(months) - 1, 10)
        ws.set_column(first_tail_col, first_tail_col, 9)       # Months
        ws.set_column(first_tail_col + 1, last_col, 14)        # Paid/Balance/Payable

        ws.write(0, 0, 'Student Fee Payment Tracker', f_title)
        ws.write(1, 0, request.env.company.name, f_sub)
        ws.write(2, 0, self._filter_text(filters), f_sub)
        ws.write(3, 0, 'Generated: %s' % fields.Datetime.context_timestamp(
            FeeLine, datetime.now()).strftime('%d-%m-%Y %H:%M'), f_sub)

        # --- two-tier header (rows 5 and 6) ---
        hdr_top, hdr_sub = 5, 6
        for col, label in enumerate(
                ['S.No', "Student's Name", 'Register No', 'Roll No', 'Division']):
            ws.merge_range(hdr_top, col, hdr_sub, col, label, f_head)

        for i, b in enumerate(buckets):
            c0 = first_bucket_col + i * 2
            ws.merge_range(hdr_top, c0, hdr_top, c0 + 1, b['label'], f_grp)
            ws.write(hdr_sub, c0, 'Amount', f_head)
            ws.write(hdr_sub, c0 + 1, 'Status', f_head)

        ws.merge_range(hdr_top, first_month_col, hdr_top,
                       first_month_col + len(months) - 1, 'April to March', f_grp_m)
        for i, m in enumerate(months):
            ws.write(hdr_sub, first_month_col + i, m['label'], f_head)

        for i, label in enumerate(['Months', 'Paid', 'Balance', 'Payable']):
            ws.merge_range(hdr_top, first_tail_col + i, hdr_sub,
                           first_tail_col + i, label, f_head)

        ws.freeze_panes(hdr_sub + 1, 2)

        # --- data rows ---
        row = hdr_sub + 1
        for st in students:
            ws.write_number(row, 0, st['sno'], f_cell_c)
            ws.write(row, 1, st['student'], f_cell)
            ws.write(row, 2, st['register_number'], f_cell_c)
            ws.write(row, 3, st['roll_no'], f_cell_c)
            ws.write(row, 4, st['division'], f_cell_c)

            for i, b in enumerate(buckets):
                cell = st['buckets'][b['key']]
                c0 = first_bucket_col + i * 2
                if cell['has']:
                    ws.write_number(row, c0, cell['amount'], f_money)
                    ws.write(row, c0 + 1, cell['status_label'],
                             f_status.get(cell['status'], f_cell_c))
                else:
                    ws.write(row, c0, '-', f_cell_c)
                    ws.write(row, c0 + 1, '-', f_status[''])

            for i, _m in enumerate(months):
                cell = st['months'][i]
                col = first_month_col + i
                if cell['has']:
                    ws.write(row, col, cell['status_label'],
                             f_status.get(cell['status'], f_cell_c))
                else:
                    ws.write(row, col, '-', f_status[''])

            ws.write(row, first_tail_col,
                     '%s / %s' % (st['months_paid'], st['months_total']), f_cell_c)
            ws.write_number(row, first_tail_col + 1, st['total_paid'], f_money)
            ws.write_number(row, first_tail_col + 2, st['total_balance'], f_money)
            ws.write_number(row, first_tail_col + 3, st['total_payable'], f_money)
            row += 1

        # --- totals ---
        if students:
            ws.merge_range(row, 0, row, first_tail_col,
                           'TOTAL  (%s students)' % kpi['students'], f_total_lbl)
            ws.write_number(row, first_tail_col + 1, kpi['paid'], f_total)
            ws.write_number(row, first_tail_col + 2, kpi['balance'], f_total)
            ws.write_number(row, first_tail_col + 3, kpi['payable'], f_total)
            ws.autofilter(hdr_sub, 0, row - 1, last_col)

        # =================================================================
        # Sheets 2 & 3 — Admission fee paid / unpaid lists
        # =================================================================
        def _admission_sheet(name, keep_paid):
            sheet = wb.add_worksheet(name)
            sheet.set_column(0, 0, 5)
            sheet.set_column(1, 1, 26)
            sheet.set_column(2, 2, 14)
            sheet.set_column(3, 3, 8)
            sheet.set_column(4, 4, 12)
            sheet.set_column(5, 5, 14)
            sheet.set_column(6, 6, 12)
            sheet.set_column(7, 7, 14)
            sheet.set_column(8, 8, 14)

            heads = ['S.No', "Student's Name", 'Register No', 'Roll No', 'Division',
                     'Admission Fee', 'Status', 'Payment Mode', 'Payment Date']
            for col, head in enumerate(heads):
                sheet.write(0, col, head, f_head)
            sheet.freeze_panes(1, 0)

            r, total = 1, 0.0
            for st in students:
                cell = st['buckets']['admission']
                if not cell['has']:
                    continue
                is_paid = cell['status'] == 'paid'
                if is_paid != keep_paid:
                    continue
                sheet.write_number(r, 0, r, f_cell_c)
                sheet.write(r, 1, st['student'], f_cell)
                sheet.write(r, 2, st['register_number'], f_cell_c)
                sheet.write(r, 3, st['roll_no'], f_cell_c)
                sheet.write(r, 4, st['division'], f_cell_c)
                sheet.write_number(r, 5, cell['amount'], f_money)
                sheet.write(r, 6, cell['status_label'],
                            f_status.get(cell['status'], f_cell_c))
                sheet.write(r, 7, cell['mode_label'] or '-', f_cell_c)
                sheet.write(r, 8, cell['date'] or '-', f_cell_c)
                total += cell['amount']
                r += 1

            if r > 1:
                sheet.merge_range(r, 0, r, 4, 'TOTAL  (%s students)' % (r - 1), f_total_lbl)
                sheet.write_number(r, 5, total, f_total)
                sheet.autofilter(0, 0, r - 1, len(heads) - 1)
            else:
                sheet.write(1, 0, 'No records.', f_cell)
            return sheet

        _admission_sheet('Admission Paid', True)
        _admission_sheet('Admission Unpaid', False)

        # =================================================================
        # Sheet 4 — Month-wise paid / unpaid summary
        # =================================================================
        ws4 = wb.add_worksheet('Month Summary')
        ws4.set_column(0, 0, 14)
        ws4.set_column(1, 4, 13)
        for col, head in enumerate(
                ['Month', 'Paid', 'Unpaid', 'Overdue', 'No Fee Line']):
            ws4.write(0, col, head, f_head)
        for i, m in enumerate(months):
            counts = {'paid': 0, 'unpaid': 0, 'over_due': 0, 'none': 0}
            for st in students:
                cell = st['months'][i]
                if not cell['has']:
                    counts['none'] += 1
                elif cell['status'] in counts:
                    counts[cell['status']] += 1
                else:
                    counts['unpaid'] += 1
            ws4.write(i + 1, 0, m['label'], f_cell)
            ws4.write_number(i + 1, 1, counts['paid'], f_status['paid'])
            ws4.write_number(i + 1, 2, counts['unpaid'], f_status['unpaid'])
            ws4.write_number(i + 1, 3, counts['over_due'], f_status['over_due'])
            ws4.write_number(i + 1, 4, counts['none'], f_cell_c)

        wb.close()
        output.seek(0)
        filename = 'student_fee_tracker_%s.xlsx' % fields.Date.today().strftime('%d_%m_%Y')
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type',
                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )
