# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ErpDashboard(models.Model):
    """The Dashboard model used to build the all details of the
    Educational system"""
    _name = "erp.dashboard"
    _description = "Education ERP Dashboard"

    def _get_current_year_id(self):
        current_year = self.env['education.academic.year'].search([
            ('enable', '=', True)
        ], limit=1)
        return current_year.id or 0

    # ============================================================
    # LIGHT DATA — loaded on page open (top summary cards only)
    # ============================================================
    @api.model
    def erp_data(self):
        current_year_id = self._get_current_year_id()

        # ----------------------------
        # STUDENT COUNTS
        # ----------------------------
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
                FROM education_student
            """)
        student_data = self.env.cr.dictfetchone() or {}

        # ----------------------------
        # FACULTY COUNTS
        # ----------------------------
        self.env.cr.execute("""
                SELECT
                    COUNT(*) AS total_faculty,
                    COUNT(*) FILTER (WHERE gender = 'male') AS male_faculty,
                    COUNT(*) FILTER (WHERE gender = 'female') AS female_faculty
                FROM education_faculty
            """)
        faculty_data = self.env.cr.dictfetchone() or {}

        # ----------------------------
        # AMENITIES COUNTS
        # ----------------------------
        self.env.cr.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE in_out_door = 'indoor') AS indoor,
                    COUNT(*) FILTER (WHERE in_out_door = 'outdoor') AS outdoor
                FROM education_amenities
            """)
        amenities_data = self.env.cr.dictfetchone() or {}

        # ----------------------------
        # EXAM COUNTS
        # ----------------------------
        self.env.cr.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE state = 'ongoing') AS ongoing,
                    COUNT(*) FILTER (WHERE state = 'close') AS closed
                FROM education_exam
                WHERE academic_year_id = %s
            """, (current_year_id,))
        exam_data = self.env.cr.dictfetchone() or {}

        total_students = student_data.get('total_students') or 0
        male_students = student_data.get('male_students') or 0
        female_students = student_data.get('female_students') or 0

        total_faculty = faculty_data.get('total_faculty') or 0
        male_faculty = faculty_data.get('male_faculty') or 0
        female_faculty = faculty_data.get('female_faculty') or 0

        amenities_indoor = amenities_data.get('indoor') or 0
        amenities_outdoor = amenities_data.get('outdoor') or 0

        exam_ongoing = exam_data.get('ongoing') or 0
        exam_closed = exam_data.get('closed') or 0

        return {
            'students': total_students,
            'female_student_count': female_students,
            'male_student_count': male_students,

            'faculties': total_faculty,
            'faculty_male': male_faculty,
            'faculty_female': female_faculty,

            'amenities': amenities_indoor + amenities_outdoor,
            'amenities_indoor': amenities_indoor,
            'amenities_outdoor': amenities_outdoor,

            'exams': exam_ongoing + exam_closed,
            'exam_ongoing': exam_ongoing,
            'exam_closed': exam_closed,

            'total_students': total_students,
            'current_academic_year_id': current_year_id,
        }

    # ============================================================
    # HEAVY DATA — loaded on demand via "Load Data" button
    # ============================================================
    @api.model
    def erp_detail_data(self):
        today = fields.Date.today()
        current_year_id = self._get_current_year_id()

        # ----------------------------
        # TODAY ATTENDANCE TOTAL
        # ----------------------------
        self.env.cr.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE present_morning = true) AS present,
                    COUNT(*) FILTER (WHERE COALESCE(present_morning, false) = false) AS absent
                FROM education_attendance_line
                WHERE date = %s
                AND state = 'done'
            """, (today,))
        attendance_data = self.env.cr.dictfetchone() or {}

        # ----------------------------
        # TODAY HOMEWORK TOTAL
        # ----------------------------
        self.env.cr.execute("""
                SELECT COUNT(*) AS total_homeworks
                FROM student_homework_line
                WHERE homework_date = %s
                AND state = 'post'
            """, (today,))
        homework_data = self.env.cr.dictfetchone() or {}

        # ----------------------------
        # DIVISION SUMMARY
        # ----------------------------
        self.env.cr.execute("""
            SELECT
                d.id AS division_id,
                d.name AS division,
                a.id AS attendance_id,
                a.state AS attendance_state,

                COUNT(al.id) FILTER (WHERE a.state = 'done') AS total,

                COUNT(al.id) FILTER (
                    WHERE a.state = 'done'
                    AND al.present_morning = true
                ) AS present,

                COUNT(al.id) FILTER (
                    WHERE a.state = 'done'
                    AND COALESCE(al.present_morning, false) = false
                ) AS absent,

                COALESCE(hw.total_homeworks, 0) AS div_homeworks

            FROM education_class_division d

            LEFT JOIN education_attendance a
                ON a.division_id = d.id
                AND a.date = %s

            LEFT JOIN education_attendance_line al
                ON al.attendance_id = a.id

            LEFT JOIN (
                SELECT class_div_id, COUNT(*) AS total_homeworks
                FROM student_homework_line
                WHERE homework_date = %s
                AND state = 'post'
                GROUP BY class_div_id
            ) hw ON hw.class_div_id = d.id

            WHERE d.current_year = true

            GROUP BY
                d.id, d.name, a.id, a.state, hw.total_homeworks

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
        updated_divisions_count = 0

        for row in division_rows:
            if not row['attendance_id']:
                status = 'Not Created'
            elif row['attendance_state'] == 'draft':
                status = 'Not Updated'
            else:
                status = 'Updated'
                updated_divisions_count += 1

            division_summary.append({
                'id': row['attendance_id'],
                'division': row['division'],
                'division_id': row['division_id'],
                'attendance_id': row['attendance_id'] or False,
                'total': row['total'] or 0,
                'present': row['present'] or 0,
                'absent': row['absent'] or 0,
                'div_homeworks': row['div_homeworks'] or 0,
                'status': status,
            })

        # ----------------------------
        # TEACHER TASKS
        # ----------------------------
        teacher_tasks = self.env['task.management'].search(
            [
                ('state', 'in', ('assigned', 'in_progress')),
                ('academic_year_id', '=', current_year_id)
            ],
            order='scheduled_date desc'
        )

        task_summary = [{
            'id': t.id,
            'teacher_name': t.user_id.name,
            'task_name': t.name,
            'date': t.scheduled_date.strftime('%d-%b-%Y') if t.scheduled_date else '',
            'state': dict(t._fields['state'].selection).get(t.state),
        } for t in teacher_tasks]

        # ----------------------------
        # EXAM VALUATIONS
        # ----------------------------
        exam_valuations = self.env['education.exam.valuation'].search(
            [
                ('state', '=', 'draft'),
                ('academic_year_id', '=', current_year_id)
            ],
            order='id desc'
        )

        valuation_summary = [{
            'id': v.id,
            'valuation_name': v.name,
            'exam_name': v.exam_id.name if v.exam_id else '',
            'subject_name': v.subject_id.name if v.subject_id else '',
            'class_name': v.class_id.name if v.class_id else '',
            'division_name': v.division_id.name if v.division_id else '',
            'state': dict(v._fields['state'].selection).get(v.state),
        } for v in exam_valuations]

        return {
            'today_present': attendance_data.get('present') or 0,
            'today_absent': attendance_data.get('absent') or 0,
            'today_homeworks': homework_data.get('total_homeworks') or 0,

            'division_summary': division_summary,
            'valuation_summary': valuation_summary,
            'teacher_tasks': task_summary,

            'total_divisions': len(division_summary),
            'updated_divisions': updated_divisions_count,
        }