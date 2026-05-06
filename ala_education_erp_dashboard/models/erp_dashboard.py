# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ErpDashboard(models.Model):
    """The Dashboard model used to build the all details of the
    Educational system"""
    _name = "ala.erp.dashboard"
    _description = "Education ERP Dashboard"

    @api.model
    def erp_data(self):
        today = fields.Date.today()

        current_year = self.env['ala.education.academic.year'].search([
            ('enable', '=', True)
        ], limit=1)
        current_year_id = current_year.id or 0

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

        self.env.cr.execute("""
                SELECT
                    COUNT(*) AS total_faculty,
                    COUNT(*) FILTER (WHERE gender = 'male') AS male_faculty,
                    COUNT(*) FILTER (WHERE gender = 'female') AS female_faculty
                FROM ala_education_faculty
            """)
        faculty_data = self.env.cr.dictfetchone() or {}

        self.env.cr.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE in_out_door = 'indoor') AS indoor,
                    COUNT(*) FILTER (WHERE in_out_door = 'outdoor') AS outdoor
                FROM ala_education_amenities
            """)
        amenities_data = self.env.cr.dictfetchone() or {}

        self.env.cr.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE state = 'ongoing') AS ongoing,
                    COUNT(*) FILTER (WHERE state = 'close') AS closed
                FROM ala_education_exam
                WHERE academic_year_id = %s
            """, (current_year_id,))
        exam_data = self.env.cr.dictfetchone() or {}

        self.env.cr.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE present = true) AS present,
                    COUNT(*) FILTER (WHERE COALESCE(present, false) = false) AS absent
                FROM ala_education_attendance_line
                WHERE date = %s
                AND state = 'done'
            """, (today,))
        attendance_data = self.env.cr.dictfetchone() or {}

        self.env.cr.execute("""
                SELECT COUNT(*) AS total_homeworks
                FROM ala_student_homework_line
                WHERE homework_date = %s
                AND state = 'post'
            """, (today,))
        homework_data = self.env.cr.dictfetchone() or {}

        self.env.cr.execute("""
                SELECT
                    d.id AS division_id,
                    d.name AS division,
                    a.id AS attendance_id,
                    a.state AS attendance_state,

                    COUNT(al.id) FILTER (WHERE a.state = 'done') AS total,
                    COUNT(al.id) FILTER (
                        WHERE a.state = 'done'
                        AND al.present = true
                    ) AS present,
                    COUNT(al.id) FILTER (
                        WHERE a.state = 'done'
                        AND COALESCE(al.present, false) = false
                    ) AS absent,

                    COALESCE(hw.total_homeworks, 0) AS div_homeworks

                FROM ala_education_class_division d

                LEFT JOIN ala_education_attendance a
                    ON a.division_id = d.id
                    AND a.date = %s

                LEFT JOIN ala_education_attendance_line al
                    ON al.attendance_id = a.id

                LEFT JOIN (
                    SELECT class_div_id, COUNT(*) AS total_homeworks
                    FROM ala_student_homework_line
                    WHERE homework_date = %s
                    AND state = 'post'
                    GROUP BY class_div_id
                ) hw ON hw.class_div_id = d.id

                WHERE d.current_year = true

                GROUP BY
                    d.id, d.name, a.id, a.state, hw.total_homeworks

                ORDER BY d.name
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

        teacher_tasks = self.env['ala.task.management'].search([
            ('state', 'in', ('assigned', 'in_progress')),
            ('academic_year_id', '=', current_year_id)
        ], order='scheduled_date desc')

        task_summary = [{
            'id': t.id,
            'teacher_name': t.user_id.name,
            'task_name': t.name,
            'date': t.scheduled_date.strftime('%d-%b-%Y') if t.scheduled_date else '',
            'state': dict(t._fields['state'].selection).get(t.state),
        } for t in teacher_tasks]

        exam_valuations = self.env['ala.education.exam.valuation'].search([
            ('state', '=', 'draft'),
            ('academic_year_id', '=', current_year_id)
        ], order='id desc')

        valuation_summary = [{
            'id': v.id,
            'valuation_name': v.name,
            'exam_name': v.exam_id.name if v.exam_id else '',
            'subject_name': v.subject_id.name if v.subject_id else '',
            'class_name': v.class_id.name if v.class_id else '',
            'division_name': v.division_id.name if v.division_id else '',
            'state': dict(v._fields['state'].selection).get(v.state),
        } for v in exam_valuations]

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
            'today_present': attendance_data.get('present') or 0,
            'today_homeworks': homework_data.get('total_homeworks') or 0,
            'today_absent': attendance_data.get('absent') or 0,
            'division_summary': division_summary,
            'valuation_summary': valuation_summary,
            'teacher_tasks': task_summary,
            'total_divisions': len(division_summary),
            'updated_divisions': updated_divisions_count,
            'current_academic_year_id': current_year_id,
        }
    #
    # @api.model
    # def erp_data(self):
    #     """ Function to get the datas like number of application, number of
    #     students, number of faculties, number of amenities and number of
    #     exams """
    #     # applications = self.env['education.application'].search([])
    #     student_count = self.env['ala.education.student'].search_count(
    #         [('tc_issued', '=', False), ('drop_out', '=', False)])
    #     male_student_count = self.env['ala.education.student'].search_count([('gender', '=', 'male'),
    #                                                                      ('tc_issued', '=', False),
    #                                                                      ('drop_out', '=', False)])
    #     female_student_count = self.env['ala.education.student'].search_count([('gender', '=', 'female'),
    #                                                                        ('tc_issued', '=', False),
    #                                                                        ('drop_out', '=', False)])
    #     faculty_count = self.env['ala.education.faculty'].search_count([])
    #     fa_male_count = self.env['ala.education.faculty'].search_count([('gender', '=', 'male')])
    #     fa_female_count = self.env['ala.education.faculty'].search_count([('gender', '=', 'female')])
    #     amenities_indoor = self.env['ala.education.amenities'].search_count([('in_out_door', '=', 'indoor')])
    #     amenities_outdoor = self.env['ala.education.amenities'].search_count([('in_out_door', '=', 'outdoor')])
    #     current_year = self.env['ala.education.academic.year'].search([
    #         ('enable', '=', True)
    #     ], limit=1)
    #     on_exam_count = self.env['ala.education.exam'].search_count(
    #         [('state', '=', 'ongoing'), ('academic_year_id', '=', current_year.id)])
    #     cl_exam_count = self.env['ala.education.exam'].search_count(
    #         [('state', '=', 'close'), ('academic_year_id', '=', current_year.id)])
    #     today_attendances = self.env['ala.education.attendance.line'].search(
    #         [('date', '=', fields.Date.today()), ('state', '=', 'done')])
    #     today_homeworks = self.env['ala.student.homework.line'].sudo().search(
    #         [('homework_date', '=', fields.Date.today()), ('state', '=', 'post')])
    #     # total_students = len(students)
    #     presents_today = len(today_attendances.filtered(lambda a: a.present_morning))
    #     absents_today = len(today_attendances.filtered(lambda a: not a.present_morning))
    #     # Division-wise breakdown
    #     # Division-wise breakdown
    #     divisions = self.env['ala.education.class.division'].search([('current_year', '=', True)])
    #
    #     # Define order priority for class names
    #     class_order = {
    #         'LKG': 1, 'UKG': 2, 'I': 3, 'II': 4, 'III': 5, 'IV': 6,
    #         'V': 7, 'VI': 8, 'VII': 9, 'VIII': 10, 'IX': 11, 'X': 12,
    #     }
    #
    #     def sort_key(div):
    #         """Extract class and section parts for proper sorting."""
    #         name = (div.name or '').upper().strip()
    #         parts = name.split('-')
    #         main = parts[0] if parts else ''
    #         section = parts[1] if len(parts) > 1 else ''
    #         return (class_order.get(main, 999), section)
    #
    #     # Apply sorted order
    #     divisions = sorted(divisions, key=sort_key)
    #     division_summary = []
    #     today = fields.Date.today()
    #
    #     updated_divisions_count = 0  # ✅ count divisions with attendance updated
    #
    #     for div in divisions:
    #         # 🔍 Get today's attendance (ANY state)
    #         div_attendance = self.env['ala.education.attendance'].sudo().search([
    #             ('date', '=', today),
    #             ('division_id', '=', div.id),
    #         ], limit=1)
    #
    #         div_homeworks = len(today_homeworks.filtered(
    #             lambda work: work.class_div_id == div
    #         ))
    #
    #         # ❌ No attendance record created
    #         if not div_attendance:
    #             division_summary.append({
    #                 'division': div.name,
    #                 'division_id': div.id,
    #                 'attendance_id': False,
    #                 'total': 0,
    #                 'present': 0,
    #                 'absent': 0,
    #                 'div_homeworks': div_homeworks,
    #                 'status': 'Not Created',
    #             })
    #             continue
    #
    #         # 🟡 Attendance exists but in DRAFT
    #         if div_attendance.state == 'draft':
    #             division_summary.append({
    #                 'id': div_attendance.id,
    #                 'division': div.name,
    #                 'division_id': div.id,
    #                 'attendance_id': div_attendance.id,
    #                 'total': 0,
    #                 'present': 0,
    #                 'absent': 0,
    #                 'div_homeworks': div_homeworks,
    #                 'status': 'Not Updated',
    #             })
    #             continue
    #
    #         # ✅ Attendance DONE
    #         updated_divisions_count += 1
    #
    #         attendance_lines = div_attendance.attendance_line_ids
    #         total = len(attendance_lines)
    #         present = len(attendance_lines.filtered(lambda a: a.present_morning))
    #         absent = total - present
    #
    #         division_summary.append({
    #             'id': div_attendance.id,
    #             'division': div.name,
    #             'division_id': div.id,
    #             'attendance_id': div_attendance.id,
    #             'total': total,
    #             'present': present,
    #             'absent': absent,
    #             'div_homeworks': div_homeworks,
    #             'status': 'Updated',
    #         })
    #
    #     # ✅ Calculate counts
    #     total_divisions = len(divisions)
    #
    #     teacher_tasks = self.env['ala.task.management'].search(
    #         [('state', 'in', ('assigned', 'in_progress')), ('academic_year_id', '=', current_year.id)],
    #         order='scheduled_date desc'
    #     )
    #     task_summary = [{
    #         'id': t.id,  # 🔑 MUST HAVE
    #         'teacher_name': t.user_id.name,
    #         'task_name': t.name,
    #         'date': t.scheduled_date.strftime('%d-%b-%Y') if t.scheduled_date else '',
    #         'state': dict(t._fields['state'].selection).get(t.state),
    #     } for t in teacher_tasks]
    #
    #     exam_valuations = self.env['ala.education.exam.valuation'].search(
    #         [('state', '=', 'draft'), ('academic_year_id', '=', current_year.id)],
    #         order='id desc'
    #     )
    #
    #     valuation_summary = [{
    #         'id': v.id,  # 🔑 MUST HAVE (for redirect / click)
    #         'valuation_name': v.name,
    #         'exam_name': v.exam_id.name if v.exam_id else '',
    #         'subject_name': v.subject_id.name if v.subject_id else '',
    #         'class_name': v.class_id.name if v.class_id else '',
    #         'division_name': v.division_id.name if v.division_id else '',
    #         'state': dict(v._fields['state'].selection).get(v.state),
    #     } for v in exam_valuations]
    #
    #     return {
    #         'students': student_count,
    #         'female_student_count': female_student_count,
    #         'male_student_count': male_student_count,
    #         'faculties': faculty_count,
    #         'faculty_male': fa_male_count,
    #         'faculty_female': fa_female_count,
    #         'amenities': amenities_indoor + amenities_outdoor,
    #         'amenities_indoor': amenities_indoor,
    #         'amenities_outdoor': amenities_outdoor,
    #         'exams': on_exam_count + cl_exam_count,
    #         'exam_ongoing': on_exam_count,
    #         'exam_closed': cl_exam_count,
    #         'total_students': student_count,
    #         'today_present': presents_today,
    #         'today_homeworks': len(today_homeworks),
    #         'today_absent': absents_today,
    #         'division_summary': division_summary,
    #         'valuation_summary': valuation_summary,
    #         'teacher_tasks': task_summary,
    #         'total_divisions': total_divisions,  # ✅ total divisions count
    #         'updated_divisions': updated_divisions_count,  # ✅ updated divisions count
    #         'current_academic_year_id': current_year,  # ✅ updated divisions count
    #     }


    @api.model
    def get_all_applications(self):
        """ Function to get count of applications in each academic year """
        years = self.env['ala.education.application'].search([]).mapped(
            'academic_year_id')
        application_count_dict = {
            year.name: self.env['ala.education.application'].search_count(
                [('academic_year_id', '=', year.name)]) for year in years}
        return application_count_dict

    @api.model
    def get_rejected_accepted_applications(self):
        """ Function to get count of all accepted and rejected applications """
        application_dict = {}
        ay_date = 0
        ay_year = ''
        academic_year = self.env['ala.education.academic.year'].search([])
        for years in academic_year:
            ay_date = years.ay_end_date
            ay_year = years.name
        for year in academic_year:
            if ay_date < year.ay_end_date:
                ay_date = year.ay_end_date
                ay_year = year.name
        rejected_applications = self.env['ala.education.application'].search_count(
            [('state', '=', 'reject'), ('academic_year_id', '=', ay_year)])
        accepted_applications = self.env['ala.education.application'].search_count(
            [('state', '=', 'done'), ('academic_year_id', '=', ay_year)])
        application_dict.update(
            {'Done': accepted_applications, 'Reject': rejected_applications})
        return application_dict

    @api.model
    def get_exam_result(self):
        """ Function to get total exam result """
        exam_result_dict = {}
        pass_count = self.env['ala.results.subject.line'].search_count(
            [('pass_or_fail', '=', True)])
        fail_count = self.env['ala.results.subject.line'].search_count(
            [('pass_or_fail', '=', False)])
        exam_result_dict.update({'Pass': pass_count, 'Fail': fail_count})
        return exam_result_dict

    @api.model
    def get_attendance(self):
        """ Function to get total attendance """
        attendance_dict = {}
        absents = self.env['ala.education.attendance.line'].search_count(
            [('date', '=', fields.Date.today()), ('full_day_absent', '=', 1)])
        total = self.env['ala.education.student'].search_count([])
        presents = total - absents
        attendance_dict.update({'Presents': presents, 'Absents': absents})
        return attendance_dict

    @api.model
    def get_student_strength(self):
        """ Function to get class wise student strength """
        classes = self.env['ala.education.class.division'].search([])
        class_wise_dict = {
            clas.name: self.env['ala.education.student'].search_count(
                [('class_division_id', '=', clas.id)]) for clas in classes}
        return class_wise_dict

    @api.model
    def get_average_marks(self):
        """ Function to get class wise average marks """
        class_average_mark_dict = {}
        classes = self.env['ala.education.class.division'].search([])
        for clas in classes:
            all_students = self.env['ala.education.student'].search(
                [('class_division_id', '=', clas.id)])
            if all_students:
                class_mark_list = [sum(
                    self.env['ala.education.exam.results'].search(
                        [('student_id', '=', student.id)]).mapped(
                        'total_mark_scored')) for student in all_students]
                count = len(class_mark_list)
                total_marks = sum(class_mark_list)
                average_mark = total_marks / count
                class_average_mark_dict.update({clas.name: average_mark})
        return class_average_mark_dict

    @api.model
    def get_academic_year(self):
        """ Function to get the academic year """
        academic_dict = {year.id: year.name for year in
                         self.env['ala.education.academic.year'].search([])}
        return academic_dict

    @api.model
    def get_academic_year_exam_result(self, *args):
        """ Function to get exam results in each academic year """
        academic_exam_result_dict = {}
        academic_pass_count = self.env['ala.results.subject.line'].search_count(
            [('academic_year_id.id', '=', *args), ('pass_or_fail', '=', True)])
        academic_fail_count = self.env['ala.results.subject.line'].search_count(
            [('academic_year_id.id', '=', *args), ('pass_or_fail', '=', False)])
        academic_exam_result_dict.update(
            {'Pass': academic_pass_count, 'Fail': academic_fail_count})
        return academic_exam_result_dict

    @api.model
    def get_classes(self):
        """ Function to get the classes """
        class_dict = {clas.id: clas.name for clas in
                      self.env['ala.education.class.division'].search([])}
        return class_dict

    @api.model
    def get_class_attendance_today(self, *args):
        """ Function to get class wise attendance """
        class_attendance_dict = {}
        class_absents = self.env['ala.education.attendance.line'].search_count(
            [('division_id.id', '=', *args),
             ('date', '=', fields.Date.today()),
             ('full_day_absent', '=', 1)])
        class_total = self.env['ala.education.student'].search_count(
            [('class_division_id.id', '=', *args)])
        class_presents = class_total - class_absents
        class_attendance_dict.update(
            {'Presents': class_presents, 'Absents': class_absents})
        return class_attendance_dict
