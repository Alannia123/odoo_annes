import calendar
from datetime import date

from odoo import http, tools, _, SUPERUSER_ID
from odoo.exceptions import AccessDenied, AccessError, MissingError, UserError, ValidationError
from odoo.http import content_disposition, Controller, request, route
from odoo.tools import consteq
from datetime import date



class WebsiteAttendance(http.Controller):

    @http.route('/school/student_attendance', type='http', auth='user', website=True)
    def view_attendance(self, month=None, year=None):
        partner = request.env.user.partner_id
        cr = request.env.cr
        cr.execute("""
            SELECT id 
            FROM ala_education_student 
            WHERE partner_id = %s 
            LIMIT 1
        """, (partner.id,))
        row = request.env.cr.fetchone()
        student_id = row[0] if row else False
        student = request.env['ala.education.student'].browse(student_id) if student_id else False
        today = date.today()
        year = int(year) if year else today.year
        month = int(month) if month else today.month

        # Get weekday of first day and total days in month
        first_weekday, total_days = calendar.monthrange(year, month)

        calendar.setfirstweekday(calendar.SUNDAY)
        month_matrix = calendar.monthcalendar(year, month)

        start_date = date(year, month, 1)
        end_date = date(year, month, total_days)

        # Get attendance records
        cr.execute("""
            SELECT id 
            FROM ala_education_attendance_line
            WHERE state = 'done'
              AND student_id = %s
              AND date BETWEEN %s AND %s
        """, (student.id, start_date, end_date))
        attendance_ids = [row[0] for row in cr.fetchall()]
        attendance_records = request.env['ala.education.attendance.line'].sudo().browse(attendance_ids)

        # Holidays
        cr.execute("""
            SELECT id 
            FROM ala_school_event
            WHERE is_holiday = TRUE
              AND event_date BETWEEN %s AND %s
        """, (start_date, end_date))
        holiday_ids = [row[0] for row in cr.fetchall()]
        holiday_records = request.env['ala.school.event'].sudo().browse(holiday_ids)


        # Map attendance status by day
        status_by_day = {}
        for rec in attendance_records:
            if rec.present:
                status_by_day.update({rec.date.day: 'present'})
            else:
                status_by_day.update({rec.date.day: 'absent'})

        # Holidays overwrite attendance if same day
        for holiday in holiday_records:
            status_by_day.update({holiday.event_date.day: 'holiday'})

        # For prev/next buttons
        prev_month = month - 1 or 12
        prev_year = year - 1 if prev_month == 12 else year
        next_month = month + 1 if month < 12 else 1
        next_year = year + 1 if next_month == 1 else year

        # status_by_day = {r.date.day: r.status for r in records}

        # Prepare weeks (each week = 7 days, with None where no day exists)

        return request.render('ala_student_portal.template_attendance_calendar', {
            'month': calendar.month_name[month],
            'month_num': month,
            'year': year,
            'weeks': month_matrix,
            'status_by_day': status_by_day,
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
        })
