# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ErpDashboard(models.Model):
    """The Dashboard model used to build the all details of the
    Educational system"""
    _name = "ala.erp.dashboard"
    _description = "Education ERP Dashboard"

    @api.model
    def erp_data(self):
        """Critical data only — faculty, student, exam, amenity counts. Fastest possible path."""
        current_year = self.env['ala.education.academic.year'].search([
            ('enable', '=', True)
        ], limit=1)
        current_year_id = current_year.id or 0

        self.env.cr.execute("""
            WITH
            students AS (
                SELECT
                    COUNT(*) FILTER (WHERE COALESCE(tc_issued,false)=false AND COALESCE(drop_out,false)=false) AS total,
                    COUNT(*) FILTER (WHERE gender='male'   AND COALESCE(tc_issued,false)=false AND COALESCE(drop_out,false)=false) AS male,
                    COUNT(*) FILTER (WHERE gender='female' AND COALESCE(tc_issued,false)=false AND COALESCE(drop_out,false)=false) AS female
                FROM ala_education_student
            ),
            faculties AS (
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE gender='male')   AS male,
                    COUNT(*) FILTER (WHERE gender='female') AS female
                FROM ala_education_faculty
            ),
            amenities AS (
                SELECT
                    COUNT(*) FILTER (WHERE in_out_door='indoor')  AS indoor,
                    COUNT(*) FILTER (WHERE in_out_door='outdoor') AS outdoor
                FROM ala_education_amenities
            ),
            exams AS (
                SELECT
                    COUNT(*) FILTER (WHERE state='ongoing') AS ongoing,
                    COUNT(*) FILTER (WHERE state='close')   AS closed
                FROM ala_education_exam
                WHERE academic_year_id = %(year_id)s
            )
            SELECT
                s.total AS st, s.male AS sm, s.female AS sf,
                f.total AS ft, f.male AS fm, f.female AS ff,
                a.indoor AS ai, a.outdoor AS ao,
                e.ongoing AS eo, e.closed AS ec
            FROM students s, faculties f, amenities a, exams e
        """, {'year_id': current_year_id})

        row = self.env.cr.dictfetchone() or {}

        return {
            'students': row.get('st') or 0,
            'male_student_count': row.get('sm') or 0,
            'female_student_count': row.get('sf') or 0,
            'faculties': row.get('ft') or 0,
            'faculty_male': row.get('fm') or 0,
            'faculty_female': row.get('ff') or 0,
            'amenities': (row.get('ai') or 0) + (row.get('ao') or 0),
            'amenities_indoor': row.get('ai') or 0,
            'amenities_outdoor': row.get('ao') or 0,
            'exams': (row.get('eo') or 0) + (row.get('ec') or 0),
            'exam_ongoing': row.get('eo') or 0,
            'exam_closed': row.get('ec') or 0,
            'current_academic_year_id': current_year_id,
        }

    @api.model
    def erp_data_deferred(self):
        """Deferred data — attendance, divisions, tasks, valuations."""
        today = fields.Date.today()

        current_year = self.env['ala.education.academic.year'].search([
            ('enable', '=', True)
        ], limit=1)
        current_year_id = current_year.id or 0

        # Attendance summary + homework count + division breakdown — single query
        self.env.cr.execute("""
            WITH
            attendance_summary AS (
                SELECT
                    COUNT(*) FILTER (WHERE present = true)                  AS present,
                    COUNT(*) FILTER (WHERE COALESCE(present, false) = false) AS absent
                FROM ala_education_attendance_line
                WHERE date = %(today)s AND state = 'done'
            ),
            homework_summary AS (
                SELECT COUNT(*) AS total
                FROM ala_student_homework_line
                WHERE homework_date = %(today)s AND state = 'post'
            ),
            division_data AS (
                SELECT
                    d.id                AS division_id,
                    d.name              AS division,
                    a.id                AS attendance_id,
                    a.state             AS attendance_state,
                    COUNT(al.id) FILTER (WHERE a.state = 'done')                                     AS total,
                    COUNT(al.id) FILTER (WHERE a.state = 'done' AND al.present = true)               AS present,
                    COUNT(al.id) FILTER (WHERE a.state = 'done' AND COALESCE(al.present,false)=false) AS absent,
                    COALESCE(hw.total_homeworks, 0)                                                   AS div_homeworks
                FROM ala_education_class_division d
                LEFT JOIN ala_education_attendance a
                    ON a.division_id = d.id AND a.date = %(today)s
                LEFT JOIN ala_education_attendance_line al
                    ON al.attendance_id = a.id
                LEFT JOIN (
                    SELECT class_div_id, COUNT(*) AS total_homeworks
                    FROM ala_student_homework_line
                    WHERE homework_date = %(today)s AND state = 'post'
                    GROUP BY class_div_id
                ) hw ON hw.class_div_id = d.id
                WHERE d.current_year = true
                GROUP BY d.id, d.name, a.id, a.state, hw.total_homeworks
                ORDER BY d.name
            )
            SELECT
                att.present        AS att_present,
                att.absent         AS att_absent,
                hw.total           AS hw_total,
                dd.*
            FROM attendance_summary att, homework_summary hw,
                 division_data dd
        """, {'today': today})

        rows = self.env.cr.dictfetchall()

        # Pull attendance/homework from first row (same value on every row due to cross join)
        today_present = 0
        today_absent = 0
        today_homeworks = 0
        division_summary = []
        updated_divisions_count = 0

        for i, r in enumerate(rows):
            if i == 0:
                today_present = r.get('att_present') or 0
                today_absent = r.get('att_absent') or 0
                today_homeworks = r.get('hw_total') or 0

            if not r['attendance_id']:
                status = 'Not Created'
            elif r['attendance_state'] == 'draft':
                status = 'Not Updated'
            else:
                status = 'Updated'
                updated_divisions_count += 1

            division_summary.append({
                'id': r['attendance_id'],
                'division': r['division'],
                'division_id': r['division_id'],
                'attendance_id': r['attendance_id'] or False,
                'total': r['total'] or 0,
                'present': r['present'] or 0,
                'absent': r['absent'] or 0,
                'div_homeworks': r['div_homeworks'] or 0,
                'status': status,
            })

        # Tasks — prefetch related in one shot
        teacher_tasks = self.env['ala.task.management'].search([
            ('state', 'in', ('assigned', 'in_progress')),
            ('academic_year_id', '=', current_year_id),
        ], order='scheduled_date desc', limit=50)
        teacher_tasks.mapped('user_id')  # bulk prefetch

        task_summary = [{
            'id': t.id,
            'teacher_name': t.user_id.name,
            'task_name': t.name,
            'date': t.scheduled_date.strftime('%d-%b-%Y') if t.scheduled_date else '',
            'state': dict(t._fields['state'].selection).get(t.state),
        } for t in teacher_tasks]

        # Valuations — prefetch related in one shot
        exam_valuations = self.env['ala.education.exam.valuation'].search([
            ('state', '=', 'draft'),
            ('academic_year_id', '=', current_year_id),
        ], order='id desc', limit=50)
        exam_valuations.mapped('exam_id')
        exam_valuations.mapped('subject_id')
        exam_valuations.mapped('class_id')
        exam_valuations.mapped('division_id')

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
            'total_students': (rows[0].get('att_present') or 0) + (rows[0].get('att_absent') or 0) if rows else 0,
            'today_present': today_present,
            'today_absent': today_absent,
            'today_homeworks': today_homeworks,
            'division_summary': division_summary,
            'total_divisions': len(division_summary),
            'updated_divisions': updated_divisions_count,
            'teacher_tasks': task_summary,
            'valuation_summary': valuation_summary,
        }
