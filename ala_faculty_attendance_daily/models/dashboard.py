# -*- coding: utf-8 -*-
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

STATUSES = ['present', 'leave', 'on_duty', 'med_leave']


class FacultyAttendanceDashboard(models.Model):
    _inherit = 'ala.faculty.attendance.sheet'

    @api.model
    def get_dashboard_data(self, period='day', ref_date=None, employee_id=None):
        """Aggregated data for the OWL dashboard.

        :param period: 'day' | 'week' | 'month'
        :param ref_date: ISO date string the period is anchored on
        :param employee_id: optional hr.employee id to focus the dashboard on
        """
        Line = self.env['ala.faculty.attendance.sheet.line']
        company = self.env.company
        ref = (fields.Date.from_string(ref_date)
               if ref_date else fields.Date.context_today(self))

        if period == 'week':
            date_from = ref - timedelta(days=ref.weekday())  # Monday
            date_to = date_from + timedelta(days=6)
            range_label = '%s – %s' % (date_from.strftime('%d %b'),
                                       date_to.strftime('%d %b %Y'))
        elif period == 'month':
            date_from = ref.replace(day=1)
            date_to = date_from + relativedelta(months=1, days=-1)
            range_label = ref.strftime('%B %Y')
        else:
            period = 'day'
            date_from = date_to = ref
            range_label = ref.strftime('%A, %d %b %Y')

        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
        ]
        if employee_id:
            domain.append(('employee_id', '=', int(employee_id)))

        # ---- KPI totals -------------------------------------------------
        totals = dict.fromkeys(STATUSES, 0)
        for status, count in Line._read_group(domain, ['status'], ['__count']):
            totals[status] = count
        total = sum(totals.values())
        rate = round((totals['present'] + totals['on_duty'])
                     / total * 100, 1) if total else 0.0

        # ---- Trend (per day) -------------------------------------------
        trend_map = {}
        for gdate, status, count in Line._read_group(
                domain, ['date:day', 'status'], ['__count']):
            trend_map[(fields.Date.to_date(gdate), status)] = count
        days, d = [], date_from
        while d <= date_to:
            days.append(d)
            d += timedelta(days=1)
        trend = {
            'labels': [d.strftime('%d') if period == 'month'
                       else d.strftime('%a %d') for d in days],
        }
        for status in STATUSES:
            trend[status] = [trend_map.get((d, status), 0) for d in days]

        # ---- Employee-wise ---------------------------------------------
        emp_map = {}
        for employee, status, count in Line._read_group(
                domain, ['employee_id', 'status'], ['__count']):
            rec = emp_map.setdefault(employee.id, {
                'id': employee.id,
                'name': employee.name,
                'roll': employee.faculty_roll_no,
                **dict.fromkeys(STATUSES, 0),
            })
            rec[status] = count
        employees = sorted(emp_map.values(),
                           key=lambda r: (r['roll'] or 99999))
        for emp in employees:
            emp_total = sum(emp[s] for s in STATUSES)
            emp['total'] = emp_total
            emp['rate'] = round((emp['present'] + emp['on_duty'])
                                / emp_total * 100, 1) if emp_total else 0.0
            if period == 'day':
                emp['day_status'] = next(
                    (s for s in STATUSES if emp[s]), False)

        # ---- Day sheet status chip -------------------------------------
        sheet_info = False
        if period == 'day':
            sheet = self.search([('date', '=', ref),
                                 ('company_id', '=', company.id)], limit=1)
            sheet_info = {
                'exists': bool(sheet),
                'state': sheet.state if sheet else False,
                'auto_closed': sheet.auto_closed if sheet else False,
                'id': sheet.id if sheet else False,
            }

        employee_focus = False
        if employee_id:
            employee = self.env['hr.employee'].browse(int(employee_id))
            if employee.exists():
                employee_focus = {'id': employee.id, 'name': employee.name}

        # Faculty announcements ticker (soft dependency on the ERP
        # dashboard module which owns ala.dashboard.announcement)
        announcements = []
        if 'ala.dashboard.announcement' in self.env:
            announcements = self.env[
                'ala.dashboard.announcement'].get_running_announcements()

        return {
            'period': period,
            'range_label': range_label,
            'date_from': fields.Date.to_string(date_from),
            'date_to': fields.Date.to_string(date_to),
            'kpi': {**totals, 'total': total, 'rate': rate},
            'trend': trend,
            'employees': employees,
            'sheet_info': sheet_info,
            'employee_focus': employee_focus,
            'announcements': announcements,
        }
