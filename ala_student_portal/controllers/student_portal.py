# -*- coding: utf-8 -*-
import base64
import json
import math
import re

from werkzeug import urls

from odoo import http, tools, _, SUPERUSER_ID
from odoo.exceptions import AccessDenied, AccessError, MissingError, UserError, ValidationError
from odoo.http import content_disposition, Controller, request, route
from odoo.tools import consteq
from odoo.addons.portal.controllers.portal import CustomerPortal
from datetime import date


class CustomerPortalCustom(CustomerPortal):
    """Controller for taking Home"""


    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        values = self._prepare_portal_layout_values()
        if request.env.user._is_internal():
            return request.render("ala_student_portal.teachsers_portal_my_home", values)
        else:
            today_date = date.today()
            cr = request.env.cr
            cr.execute("""
                SELECT COUNT(*)
                FROM ala_web_info
                WHERE enable = TRUE
                  AND date = %s
            """, (today_date,))
            today_announce_count = cr.fetchone()[0]
            print('DDDDDDDDDDDEEEEEEEEEEEEEEE',today_announce_count)
            partner = request.env.user.partner_id
            cr.execute("""
                        SELECT id 
                        FROM ala_education_student 
                        WHERE partner_id = %s 
                        LIMIT 1
                    """, (partner.id,))
            row = request.env.cr.fetchone()
            student_id = row[0] if row else False
            student = request.env['ala.education.student'].sudo().browse(student_id) if student_id else False

            today_date_str = today_date.strftime('%Y-%m-%d')

            # 1️⃣ Teacher Class Parent count
            request.env.cr.execute("""
                SELECT COUNT(*) 
                FROM ala_teacher_class_parent
                WHERE class_div_id = %s
                  AND state = 'done'
                  AND DATE(create_date) = %s
            """, (student.class_division_id.id, today_date_str))
            today_cl_comm_count = request.env.cr.fetchone()[0]

            # 2️⃣ Teacher Student Parent count
            request.env.cr.execute("""
                SELECT COUNT(*)
                FROM ala_teacher_student_parent
                WHERE student_id = %s
                  AND state = 'done'
                  AND DATE(create_date) = %s
            """, (student.id, today_date_str))
            today_stu_comm_count = request.env.cr.fetchone()[0]

            # 3️⃣ Student Homework count
            request.env.cr.execute("""
                SELECT COUNT(*)
                FROM ala_student_homework
                WHERE class_div_id = %s
                  AND homework_date = %s
            """, (student.class_division_id.id, today_date_str))
            today_home_work_count = request.env.cr.fetchone()[0]
            # 4️⃣ Attendance records
            # Attendance record for today (only one expected)
            request.env.cr.execute("""
                SELECT id
                FROM ala_education_attendance
                WHERE state = 'done'
                  AND date = %s
                  AND division_id = %s
                LIMIT 1
            """, (today_date_str, student.class_division_id.id))

            attendance_row = request.env.cr.fetchone()
            attendance_id = attendance_row[0] if attendance_row else False

            attendance_record = request.env['ala.education.attendance'].sudo().browse(attendance_id)

            attendance = 'N/A'
            if attendance_record:
                request.env.cr.execute("""
                    SELECT id
                    FROM ala_education_attendance_line
                    WHERE attendance_id = %s
                      AND register_no = %s
                    LIMIT 1
                """, (attendance_record.id, student.register_no))

                attendance_line_row = request.env.cr.fetchone()
                today_attendance = request.env['ala.education.attendance.line'].sudo().browse(
                                            attendance_line_row[0]) if attendance_line_row else False
                if today_attendance:
                    if today_attendance.present:
                        attendance = 'Present'
                    else:
                        attendance = 'Absent'

            request.env.cr.execute("""
                            SELECT id
                            FROM ala_school_event
                            WHERE event_date = %s
                            LIMIT 1
                        """, (today_date,))
            event_row = request.env.cr.fetchone()
            today_event = request.env['ala.school.event'].sudo().browse(event_row[0]) if event_row else False
            request.env.cr.execute("""
                            SELECT id
                            FROM ala_student_fees
                            WHERE student_id = %s
                        """, (student.id,))
            student_fees_ids = [row[0] for row in request.env.cr.fetchall()]
            student_fees = request.env['ala.student.fees'].browse(student_fees_ids)
            print('eeeeeed44444444444444444444',today_event)
            return request.render("ala_student_portal.student_portal_my_home", {
                                                                            'today_announce_count' : today_announce_count,
                                                                            'student' : student,
                                                                            'student_fees' : student_fees,
                                                                            'div_name' : student.class_division_id.name,
                                                                            'today_cl_comm_count' : today_cl_comm_count,
                                                                            'today_stu_comm_count' : today_stu_comm_count,
                                                                            'attendance' : attendance,
                                                                            'today_home_work_count' : today_home_work_count,
                                                                            'today_event' : today_event,
                                                                            })

    @route(['/school/student_info'], type='http', auth="user", website=True)
    def get_school_student_info(self, **kw):
        partner = request.env.user.partner_id
        request.env.cr.execute("""
                                SELECT id 
                                FROM ala_education_student 
                                WHERE partner_id = %s 
                                LIMIT 1
                            """, (partner.id,))
        row = request.env.cr.fetchone()
        student_id = row[0] if row else False
        student = request.env['ala.education.student'].sudo().browse(student_id) if student_id else False
        return request.render("ala_student_portal.student_info", {'student': student})

    @route(['/school/announcements'], type='http', auth="user", website=True)
    def get_school_announcements(self, **kw):
        display_notice = ''
        request.env.cr.execute("""
                SELECT id
                FROM ala_web_info
                WHERE enable = TRUE
            """)
        rows = request.env.cr.fetchall()
        notices = request.env['ala.web.info'].sudo().browse([row[0] for row in rows]) if rows else request.env['ala.web.info']
        raw_html = ""
        for notice in notices:
            date = notice.date.strftime('%d-%m-%Y')
            raw_html = raw_html + f""" <div style="text-align:center;">
                                <h4 style="color:#331a00;"><u>{date}</u></h2>
                                <span style="color: {notice.color};"><strong >{notice.anounce}</strong>.</span>
                            </div><br/><br/>
                            """
        # values = self._prepare_portal_layout_values()
        return request.render("ala_student_portal.student_school_announcements", {'notices': raw_html})


    @route(['/school/all_homeworks'], type='http', auth="user", website=True)
    def get_school_all_homeworks(self, **kw):
        today_date = date.today()
        partner = request.env.user.partner_id
        request.env.cr.execute("""
                    SELECT id
                    FROM ala_education_student
                    WHERE partner_id = %s
                    LIMIT 1
                """, (partner.id,))
        row = request.env.cr.fetchone()
        student_id = row[0] if row else False
        student = request.env['ala.education.student'].sudo().browse(student_id) if student_id else False

        request.env.cr.execute("""
                    SELECT id
                    FROM ala_student_homework
                    WHERE class_div_id = %s
                """, (student.class_division_id.id,))
        rows = request.env.cr.fetchall()
        home_work_ids = [r[0] for r in rows] if rows else []
        home_works = request.env['ala.student.homework'].sudo().browse(home_work_ids) if home_work_ids else request.env['ala.student.homework']
        today_home_work_id = home_works.filtered(lambda hw: hw.homework_date == today_date)
        print('ddddddddddddsssssssssss',today_home_work_id)
        print('ddddddddddddsssssssssss',today_home_work_id.work_line_ids)
        print('ddddddddddddsssssssssss',len(today_home_work_id.work_line_ids))
        return request.render("ala_student_portal.portal_all_homeworks", {'homeworks': home_works,
                                                                          'today_homework': today_home_work_id,
                                                                          })


    @route(['/homework/get_homework/<int:work_id>'],  type='http', auth="user", website=True)
    def get_school_get_homeworks(self, work_id=None, **kw):
        # homework_id = int(work_id)
        home_work_id = request.env['ala.student.homework'].sudo().browse(work_id)
        return request.render("ala_student_portal.portal_open_homeworks", {'home_work_id': home_work_id})

    @route(['/school/timetable'], type='http', auth="user", website=True)
    def get_school_class_timetable(self, **kw):
        today_date = date.today()
        partner = request.env.user.partner_id
        student_id = request.env['ala.education.student'].sudo().search([('partner_id', '=', partner.id)])
        timetable_id = request.env['ala.education.timetable'].sudo().search([('class_division_id', '=', student_id.class_division_id.id), ('state', '=', 'done'),
                                                                       ('academic_year_id.enable', '=', True)])
        return request.render("ala_student_portal.portal_student_timetable", {'timetable_id': timetable_id})


    @route(['/school/class_communation'], type='http', auth="user", website=True)
    def get_school_all_class_comm(self, **kw):
        today_date = date.today()
        partner = request.env.user.partner_id
        student_id = request.env['ala.education.student'].sudo().search([('partner_id', '=', partner.id)])
        class_comm_ids = request.env['ala.teacher.class.parent'].sudo().search(
                                        [('class_div_id', '=', student_id.class_division_id.id)])
        today_class_comm_ids = request.env['ala.teacher.class.parent'].sudo().search(
                    [('class_div_id', '=', student_id.class_division_id.id), ('create_date', '=', today_date)])
        return request.render("ala_student_portal.portal_all_class_comms", {'class_comms': class_comm_ids,
                                                                          'today_class_comms': today_class_comm_ids})

    @route(['/class_comm/get_comm/<int:comm_id>'], type='http', auth="user", website=True)
    def get_class_get_comms(self, comm_id=None, **kw):
        # homework_id = int(work_id)
        class_com_id = request.env['ala.teacher.class.parent'].sudo().browse(comm_id)
        return request.render("ala_student_portal.portal_open_communication", {'class_com_id': class_com_id})

    @http.route(['/student/add_comment_class_comm'], type='http', auth="user", methods=['POST'], website=True)
    def add_comment_calss(self, res_id, model, message, **kwargs):
        if res_id and model and message:
            record = request.env[model].sudo().browse(int(res_id))
            if record.exists():
                record.message_post(body=message, message_type='comment', subtype_xmlid="mail.mt_comment")
        return request.redirect('/class_comm/get_comm/%s' % res_id)

    @route(['/school/teacher_communation'], type='http', auth="user", website=True)
    def get_school_all_teacher_comm(self, **kw):
        today_date = date.today()
        partner = request.env.user.partner_id
        student_id = request.env['ala.education.student'].sudo().search([('partner_id', '=', partner.id)])
        teacher_comm_ids = request.env['ala.teacher.student.parent'].sudo().search(
            [('class_div_id', '=', student_id.class_division_id.id),('student_id', '=', student_id.id)])
        today_teacher_comm_ids = request.env['ala.teacher.student.parent'].sudo().search(
            [('class_div_id', '=', student_id.class_division_id.id), ('create_date', '=', today_date),('student_id', '=', student_id.id)])

        return request.render("ala_student_portal.portal_stu_teacher_class_comms", {'teacher_comm_ids': teacher_comm_ids,
                                                                            'today_teacher_comm_ids': today_teacher_comm_ids})

    @route(['/teacher_comm/get_comm/<int:comm_id>'], type='http', auth="user", website=True)
    def get_teacher_get_comms(self, comm_id=None, **kw):
        # homework_id = int(work_id)
        teacher_com_id = request.env['ala.teacher.student.parent'].sudo().browse(comm_id)
        return request.render("ala_student_portal.portal_open_teacher_communication", {'teacher_com_id': teacher_com_id})

    @http.route(['/teacher/add_comment_teacher_comm'], type='http', auth="user", methods=['POST'], website=True)
    def add_comment_teacher(self, res_id, model, message, **kwargs):
        if res_id and model and message:
            record = request.env[model].sudo().browse(int(res_id))
            if record.exists():
                record.message_post(body=message, message_type='comment', subtype_xmlid="mail.mt_comment")
        return request.redirect('/teacher_comm/get_comm/%s' % res_id)

    # Fees Template
    @route(['/my/fees'], type='http', auth="user", website=True)
    def get_school_student_fees(self, **kw):
        partner = request.env.user.partner_id
        total_fees = 0
        paid_fees = 0
        balance_fees = 0
        cr = request.env.cr
        cr.execute("""
                            SELECT id 
                            FROM ala_education_student 
                            WHERE partner_id = %s 
                            LIMIT 1
                        """, (partner.id,))
        row = request.env.cr.fetchone()
        student_id = row[0] if row else False
        student = request.env['ala.education.student'].sudo().browse(student_id) if student_id else False
        # Execute SQL to get all fee IDs for the student
        # Fetch single fee record ID for the student
        # Fetch single fee record ID for the student where academic year is enabled
        request.env.cr.execute("""
            SELECT sf.id
            FROM ala_student_fees sf
            JOIN ala_education_academic_year ay ON sf.academic_year_id = ay.id
            WHERE sf.student_id = %s
              AND ay.enable = TRUE
            LIMIT 1
        """, (student_id,))

        student_fee = False
        fee_row = request.env.cr.fetchone()
        student_fee = request.env['ala.student.fees'].sudo().browse(fee_row[0]) if fee_row else False
        if student_fee:
            total_fees = student_fee.amount_total
            paid_fees = student_fee.amount_paid
            balance_fees = student_fee.amount_unpaid
        return request.render("ala_student_portal.portal_monthly_payment_tiles", {'student': student_id,
                                                                                  'total_fees': total_fees,
                                                                                  'student_fees': student_fee,
                                                                                  'paid_fees': paid_fees,
                                                                                  'balance_fees': balance_fees,
                                                                                  })

    # # Fees Template
    # @route(['/my/result'], type='http', auth="user", website=True)
    # def get_school_student_result(self, **kw):
    #     partner = request.env.user.partner_id
    #     student_id = request.env['ala.education.student'].sudo().search([('partner_id', '=', partner.id)])
    #     fees_status = request.env['student.fees'].sudo().search([('student_id', '=', student_id.id)])
    #     over_due = False
    #     if fees_status.payment_status == 'over_due':
    #         over_due = 'over_due'
    #     return request.render("ala_student_portal.portal_student_result", {'student': student_id , 'over_due' : over_due})# Fees Template

    @route(['/my/result'], type='http', auth="user", website=True)
    def get_school_student_result(self, **kw):
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
        student = request.env['ala.education.student'].sudo().browse(student_id) if student_id else False
        over_due = False
        if student.hide_result:
            over_due = 'over_due'
        return request.render("ala_student_portal.portal_student_result", {'student': student , 'over_due' : over_due})