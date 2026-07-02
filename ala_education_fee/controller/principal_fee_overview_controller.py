# -*- coding: utf-8 -*-
import io

from odoo import http
from odoo.http import request, content_disposition

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class PrincipalFeeOverviewController(http.Controller):

    @http.route('/mis_education_fee/principal_fee_overview/xlsx',
                type='http', auth='user')
    def principal_fee_overview_xlsx(self, date_from=None, date_to=None,
                                    payment_mode=None, **kw):
        if xlsxwriter is None:
            return request.not_found()

        # Principal-only export, mirror the menu/group restriction.
        if not request.env.user.has_group(
                'mis_education_core.group_education_principal'):
            return request.not_found()

        Line = request.env['student.fee.line']
        data = Line.get_principal_fee_overview(
            date_from or False, date_to or False, payment_mode or False,
        )
        lines, totals = data['lines'], data['totals']

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = wb.add_worksheet('Fee Overview')

        f_title = wb.add_format({'bold': True, 'font_size': 14})
        f_meta = wb.add_format({'italic': True, 'font_color': '#666666'})
        f_head = wb.add_format({
            'bold': True, 'bg_color': '#16222a', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter',
        })
        f_text = wb.add_format({'border': 1})
        f_money = wb.add_format({'border': 1, 'num_format': '#,##,##0.00'})
        f_tot_lbl = wb.add_format({'bold': True, 'border': 1,
                                   'bg_color': '#F2F2F2', 'align': 'right'})
        f_tot_money = wb.add_format({'bold': True, 'border': 1,
                                     'bg_color': '#F2F2F2',
                                     'num_format': '#,##,##0.00'})

        ws.write(0, 0, 'Fee Collection Overview', f_title)
        ws.write(1, 0, 'Period: %s \u2192 %s' % (date_from or '...',
                                                 date_to or '...'), f_meta)

        headers = ['#', 'Student', 'Division', 'Roll No',
                   'Register No', 'Mode', 'Amount']
        row = 3
        for col, head in enumerate(headers):
            ws.write(row, col, head, f_head)
        for col, w in enumerate([4, 26, 14, 10, 16, 12, 16]):
            ws.set_column(col, col, w)

        for idx, line in enumerate(lines, start=1):
            row += 1
            ws.write(row, 0, idx, f_text)
            ws.write(row, 1, line['student'], f_text)
            ws.write(row, 2, line['division'], f_text)
            ws.write(row, 3, line['roll_no'], f_text)
            ws.write(row, 4, line['register_number'], f_text)
            ws.write(row, 5, line['payment_mode'], f_text)
            ws.write_number(row, 6, line['amount'], f_money)

        row += 1
        ws.merge_range(row, 0, row, 5,
                       'Total (%s records)' % totals['count'], f_tot_lbl)
        ws.write_number(row, 6, totals['amount'], f_tot_money)

        wb.close()
        output.seek(0)
        xlsx_data = output.read()

        filename = 'fee_overview_%s_%s.xlsx' % (date_from or 'all',
                                                date_to or 'all')
        return request.make_response(
            xlsx_data,
            headers=[
                ('Content-Type',
                 'application/vnd.openxmlformats-officedocument.'
                 'spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )