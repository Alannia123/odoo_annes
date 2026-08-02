# -*- coding: utf-8 -*-
"""XLSX export for the Principal Fee Overview.

The controller re-runs the same model methods the screen uses, so an
export can never disagree with what the principal was looking at.
"""

import io

from odoo import fields, http
from odoo.http import content_disposition, request

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class PrincipalFeeOverviewController(http.Controller):

    @http.route('/ala_fee_dashboard/principal_fee_overview/xlsx',
                type='http', auth='user')
    def principal_fee_overview_xlsx(self, date_from='', date_to='',
                                    payment_mode='', division_id='',
                                    view_type='summary', **kw):
        if xlsxwriter is None:
            return request.make_response(
                "The 'xlsxwriter' Python package is not installed on this "
                "server, so Excel export is unavailable.",
                headers=[('Content-Type', 'text/plain')])

        FeeLine = request.env['ala.student.fee.line']
        division = int(division_id) if division_id else False

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Fee Collection')

        fmt_title = workbook.add_format({
            'bold': True, 'font_size': 14, 'font_color': '#14306B'})
        fmt_meta = workbook.add_format({'font_size': 9, 'font_color': '#64748B'})
        fmt_header = workbook.add_format({
            'bold': True, 'bg_color': '#14306B', 'font_color': '#FFFFFF',
            'border': 1, 'align': 'center', 'valign': 'vcenter',
            'text_wrap': True})
        fmt_money = workbook.add_format({'num_format': '#,##,##0.00', 'border': 1})
        fmt_money_bold = workbook.add_format({
            'num_format': '#,##,##0.00', 'bold': True, 'border': 1,
            'bg_color': '#F1F5F9'})
        fmt_cell = workbook.add_format({'border': 1})
        fmt_bold = workbook.add_format({'bold': True, 'border': 1,
                                        'bg_color': '#F1F5F9'})
        fmt_date = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1})

        # ---- title block ------------------------------------------------
        company = request.env.company.name
        window = '%s to %s' % (date_from or 'start', date_to or 'today')
        sheet.write(0, 0, 'Fee Collection Overview', fmt_title)
        sheet.write(1, 0, '%s  |  %s' % (company, window), fmt_meta)
        top = 3

        if view_type == 'summary':
            payload = FeeLine.get_principal_fee_summary(
                date_from or False, date_to or False,
                payment_mode or False, division)
            mode_cols = payload['mode_columns']

            headers = (['#', 'Date'] + [m['label'] for m in mode_cols]
                       + ['Receipts', 'Total'])
            for col, title in enumerate(headers):
                sheet.write(top, col, title, fmt_header)
            sheet.set_column(0, 0, 5)
            sheet.set_column(1, 1, 13)
            sheet.set_column(2, len(headers) - 1, 15)
            sheet.freeze_panes(top + 1, 2)

            row_idx = top + 1
            for row in payload['rows']:
                sheet.write(row_idx, 0, row['sno'], fmt_cell)
                sheet.write_datetime(
                    row_idx, 1, fields.Date.from_string(row['date']), fmt_date)
                for j, mode in enumerate(mode_cols):
                    sheet.write(row_idx, 2 + j,
                                row['modes'][mode['key']], fmt_money)
                sheet.write(row_idx, 2 + len(mode_cols), row['count'], fmt_cell)
                sheet.write(row_idx, 3 + len(mode_cols),
                            row['total'], fmt_money_bold)
                row_idx += 1

            totals = payload['totals']
            sheet.write(row_idx, 0, '', fmt_bold)
            sheet.write(row_idx, 1,
                        'Grand Total (%s days)' % totals['days'], fmt_bold)
            for j, mode in enumerate(mode_cols):
                sheet.write(row_idx, 2 + j,
                            totals['by_mode'][mode['key']], fmt_money_bold)
            sheet.write(row_idx, 2 + len(mode_cols), totals['count'], fmt_bold)
            sheet.write(row_idx, 3 + len(mode_cols),
                        totals['amount'], fmt_money_bold)

            filename = 'fee_collection_daywise_summary.xlsx'

        else:
            payload = FeeLine.get_principal_fee_overview(
                date_from or False, date_to or False,
                payment_mode or False, division, limit=20000)

            headers = ['#', 'Date', 'Student', 'Reg. No', 'Division',
                       'Particulars', 'Mode', 'Fine', 'Concession', 'Amount']
            for col, title in enumerate(headers):
                sheet.write(top, col, title, fmt_header)
            sheet.set_column(0, 0, 5)
            sheet.set_column(1, 1, 13)
            sheet.set_column(2, 2, 26)
            sheet.set_column(3, 4, 14)
            sheet.set_column(5, 5, 32)
            sheet.set_column(6, 6, 15)
            sheet.set_column(7, 9, 14)
            sheet.freeze_panes(top + 1, 3)

            row_idx = top + 1
            for line in payload['lines']:
                sheet.write(row_idx, 0, line['sno'], fmt_cell)
                if line['date']:
                    sheet.write_datetime(
                        row_idx, 1,
                        fields.Date.from_string(line['date']), fmt_date)
                else:
                    sheet.write(row_idx, 1, '', fmt_cell)
                sheet.write(row_idx, 2, line['student'], fmt_cell)
                sheet.write(row_idx, 3, line['register_number'], fmt_cell)
                sheet.write(row_idx, 4, line['division'], fmt_cell)
                sheet.write(row_idx, 5, line['description'], fmt_cell)
                sheet.write(row_idx, 6, line['mode_label'], fmt_cell)
                sheet.write(row_idx, 7, line['fine'], fmt_money)
                sheet.write(row_idx, 8, line['concession'], fmt_money)
                sheet.write(row_idx, 9, line['amount'], fmt_money)
                row_idx += 1

            totals = payload['totals']
            sheet.write(row_idx, 0, '', fmt_bold)
            sheet.write(row_idx, 1,
                        'Total (%s receipts)' % totals['count'], fmt_bold)
            for col in range(2, 7):
                sheet.write(row_idx, col, '', fmt_bold)
            sheet.write(row_idx, 7, totals['fine'], fmt_money_bold)
            sheet.write(row_idx, 8, totals['concession'], fmt_money_bold)
            sheet.write(row_idx, 9, totals['amount'], fmt_money_bold)

            filename = 'fee_collection_receipt_detail.xlsx'

        workbook.close()
        output.seek(0)
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type',
                 'application/vnd.openxmlformats-officedocument'
                 '.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )
