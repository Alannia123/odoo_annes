# -*- coding: utf-8 -*-
import base64
import io
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

STATUS_CODE = {
    'present': 'P',
    'leave': 'L',
    'on_duty': 'OD',
    'med_leave': 'ML',
}
WORKED = ('present', 'on_duty')


class FacultyAttendanceReportWizard(models.TransientModel):
    _name = 'ala.faculty.attendance.report.wizard'
    _description = 'Faculty Monthly Attendance Report'

    month_date = fields.Date(
        string='Month', required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1),
        help='Pick any date inside the month to report on')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company)
    file_data = fields.Binary(string='File', readonly=True)
    file_name = fields.Char(string='File Name', readonly=True)

    # ------------------------------------------------------------------
    # Matrix data (shared by PDF and XLSX)
    # ------------------------------------------------------------------
    def _get_matrix(self):
        self.ensure_one()
        date_from = self.month_date.replace(day=1)
        date_to = date_from + relativedelta(months=1, days=-1)
        days = []
        d = date_from
        while d <= date_to:
            days.append(d)
            d += timedelta(days=1)

        lines = self.env['ala.faculty.attendance.sheet.line'].sudo().search([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', self.company_id.id),
        ])
        cell_map = {(line.employee_id.id, line.date): line.status
                    for line in lines}

        employees = self.env['hr.employee'].sudo().search([
            ('faculty_attendance_active', '=', True),
            ('faculty_roll_no', '>', 0),
            ('company_id', '=', self.company_id.id),
        ]).sorted(key=lambda e: e.faculty_roll_no)
        # also include anyone who has lines but was later deactivated
        extra = lines.mapped('employee_id') - employees
        employees = employees | extra

        rows = []
        for emp in employees.sorted(key=lambda e: e.faculty_roll_no or 99999):
            counts = dict.fromkeys(STATUS_CODE, 0)
            cells = []
            for day in days:
                status = cell_map.get((emp.id, day))
                if status:
                    counts[status] += 1
                cells.append({
                    'code': STATUS_CODE.get(status, '-') if status else '-',
                    'status': status or False,
                    'is_sunday': day.weekday() == 6,
                })
            marked = sum(counts.values())
            worked = sum(counts[s] for s in WORKED)
            rows.append({
                'roll': emp.faculty_roll_no,
                'name': emp.name,
                'cells': cells,
                'present': counts['present'],
                'leave': counts['leave'],
                'on_duty': counts['on_duty'],
                'med_leave': counts['med_leave'],
                'marked': marked,
                'rate': round(worked / marked * 100, 1) if marked else 0.0,
            })
        return {
            'month_label': date_from.strftime('%B %Y'),
            'date_from': date_from,
            'date_to': date_to,
            'days': days,
            'rows': rows,
            'company': self.company_id,
        }

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------
    def action_print_pdf(self):
        self.ensure_one()
        if not self._get_matrix()['rows']:
            raise UserError(_('No faculty found for this month.'))
        return self.env.ref(
            'ala_faculty_attendance_daily.action_report_faculty_att_monthly'
        ).report_action(self)

    # ------------------------------------------------------------------
    # XLSX
    # ------------------------------------------------------------------
    def action_export_xlsx(self):
        self.ensure_one()
        import xlsxwriter

        data = self._get_matrix()
        if not data['rows']:
            raise UserError(_('No faculty found for this month.'))

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        sheet = workbook.add_worksheet('Attendance %s'
                                       % data['date_from'].strftime('%b-%Y'))

        fmt_title = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center',
            'valign': 'vcenter', 'font_color': '#134E4A'})
        fmt_head = workbook.add_format({
            'bold': True, 'bg_color': '#134E4A', 'font_color': '#FFFFFF',
            'align': 'center', 'valign': 'vcenter', 'border': 1,
            'font_size': 9})
        fmt_sun = workbook.add_format({
            'bold': True, 'bg_color': '#F59E0B', 'font_color': '#FFFFFF',
            'align': 'center', 'valign': 'vcenter', 'border': 1,
            'font_size': 9})
        fmt_name = workbook.add_format({
            'border': 1, 'font_size': 9, 'valign': 'vcenter'})
        fmt_roll = workbook.add_format({
            'border': 1, 'font_size': 9, 'align': 'center', 'bold': True,
            'font_color': '#0F766E'})
        cell_formats = {
            'P': workbook.add_format({
                'border': 1, 'align': 'center', 'font_size': 8,
                'font_color': '#0F766E', 'bold': True}),
            'L': workbook.add_format({
                'border': 1, 'align': 'center', 'font_size': 8,
                'font_color': '#DC2626', 'bold': True,
                'bg_color': '#FEE2E2'}),
            'OD': workbook.add_format({
                'border': 1, 'align': 'center', 'font_size': 8,
                'font_color': '#B45309', 'bold': True,
                'bg_color': '#FEF3C7'}),
            'ML': workbook.add_format({
                'border': 1, 'align': 'center', 'font_size': 8,
                'font_color': '#475569', 'bold': True,
                'bg_color': '#E2E8F0'}),
            '-': workbook.add_format({
                'border': 1, 'align': 'center', 'font_size': 8,
                'font_color': '#94A3B8'}),
        }
        fmt_sun_cell = workbook.add_format({
            'border': 1, 'align': 'center', 'font_size': 8,
            'bg_color': '#FDF6EC', 'font_color': '#B45309'})
        fmt_total = workbook.add_format({
            'border': 1, 'align': 'center', 'font_size': 9, 'bold': True})
        fmt_rate = workbook.add_format({
            'border': 1, 'align': 'center', 'font_size': 9, 'bold': True,
            'font_color': '#0F766E', 'num_format': '0.0"%"'})

        n_days = len(data['days'])
        total_cols = 2 + n_days + 6

        sheet.merge_range(0, 0, 0, total_cols - 1,
                          '%s — Faculty Attendance — %s'
                          % (data['company'].name, data['month_label']),
                          fmt_title)
        sheet.set_row(0, 26)

        header_row = 2
        sheet.write(header_row, 0, 'Roll', fmt_head)
        sheet.write(header_row, 1, 'Faculty', fmt_head)
        for idx, day in enumerate(data['days']):
            fmt = fmt_sun if day.weekday() == 6 else fmt_head
            sheet.write(header_row, 2 + idx, day.day, fmt)
        summary_heads = ['P', 'L', 'OD', 'ML', 'Marked', '%']
        for idx, head in enumerate(summary_heads):
            sheet.write(header_row, 2 + n_days + idx, head, fmt_head)

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 26)
        sheet.set_column(2, 1 + n_days, 3.4)
        sheet.set_column(2 + n_days, 2 + n_days + 5, 7)

        row_idx = header_row + 1
        for row in data['rows']:
            sheet.write(row_idx, 0, row['roll'], fmt_roll)
            sheet.write(row_idx, 1, row['name'], fmt_name)
            for cell_pos, cell in enumerate(row['cells']):
                if cell['code'] == '-' and cell['is_sunday']:
                    sheet.write(row_idx, 2 + cell_pos, 'S', fmt_sun_cell)
                else:
                    sheet.write(row_idx, 2 + cell_pos, cell['code'],
                                cell_formats[cell['code']])
            base = 2 + n_days
            sheet.write(row_idx, base, row['present'], fmt_total)
            sheet.write(row_idx, base + 1, row['leave'], fmt_total)
            sheet.write(row_idx, base + 2, row['on_duty'], fmt_total)
            sheet.write(row_idx, base + 3, row['med_leave'], fmt_total)
            sheet.write(row_idx, base + 4, row['marked'], fmt_total)
            sheet.write(row_idx, base + 5, row['rate'], fmt_rate)
            row_idx += 1

        legend_fmt = workbook.add_format({
            'font_size': 8, 'font_color': '#64748B'})
        sheet.write(row_idx + 1, 1,
                    'P = Present   L = Leave   OD = On Duty   '
                    'ML = Med Leave   S = Sunday   - = Not Marked   '
                    '% = (Present + On Duty) / Marked days', legend_fmt)
        sheet.freeze_panes(header_row + 1, 2)
        workbook.close()

        self.write({
            'file_data': base64.b64encode(buffer.getvalue()),
            'file_name': 'Faculty_Attendance_%s.xlsx'
                         % data['date_from'].strftime('%b_%Y'),
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=%s&id=%s&field=file_data'
                   '&download=true&filename=%s'
                   % (self._name, self.id, self.file_name),
            'target': 'self',
        }


class ReportFacultyAttMonthly(models.AbstractModel):
    _name = 'report.ala_faculty_attendance_daily.report_att_monthly'
    _description = 'Faculty Monthly Attendance PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env['ala.faculty.attendance.report.wizard'].browse(
            docids)
        # Safe defaults regardless of entry point
        matrices = {}
        for wizard in wizards:
            try:
                matrices[wizard.id] = wizard._get_matrix()
            except Exception:
                matrices[wizard.id] = {
                    'month_label': '', 'days': [], 'rows': [],
                    'company': self.env.company,
                }
        return {
            'doc_ids': docids,
            'doc_model': 'ala.faculty.attendance.report.wizard',
            'docs': wizards,
            'matrices': matrices,
        }
