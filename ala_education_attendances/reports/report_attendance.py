from odoo import models
from datetime import date, timedelta

class ReportMonthlyAttendance(models.AbstractModel):
    _name = 'report.ala_education_attendances.monthly_attendance_report_temp'
    _description = 'Monthly Attendance Report'

    def _get_month_dates(self, year, month):
        start = date(year, month, 1)
        end = (start.replace(month=month % 12 + 1, day=1) - timedelta(days=1))
        end_date = (end.replace(year=year))
        return [(start + timedelta(days=i)) for i in range((end_date - start).days + 1)]

    @staticmethod
    def _format_attendance(edu_attendances):
        result = {}
        for attendance in edu_attendances:
            for line in attendance.attendance_line_ids:
                student = line.student_id.id
                date_str = line.date.strftime('%Y-%m-%d')
                result.setdefault(student, {})[date_str] = line.present
        return result

    def _get_report_values(self, docids, data=None):
        division_id = int(data['division_id'][0])
        month = int(data['month'])
        year = int(data['year'])
        students = self.env['ala.education.student'].search([('class_division_id', '=', division_id)])
        students_sorted = sorted(
            students,
            key=lambda s: int(s.roll_no) if s.roll_no.isdigit() else s.roll_no
        )
        dates = self._get_month_dates(year, month)


        edu_attendances = self.env['ala.education.attendance'].search([
            ('state', '=', 'done'),
            ('date', '>=', dates[0]),
            ('date', '<=', dates[-1]), ('division_id', '=', division_id)
        ])

        attendance_dict = self._format_attendance(edu_attendances)


        return {
            'doc_ids': docids,
            'doc_model': 'ala.education.attendance',
            'students': students_sorted,
            'dates': dates,
            'attendance_dict': attendance_dict,
            'standard_name': data['standard_name'],
            'month_str': data['month_str'],
            'total_days': len(edu_attendances),
            'academic_year_id': data['academic_year_id'][1],
        }
