# -*- coding: utf-8 -*-

import pandas
from datetime import date, timedelta
from odoo import api, fields, models
from odoo.http import request
from odoo.tools import date_utils
from odoo.fields import Date



class EducationStudent(models.Model):
    _inherit = 'ala.education.student'

    def action_education_attendance_line_student(self):
        self.ensure_one()

        # Find current academic year
        academic_year = self.env['ala.education.academic.year'].search(
            [('enable', '=', True)], limit=1
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Attendance',
            'res_model': 'ala.education.attendance.line',
            'view_mode': 'list,calendar',
            'domain': [
                ('student_id', '=', self.id),
                ('state', '=', 'done'),
                ('academic_year_id', '=', academic_year.id)
            ],
            'context': {
                'default_student_id': self.id
            }
        }


    @staticmethod
    def _format_student_attendance(attendance_recs):
        result = {}
        for attendance in attendance_recs:
            for line in attendance.attendance_line_ids:
                student_id = line.student_id.id
                date_str = attendance.date.strftime('%Y-%m-%d')

                # ✅ Convert None → False
                result.setdefault(student_id, {})[date_str] = bool(line.present)

        return result

    @api.model
    def get_student_attendance_dashboard(self, division_id, option):
        """Return student attendance dashboard data (like employee dashboard)
           Uses only attendance table. No leaves considered.
           If attendance not found -> blank.
        """

        # ---------------------------------------
        # 1. Generate Dates Based on Option
        # ---------------------------------------
        dates = False
        if option == 'this_week':
            dates = pandas.date_range(
                date_utils.start_of(fields.Date.today(), 'week'),
                date_utils.end_of(fields.Date.today(), 'week'),
                freq='d'
            ).strftime("%Y-%m-%d").tolist()

        elif option == 'this_month':
            dates = pandas.date_range(
                date_utils.start_of(fields.Date.today(), 'month'),
                date_utils.end_of(fields.Date.today(), 'month'),
                freq='d'
            ).strftime("%Y-%m-%d").tolist()
        elif option == 'last_month':
            today = fields.Date.today()

            last_month_date = date_utils.subtract(today, months=1)

            dates = pandas.date_range(
                date_utils.start_of(last_month_date, 'month'),
                date_utils.end_of(last_month_date, 'month'),
                freq='d'
            ).strftime("%Y-%m-%d").tolist()

        elif option == 'last_15_days':
            dates = [str(date.today() - timedelta(days=d)) for d in range(15)]
            dates = dates[::-1]  # Reverse for calendar layout

        # ---------------------------------------
        # 3. Fetch All Attendance Records For Date Range
        # ---------------------------------------
        start_date = Date.from_string(dates[0])
        end_date = Date.from_string(dates[-1])

        students_sorted = False
        if division_id == 'all':
            attendance_recs = self.env['ala.education.attendance'].search([
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('state', '=', 'done'),
            ])
            students_sorted = self.env['ala.education.student'].search([], order="id desc")
        else:
            attendance_recs = self.env['ala.education.attendance'].search([
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('state', '=', 'done'),
                ('division_id', '=', int(division_id)),
            ])
            students = self.env['ala.education.student'].search([('class_division_id', '=', int(division_id))])

            # Sort by roll number
            students_sorted = sorted(
                students,
                key=lambda s: int(s.roll_no) if str(s.roll_no).isdigit() else s.roll_no
            )

        print('att',attendance_recs)
        print('att--------------',students_sorted)

        # attendance_dict = {student_id: { 'YYYY-MM-DD': present(1/0) } }
        attendance_dict = self._format_student_attendance(attendance_recs)
        print('AEEEEEEEEEEEEEEE',attendance_dict)

        # ---------------------------------------
        # 4. Build Final Student Dashboard Output
        # ---------------------------------------
        student_data = []
        for student in students_sorted:
            res_config = self.env['res.config.settings'].search([], limit=1,
                                                                order='id desc')
            daily_rows = []
            total_present = 0

            for dt in dates:
                present_val = attendance_dict.get(student.id, {}).get(dt, None)
                # print('DEEEEEEEEEEEEEEWWWWWWWWW',present_val,type(present_val))

                # Convert present status to readable
                if present_val == True:
                    print('Present=============',present_val,type(present_val))
                    state = res_config.present
                    color = "#ffffff"  # green
                    total_present += 1
                elif present_val == False:
                    print('Absent=============', present_val,type(present_val))
                    state = res_config.absent
                    color = "#ffffff"  # red
                else:
                    print('Nothing=============', present_val, type(present_val))
                    state = ""  # blank - no attendance record
                    color = "#E7E9EB"

                daily_rows.append({
                    'id': student.id,
                    'date': dt,
                    'state': state,
                    'color': color,
                })
                # print('DDDFFFFFFFFFFFFFFFFFFFFFF',state,color,present_val)

            student_data.append({
                'id': student.id,
                'name': student.name,
                'division': student.class_division_id.name,
                'roll_no': student.roll_no,
                'attendance': daily_rows,
                'total_present': total_present,
            })

        return {
            'student_data': student_data,
            'filtered_duration_dates': dates,
        }

    # @api.model
    # def get_student_leave_data(self, option):
    #     """Returns data to the dashboard"""
    #     student_data = []
    #     res_config = self.env['res.config.settings'].search([], limit=1,
    #                                                         order='id desc')
    #     dates = False
    #     if option == 'this_week':
    #         dates = pandas.date_range(
    #             date_utils.start_of(fields.Date.today(), 'week'),
    #             date_utils.end_of(fields.Date.today(), 'week')
    #             - timedelta(
    #                 days=0),
    #             freq='d').strftime(
    #             "%Y-%m-%d").tolist()
    #     elif option == 'this_month':
    #         dates = pandas.date_range(
    #             date_utils.start_of(fields.Date.today(), 'month'),
    #             date_utils.end_of(fields.Date.today(), 'month')
    #             - timedelta(
    #                 days=0),
    #             freq='d').strftime(
    #             "%Y-%m-%d").tolist()
    #     elif option == 'last_15_days':
    #         dates = [str(date.today() - timedelta(days=day))
    #                  for day in range(15)]
    #     cids = request.httprequest.cookies.get('cids')
    #     allowed_company_ids = [int(cid) for cid in cids.split(',')]
    #     for employee in self.env['hr.employee'].search(
    #             [('company_id', '=', allowed_company_ids)]):
    #         leave_data = []
    #         student_present_dates = []
    #         student_leave_dates = []
    #         total_absent_count = 0
    #         query = ("""
    #             SELECT hl.id,employee_id,request_date_from,request_date_to,
    #             hlt.leave_code,hlt.color
    #             FROM hr_leave hl
	# 			INNER JOIN hr_leave_type hlt ON hlt.id = hl.holiday_status_id
    #             WHERE hl.state = 'validate' AND employee_id = '%s'"""
    #                  % employee.id)
    #         self._cr.execute(query)
    #         all_leave_rec = self._cr.dictfetchall()
    #         for leave in all_leave_rec:
    #             leave_dates = pandas.date_range(
    #                 leave.get('request_date_from'),
    #                 leave.get('request_date_to') - timedelta(
    #                     days=0),
    #                 freq='d').strftime(
    #                 "%Y-%m-%d").tolist()
    #             leave_dates.insert(0, leave.get('leave_code'))
    #             leave_dates.insert(1, leave.get('color'))
    #             for leave_date in leave_dates:
    #                 if leave_date in dates:
    #                     student_leave_dates.append(
    #                         leave_date
    #                     )
    #         for employee_check_in in employee.attendance_ids:
    #             student_present_dates.append(
    #                 str(employee_check_in.check_in.date()))
    #         for leave_date in dates:
    #             color = "#ffffff"
    #             marks = self.env[
    #                 'res.config.settings'].search([], limit=1)
    #             state = None
    #             if marks:
    #                 if leave_date in student_present_dates:
    #                     state = res_config.present
    #                 else:
    #                     state = res_config.absent
    #             if leave_date in student_leave_dates:
    #                 state = leave_dates[0]
    #                 color = "#F06050" if leave_dates[1] == 1 \
    #                     else "#F4A460" if leave_dates[1] == 2 \
    #                     else "#F7CD1F" if leave_dates[1] == 3 \
    #                     else "#6CC1ED" if leave_dates[1] == 4 \
    #                     else "#814968" if leave_dates[1] == 5 \
    #                     else "#EB7E7F" if leave_dates[1] == 6 \
    #                     else "#2C8397" if leave_dates[1] == 7 \
    #                     else "#475577" if leave_dates[1] == 8 \
    #                     else "#D6145F" if leave_dates[1] == 9 \
    #                     else "#30C381" if leave_dates[1] == 10 \
    #                     else "#9365B8" if leave_dates[1] == 11 \
    #                     else "#ffffff"
    #                 total_absent_count += 1
    #             leave_data.append({
    #                 'id': employee.id,
    #                 'leave_date': leave_date,
    #                 'state': state,
    #                 'color': color
    #             })
    #         student_data.append({
    #             'id': employee.id,
    #             'name': employee.name,
    #             'leave_data': leave_data[::-1],
    #             'total_absent_count': total_absent_count
    #         })
    #     return {
    #         'employee_data': student_data,
    #         'filtered_duration_dates': dates[::-1]
    #     }
