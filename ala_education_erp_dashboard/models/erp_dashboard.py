# -*- coding: utf-8 -*-

from odoo import api, fields, models

MANAGER_GROUPS = (
    'ala_education_core.group_education_principal',
    'ala_education_core.group_education_office_admin',
)


class ErpDashboard(models.Model):
    """The Dashboard model used to build the all details of the
    Educational system"""
    _name = "ala.erp.dashboard"
    _description = "Education ERP Dashboard"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _is_dashboard_manager(self):
        user = self.env.user
        return any(user.has_group(group) for group in MANAGER_GROUPS)

    def _get_current_year_id(self):
        current_year = self.env['ala.education.academic.year'].search([
            ('enable', '=', True)
        ], limit=1)
        return current_year.id or 0

    def _faculty_attendance_block(self):
        """Faculty (teacher) attendance summary. Soft dependency on
        ala_faculty_attendance_daily — returns False when not installed."""
        if 'ala.faculty.attendance.sheet' not in self.env:
            return False
        Sheet = self.env['ala.faculty.attendance.sheet'].sudo()
        today_data = Sheet.get_dashboard_data(period='day')
        month_data = Sheet.get_dashboard_data(period='month')
        total_faculty = self.env['hr.employee'].sudo().search_count([
            ('faculty_attendance_active', '=', True),
            ('faculty_roll_no', '>', 0),
            ('company_id', '=', self.env.company.id),
        ])
        marked = today_data['kpi']['total']
        return {
            'today_present': today_data['kpi'].get('present', 0),
            'today_leave': today_data['kpi'].get('leave', 0),
            'today_on_duty': today_data['kpi'].get('on_duty', 0),
            'today_med_leave': today_data['kpi'].get('med_leave', 0),
            'today_unmarked': max(total_faculty - marked, 0),
            'today_rate': today_data['kpi']['rate'],
            'month_rate': month_data['kpi']['rate'],
            'sheet_info': today_data['sheet_info'],
            'teachers': [{
                'id': emp['id'],
                'roll': emp['roll'],
                'name': emp['name'],
                'present': emp['present'],
                'leave': emp['leave'] + emp['med_leave'],
                'rate': emp['rate'],
            } for emp in month_data['employees']],
        }

    def _get_own_employee(self):
        return self.env['hr.employee'].sudo().search(
            [('user_id', '=', self.env.uid)], limit=1)

    def _get_own_faculty(self, employee=None):
        employee = employee or self._get_own_employee()
        if not employee:
            return self.env['ala.education.faculty'].sudo().browse()
        return self.env['ala.education.faculty'].sudo().search(
            [('employee_id', '=', employee.id)], limit=1)

    def _faculty_self_block(self):
        """Minimal personal payload for group_education_faculty users.
        Deliberately tiny — a handful of indexed lookups — so the mobile
        app renders fast."""
        today = fields.Date.context_today(self)
        employee = self._get_own_employee()
        block = {
            'name': self.env.user.name,
            'my_attendance': {
                'available': False,
                'today_status': False,
                'today_label': 'Not Marked',
                'month_rate': 0.0,
            },
            'divisions': [],
        }

        # ---- own attendance status (faculty attendance module) ----
        if employee and 'ala.faculty.attendance.sheet.line' in self.env:
            Line = self.env['ala.faculty.attendance.sheet.line'].sudo()
            my = block['my_attendance']
            my['available'] = True
            line = Line.search([
                ('employee_id', '=', employee.id),
                ('date', '=', today),
            ], limit=1)
            if line:
                my['today_status'] = line.status
                my['today_label'] = dict(
                    line._fields['status'].selection).get(line.status)
            worked = total = 0
            for status, count in Line._read_group(
                    [('employee_id', '=', employee.id),
                     ('date', '>=', today.replace(day=1)),
                     ('date', '<=', today)],
                    ['status'], ['__count']):
                total += count
                if status in ('present', 'on_duty'):
                    worked += count
            my['month_rate'] = round(worked / total * 100, 1) if total else 0.0

        # ---- divisions where this faculty is in charge ----
        faculty = self._get_own_faculty(employee)
        if faculty:
            divisions = self.env['ala.education.class.division'].sudo().search([
                ('faculty_id', '=', faculty.id),
                ('current_year', '=', True),
            ])
            if divisions:
                self.env.cr.execute("""
                    SELECT d.id AS division_id, d.name AS division,
                           a.id AS attendance_id, a.state AS attendance_state,
                           COUNT(al.id) AS total,
                           COUNT(al.id) FILTER (
                               WHERE al.present = true) AS present,
                           COUNT(al.id) FILTER (
                               WHERE COALESCE(al.present, false)
                                     = false) AS absent
                    FROM ala_education_class_division d
                    LEFT JOIN ala_education_attendance a
                        ON a.division_id = d.id AND a.date = %s
                    LEFT JOIN ala_education_attendance_line al
                        ON al.attendance_id = a.id
                    WHERE d.id IN %s
                    GROUP BY d.id, d.name, a.id, a.state
                    ORDER BY d.name
                """, (today, tuple(divisions.ids)))
                for row in self.env.cr.dictfetchall():
                    if not row['attendance_id']:
                        status = 'not_created'
                    elif row['attendance_state'] == 'draft':
                        status = 'not_updated'
                    else:
                        status = 'updated'
                    block['divisions'].append({
                        'division_id': row['division_id'],
                        'division': row['division'],
                        'attendance_id': row['attendance_id'] or False,
                        'total': row['total'] or 0,
                        'present': row['present'] or 0,
                        'absent': row['absent'] or 0,
                        'status': status,
                    })
        return block

    # ==================================================================
    # MAIN DATA — auto-loaded on open, Principal / Office Admin ONLY
    # ==================================================================
    @api.model
    def erp_data(self):
        Announcement = self.env['ala.dashboard.announcement']
        if not self._is_dashboard_manager():
            return {
                'allowed': False,
                'faculty_self': self._faculty_self_block(),
                'announcements': Announcement.get_running_announcements(),
            }

        current_year_id = self._get_current_year_id()
        today = fields.Date.context_today(self)

        # ---------------- STUDENT COUNTS ----------------
        self.env.cr.execute("""
                SELECT
                    COUNT(*) FILTER (
                        WHERE COALESCE(tc_issued, false) = false
                        AND COALESCE(drop_out, false) = false
                    ) AS total_students,
                    COUNT(*) FILTER (
                        WHERE gender = 'male'
                        AND COALESCE(tc_issued, false) = false
                        AND COALESCE(drop_out, false) = false
                    ) AS male_students,
                    COUNT(*) FILTER (
                        WHERE gender = 'female'
                        AND COALESCE(tc_issued, false) = false
                        AND COALESCE(drop_out, false) = false
                    ) AS female_students
                FROM ala_education_student
            """)
        student_data = self.env.cr.dictfetchone() or {}

        # ---------------- FACULTY COUNTS ----------------
        self.env.cr.execute("""
                SELECT
                    COUNT(*) AS total_faculty,
                    COUNT(*) FILTER (WHERE gender = 'male') AS male_faculty,
                    COUNT(*) FILTER (WHERE gender = 'female') AS female_faculty
                FROM ala_education_faculty
            """)
        faculty_data = self.env.cr.dictfetchone() or {}

        # ---------------- EXAM COUNTS ----------------
        self.env.cr.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE state = 'ongoing') AS ongoing,
                    COUNT(*) FILTER (WHERE state = 'close') AS closed
                FROM ala_education_exam
                WHERE academic_year_id = %s
            """, (current_year_id,))
        exam_data = self.env.cr.dictfetchone() or {}

        # ---------------- TODAY STUDENT ATTENDANCE ----------------
        self.env.cr.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE present = true) AS present,
                    COUNT(*) FILTER (
                        WHERE COALESCE(present, false) = false
                    ) AS absent
                FROM ala_education_attendance_line
                WHERE date = %s AND state = 'done'
            """, (today,))
        attendance_data = self.env.cr.dictfetchone() or {}

        # ---------------- TODAY HOMEWORK ----------------
        self.env.cr.execute("""
                SELECT COUNT(*) AS total_homeworks
                FROM ala_student_homework_line
                WHERE homework_date = %s AND state = 'post'
            """, (today,))
        homework_data = self.env.cr.dictfetchone() or {}

        # ---------------- DIVISION SUMMARY ----------------
        self.env.cr.execute("""
            SELECT
                d.id AS division_id,
                d.name AS division,
                a.id AS attendance_id,
                a.state AS attendance_state,
                COUNT(al.id) FILTER (WHERE a.state = 'done') AS total,
                COUNT(al.id) FILTER (
                    WHERE a.state = 'done' AND al.present = true
                ) AS present,
                COUNT(al.id) FILTER (
                    WHERE a.state = 'done'
                    AND COALESCE(al.present, false) = false
                ) AS absent,
                COALESCE(hw.total_homeworks, 0) AS div_homeworks
            FROM ala_education_class_division d
            LEFT JOIN ala_education_attendance a
                ON a.division_id = d.id AND a.date = %s
            LEFT JOIN ala_education_attendance_line al
                ON al.attendance_id = a.id
            LEFT JOIN (
                SELECT class_div_id, COUNT(*) AS total_homeworks
                FROM ala_student_homework_line
                WHERE homework_date = %s AND state = 'post'
                GROUP BY class_div_id
            ) hw ON hw.class_div_id = d.id
            WHERE d.current_year = true
            GROUP BY d.id, d.name, a.id, a.state, hw.total_homeworks
            ORDER BY
                CASE
                    WHEN d.name ILIKE 'LKG%%' THEN 1
                    WHEN d.name ILIKE 'UKG%%' THEN 2
                    WHEN d.name ILIKE 'I-%%' THEN 3
                    WHEN d.name ILIKE 'II-%%' THEN 4
                    WHEN d.name ILIKE 'III-%%' THEN 5
                    WHEN d.name ILIKE 'IV-%%' THEN 6
                    WHEN d.name ILIKE 'V-%%' THEN 7
                    WHEN d.name ILIKE 'VI-%%' THEN 8
                    WHEN d.name ILIKE 'VII-%%' THEN 9
                    WHEN d.name ILIKE 'VIII-%%' THEN 10
                    WHEN d.name ILIKE 'IX-%%' THEN 11
                    WHEN d.name ILIKE 'X-%%' THEN 12
                    ELSE 99
                END,
                d.name
        """, (today, today))
        division_rows = self.env.cr.dictfetchall()

        division_summary = []
        updated_divisions = 0
        for row in division_rows:
            if not row['attendance_id']:
                status = 'not_created'
            elif row['attendance_state'] == 'draft':
                status = 'not_updated'
            else:
                status = 'updated'
                updated_divisions += 1
            division_summary.append({
                'division_id': row['division_id'],
                'division': row['division'],
                'attendance_id': row['attendance_id'] or False,
                'total': row['total'] or 0,
                'present': row['present'] or 0,
                'absent': row['absent'] or 0,
                'div_homeworks': row['div_homeworks'] or 0,
                'status': status,
            })

        return {
            'allowed': True,
            'current_academic_year_id': current_year_id,
            'cards': {
                'students': student_data.get('total_students') or 0,
                'student_male': student_data.get('male_students') or 0,
                'student_female': student_data.get('female_students') or 0,
                'faculties': faculty_data.get('total_faculty') or 0,
                'faculty_male': faculty_data.get('male_faculty') or 0,
                'faculty_female': faculty_data.get('female_faculty') or 0,
                'exam_ongoing': exam_data.get('ongoing') or 0,
                'exam_closed': exam_data.get('closed') or 0,
                'exams': (exam_data.get('ongoing') or 0)
                         + (exam_data.get('closed') or 0),
            },
            'attendance': {
                'total_students': student_data.get('total_students') or 0,
                'today_present': attendance_data.get('present') or 0,
                'today_absent': attendance_data.get('absent') or 0,
                'today_homeworks': homework_data.get('total_homeworks') or 0,
                'division_summary': division_summary,
                'total_divisions': len(division_summary),
                'updated_divisions': updated_divisions,
            },
            'faculty_attendance': self._faculty_attendance_block(),
            'announcements': Announcement.get_running_announcements(),
        }

    # ==================================================================
    # ON-DEMAND — Teacher Tasks (button, available to all internal users)
    # ==================================================================
    @api.model
    def erp_task_data(self):
        current_year_id = self._get_current_year_id()
        domain = [
            ('state', 'in', ('assigned', 'in_progress')),
            ('academic_year_id', '=', current_year_id),
        ]
        if not self._is_dashboard_manager():
            domain.append(('user_id', '=', self.env.uid))
        tasks = self.env['ala.task.management'].search(
            domain, order='scheduled_date desc', limit=80)
        return [{
            'id': task.id,
            'teacher_name': task.user_id.name or '',
            'task_name': task.name or '',
            'date': task.scheduled_date.strftime('%d-%b-%Y')
                    if task.scheduled_date else '',
            'state': dict(task._fields['state'].selection).get(task.state),
        } for task in tasks]

    # ==================================================================
    # ON-DEMAND — Exam Valuations (button, available to all internal users)
    # ==================================================================
    @api.model
    def erp_valuation_data(self):
        current_year_id = self._get_current_year_id()
        Valuation = self.env['ala.education.exam.valuation']
        domain = [
            ('state', '=', 'draft'),
            ('academic_year_id', '=', current_year_id),
        ]
        if not self._is_dashboard_manager():
            faculty = self._get_own_faculty()
            if 'faculty_id' in Valuation._fields and faculty:
                domain.append(('faculty_id', '=', faculty.id))
            elif 'user_id' in Valuation._fields:
                domain.append(('user_id', '=', self.env.uid))
            else:
                return []  # cannot scope safely -> show nothing
        valuations = Valuation.search(domain, order='id desc', limit=80)
        return [{
            'id': valuation.id,
            'valuation_name': valuation.name or '',
            'exam_name': valuation.exam_id.name or '',
            'subject_name': valuation.subject_id.name or '',
            'class_name': valuation.class_id.name or '',
            'division_name': valuation.division_id.name or '',
            'state': dict(valuation._fields['state'].selection).get(
                valuation.state),
        } for valuation in valuations]

    # ==================================================================
    # Faculty attendance entry — open (or create) today's sheet
    # ==================================================================
    @api.model
    def action_open_today_faculty_sheet(self):
        if not self._is_dashboard_manager():
            return False
        if 'ala.faculty.attendance.sheet' not in self.env:
            return False
        Sheet = self.env['ala.faculty.attendance.sheet']
        today = fields.Date.context_today(self)
        sheet = Sheet.search([
            ('date', '=', today),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not sheet:
            sheet = Sheet.create({'date': today})
            sheet._create_lines(raise_if_empty=False)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Faculty Attendance',
            'res_model': 'ala.faculty.attendance.sheet',
            'res_id': sheet.id,
            'views': [[False, 'form']],
            'target': 'current',
        }
