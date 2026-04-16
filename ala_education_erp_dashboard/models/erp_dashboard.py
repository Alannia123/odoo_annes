# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ErpDashboard(models.Model):
    """The Dashboard model used to build the all details of the
    Educational system"""
    _name = "ala.erp.dashboard"
    _description = "Education ERP Dashboard"

    @api.model
    def erp_data(self):
        """ Function to get the datas like number of application, number of
        students, number of faculties, number of amenities and number of
        exams """
        # applications = self.env['ala.education.application'].search([])
        student_count = self.env['ala.education.student'].search_count([('tc_issued', '=', False), ('drop_out', '=', False)])
        male_student_count = self.env['ala.education.student'].search_count([('gender', '=', 'male'),
                                                                    ('tc_issued', '=', False),  ('drop_out', '=', False)])
        female_student_count = self.env['ala.education.student'].search_count([('gender', '=', 'female'),
                                                                    ('tc_issued', '=', False),  ('drop_out', '=', False)])
        faculty_count = self.env['ala.education.faculty'].search_count([])
        fa_male_count = self.env['ala.education.faculty'].search_count([('gender', '=', 'male')])
        fa_female_count = self.env['ala.education.faculty'].search_count([('gender', '=', 'female')])
        amenities_indoor = self.env['ala.education.amenities'].search_count([('in_out_door', '=', 'indoor')])
        amenities_outdoor = self.env['ala.education.amenities'].search_count([('in_out_door', '=', 'outdoor')])
        on_exam_count = self.env['ala.education.exam'].search_count([('state', '=', 'ongoing')])
        cl_exam_count = self.env['ala.education.exam'].search_count([('state', '=', 'close')])
        today_attendances = self.env['ala.education.attendance.line'].search([('date', '=', fields.Date.today()), ('state', '=', 'done')])
        today_homeworks = self.env['ala.student.homework.line'].sudo().search([('homework_date', '=', fields.Date.today()), ('state', '=', 'post')])
        # total_students = len(students)
        presents_today = len(today_attendances.filtered(lambda a: a.present))
        absents_today = len(today_attendances.filtered(lambda a: not a.present))
        # Division-wise breakdown
        # Division-wise breakdown
        divisions = self.env['ala.education.class.division'].search([])

        # Define order priority for class names
        class_order = {
            'LKG': 1, 'UKG': 2, 'I': 3, 'II': 4, 'III': 5, 'IV': 6,
            'V': 7, 'VI': 8, 'VII': 9, 'VIII': 10, 'IX': 11, 'X': 12,
        }

        def sort_key(div):
            """Extract class and section parts for proper sorting."""
            name = (div.name or '').upper().strip()
            parts = name.split('-')
            main = parts[0] if parts else ''
            section = parts[1] if len(parts) > 1 else ''
            return (class_order.get(main, 999), section)

        # Apply sorted order
        divisions = sorted(divisions, key=sort_key)
        division_summary = []
        today = fields.Date.today()

        updated_divisions_count = 0  # ✅ count divisions with attendance updated

        for div in divisions:
            # 🔍 Get today's attendance (ANY state)
            div_attendance = self.env['ala.education.attendance'].sudo().search([
                ('date', '=', today),
                ('division_id', '=', div.id),
            ], limit=1)

            div_homeworks = len(today_homeworks.filtered(
                lambda work: work.class_div_id == div
            ))

            # ❌ No attendance record created
            if not div_attendance:
                division_summary.append({
                    'division': div.name,
                    'division_id': div.id,
                    'attendance_id': False,
                    'total': 0,
                    'present': 0,
                    'absent': 0,
                    'div_homeworks': div_homeworks,
                    'status': 'Not Created',
                })
                continue

            # 🟡 Attendance exists but in DRAFT
            if div_attendance.state == 'draft':
                division_summary.append({
                    'id': div_attendance.id,
                    'division': div.name,
                    'division_id': div.id,
                    'attendance_id': div_attendance.id,
                    'total': 0,
                    'present': 0,
                    'absent': 0,
                    'div_homeworks': div_homeworks,
                    'status': 'Not Updated',
                })
                continue

            # ✅ Attendance DONE
            updated_divisions_count += 1

            attendance_lines = div_attendance.attendance_line_ids
            total = len(attendance_lines)
            present = len(attendance_lines.filtered(lambda a: a.present))
            absent = total - present

            division_summary.append({
                'id': div_attendance.id,
                'division': div.name,
                'division_id': div.id,
                'attendance_id': div_attendance.id,
                'total': total,
                'present': present,
                'absent': absent,
                'div_homeworks': div_homeworks,
                'status': 'Updated',
            })

        # ✅ Calculate counts
        total_divisions = len(divisions)

        teacher_tasks = self.env['ala.task.management'].search(
            [('state', 'in', ('assigned', 'in_progress'))],
            order='scheduled_date desc'
        )
        task_summary = [{
            'id': t.id,  # 🔑 MUST HAVE
            'teacher_name': t.user_id.name,
            'task_name': t.name,
            'date': t.scheduled_date.strftime('%d-%b-%Y') if t.scheduled_date else '',
            'state': dict(t._fields['state'].selection).get(t.state),
        } for t in teacher_tasks]

        exam_valuations = self.env['ala.education.exam.valuation'].search(
            [('state', '=', 'draft')],
            order='id desc'
        )

        valuation_summary = [{
            'id': v.id,  # 🔑 MUST HAVE (for redirect / click)
            'valuation_name': v.name,
            'exam_name': v.exam_id.name if v.exam_id else '',
            'subject_name': v.subject_id.name if v.subject_id else '',
            'class_name': v.class_id.name if v.class_id else '',
            'division_name': v.division_id.name if v.division_id else '',
            'state': dict(v._fields['state'].selection).get(v.state),
        } for v in exam_valuations]

        return {
            'students': student_count,
            'female_student_count': female_student_count,
            'male_student_count': male_student_count,
            'faculties': faculty_count,
            'faculty_male': fa_male_count,
            'faculty_female': fa_female_count,
            'amenities': amenities_indoor + amenities_outdoor,
            'amenities_indoor': amenities_indoor,
            'amenities_outdoor': amenities_outdoor,
            'exams': on_exam_count + cl_exam_count,
            'exam_ongoing': on_exam_count,
            'exam_closed': cl_exam_count,
            'total_students': student_count,
            'today_present': presents_today,
            'today_homeworks': len(today_homeworks),
            'today_absent': absents_today,
            'division_summary': division_summary,
            'valuation_summary': valuation_summary,
            'teacher_tasks': task_summary,
            'total_divisions': total_divisions,  # ✅ total divisions count
            'updated_divisions': updated_divisions_count,  # ✅ updated divisions count
        }

    # @api.model
    # def erp_data(self):
    #     """Optimized version: single-pass grouped counts and reduced ORM calls."""
    #
    #     cr = self.env.cr  # direct cursor for grouped queries
    #
    #     # --- STUDENTS ---
    #     cr.execute("""
    #             SELECT gender, COUNT(*)
    #             FROM education_student
    #             GROUP BY gender
    #         """)
    #     gender_counts = dict(cr.fetchall())
    #     student_count = sum(gender_counts.values())
    #     male_student_count = gender_counts.get('male', 0)
    #     female_student_count = gender_counts.get('female', 0)
    #
    #     # --- FACULTIES ---
    #     cr.execute("""
    #             SELECT gender, COUNT(*)
    #             FROM education_faculty
    #             GROUP BY gender
    #         """)
    #     fac_counts = dict(cr.fetchall())
    #     faculty_count = sum(fac_counts.values())
    #     fa_male_count = fac_counts.get('male', 0)
    #     fa_female_count = fac_counts.get('female', 0)
    #
    #     # --- AMENITIES ---
    #     cr.execute("""
    #             SELECT in_out_door, COUNT(*)
    #             FROM education_amenities
    #             GROUP BY in_out_door
    #         """)
    #     amenities_counts = dict(cr.fetchall())
    #     amenities_indoor = amenities_counts.get('indoor', 0)
    #     amenities_outdoor = amenities_counts.get('outdoor', 0)
    #
    #     # --- EXAMS ---
    #     cr.execute("""
    #             SELECT state, COUNT(*)
    #             FROM education_exam
    #             GROUP BY state
    #         """)
    #     exam_counts = dict(cr.fetchall())
    #     on_exam_count = exam_counts.get('ongoing', 0)
    #     cl_exam_count = exam_counts.get('close', 0)
    #
    #     # --- ATTENDANCE & HOMEWORK (for today) ---
    #     today = fields.Date.today()
    #
    #     # Attendance lines (use grouped SQL)
    #     cr.execute("""
    #             SELECT present, COUNT(*)
    #             FROM education_attendance_line
    #             WHERE date = %s AND state = 'done'
    #             GROUP BY present
    #         """, (today,))
    #     att_summary = dict(cr.fetchall())
    #     presents_today = att_summary.get(True, 0)
    #     absents_today = att_summary.get(False, 0)
    #
    #     # Homework lines
    #     cr.execute("""
    #             SELECT COUNT(*)
    #             FROM student_homework_line
    #             WHERE homework_date = %s AND state = 'post'
    #         """, (today,))
    #     today_homeworks = cr.fetchone()[0]
    #
    #     # --- DIVISION SUMMARY (batched) ---
    #     divisions = self.env['ala.education.class.division'].sudo().search([])
    #     class_order = {
    #         'LKG': 1, 'UKG': 2, 'I': 3, 'II': 4, 'III': 5, 'IV': 6,
    #         'V': 7, 'VI': 8, 'VII': 9, 'VIII': 10, 'IX': 11, 'X': 12,
    #     }
    #
    #     def sort_key(div):
    #         name = (div.name or '').upper().strip()
    #         parts = name.split('-')
    #         main = parts[0] if parts else ''
    #         section = parts[1] if len(parts) > 1 else ''
    #         return (class_order.get(main, 999), section)
    #
    #     divisions = sorted(divisions, key=sort_key)
    #     division_ids = [d.id for d in divisions]
    #
    #     # Fetch attendance & homework lines for all divisions in one go
    #     self.env.cr.execute("""
    #             SELECT division_id, COUNT(*)
    #             FROM education_attendance
    #             WHERE date = %s AND state = 'done' AND division_id IS NOT NULL
    #             GROUP BY division_id
    #         """, (today,))
    #     attendance_map = dict(self.env.cr.fetchall())
    #
    #     self.env.cr.execute("""
    #             SELECT class_div_id, COUNT(*)
    #             FROM student_homework_line
    #             WHERE homework_date = %s AND state = 'post' AND class_div_id IS NOT NULL
    #             GROUP BY class_div_id
    #         """, (today,))
    #     homework_map = dict(self.env.cr.fetchall())
    #
    #     division_summary = []
    #     updated_divisions_count = 0
    #     for div in divisions:
    #         if div.id in attendance_map:
    #             updated_divisions_count += 1
    #             div_homeworks = homework_map.get(div.id, 0)
    #             division_summary.append({
    #                 'division': div.name,
    #                 'total': attendance_map[div.id],  # optional: replace with total lines if needed
    #                 'present': 0,  # skipped for speed, can expand with join later
    #                 'absent': 0,
    #                 'div_homeworks': div_homeworks,
    #                 'status': 'Updated',
    #             })
    #         else:
    #             division_summary.append({
    #                 'division': div.name,
    #                 'total': 0,
    #                 'present': 0,
    #                 'absent': 0,
    #                 'div_homeworks': homework_map.get(div.id, 0),
    #                 'status': 'Not Updated',
    #             })
    #
    #     total_divisions = len(divisions)
    #
    #     # --- TEACHER TASKS ---
    #     teacher_tasks = self.env['ala.task.management'].sudo().search(
    #         [('state', 'in', ('assigned', 'in_progress'))],
    #         order='scheduled_date desc', limit=10
    #     )
    #     task_summary = [{
    #         'teacher_name': t.user_id.name,
    #         'task_name': t.name,
    #         'date': t.scheduled_date.strftime('%d-%b-%Y') if t.scheduled_date else '',
    #         'state': dict(t._fields['state'].selection).get(t.state),
    #     } for t in teacher_tasks]
    #
    #     # --- FINAL RESULT ---
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
    #         'today_present': presents_today,
    #         'today_absent': absents_today,
    #         'today_homeworks': today_homeworks,
    #         'division_summary': division_summary,
    #         'teacher_tasks': task_summary,
    #         'total_divisions': total_divisions,
    #         'updated_divisions': updated_divisions_count,
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
