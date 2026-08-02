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
import calendar
import logging
from odoo import fields

_logger = logging.getLogger(__name__)

# 2 * pi * r for the donut radius used in the home template (r = 54)
DONUT_CIRCUMFERENCE = 339.292


class CustomerPortalCustom(CustomerPortal):
    """Controller for taking Home"""

    # ------------------------------------------------------------------
    # Dashboard helpers
    # ------------------------------------------------------------------
    def _ala_student_from_partner(self):
        """Resolve the student linked to the logged-in portal user."""
        cr = request.env.cr
        cr.execute("""
            SELECT id FROM ala_education_student
            WHERE partner_id = %s LIMIT 1
        """, (request.env.user.partner_id.id,))
        row = cr.fetchone()
        if not row:
            return request.env['ala.education.student']
        return request.env['ala.education.student'].sudo().browse(row[0])

    def _ala_greeting(self):
        """Time-of-day greeting in the user's own timezone, not UTC."""
        local_dt = fields.Datetime.context_timestamp(
            request.env.user, fields.Datetime.now())
        hour = local_dt.hour
        if hour < 12:
            return 'Good morning'
        if hour < 17:
            return 'Good afternoon'
        return 'Good evening'

    def _ala_attendance_month(self, student):
        """Present / absent / holiday counts + calendar matrix for this month."""
        cr = request.env.cr
        today = date.today()
        first_weekday, total_days = calendar.monthrange(today.year, today.month)
        calendar.setfirstweekday(calendar.SUNDAY)
        weeks = calendar.monthcalendar(today.year, today.month)

        start_date = date(today.year, today.month, 1)
        end_date = date(today.year, today.month, total_days)

        status_by_day = {}
        present = absent = 0

        if student:
            cr.execute("""
                SELECT date, present
                FROM ala_education_attendance_line
                WHERE state = 'done'
                  AND student_id = %s
                  AND date BETWEEN %s AND %s
            """, (student.id, start_date, end_date))
            for rec_date, is_present in cr.fetchall():
                if is_present:
                    status_by_day[rec_date.day] = 'present'
                    present += 1
                else:
                    status_by_day[rec_date.day] = 'absent'
                    absent += 1

        cr.execute("""
            SELECT event_date FROM ala_school_event
            WHERE is_holiday = TRUE AND event_date BETWEEN %s AND %s
        """, (start_date, end_date))
        holidays = cr.fetchall()
        for (event_date,) in holidays:
            status_by_day[event_date.day] = 'holiday'

        return {
            'att_month_label': '%s %s' % (
                calendar.month_name[today.month], today.year),
            'att_weeks': weeks,
            'att_status_by_day': status_by_day,
            'att_present': present,
            'att_absent': absent,
            'att_holiday': len(holidays),
            'att_today_day': today.day,
        }

    def _ala_recent_homework(self, student, limit=6):
        """Most recent homework lines as flat cards."""
        if not student or not student.class_division_id:
            return []
        records = request.env['ala.student.homework'].sudo().search(
            [('class_div_id', '=', student.class_division_id.id)],
            order='homework_date desc', limit=limit)
        cards = []
        for hw in records:
            for line in hw.work_line_ids:
                cards.append({
                    'id': hw.id,
                    'subject': line.subject_id.name or 'General',
                    'date': hw.homework_date,
                    'text': line.homework or '',
                })
                if len(cards) >= limit:
                    return cards
        return cards

    def _ala_recent_messages(self, student, limit=4):
        """Class notes and teacher notes merged into one feed.

        Uses search() rather than raw SQL: 'desc' is a reserved SQL keyword
        and the ORM handles the quoting for us.
        """
        if not student:
            return []
        feed = []

        class_notes = request.env['ala.teacher.class.parent'].sudo().search(
            [('class_div_id', '=', student.class_division_id.id),
             ('state', '=', 'done')],
            order='create_date desc', limit=limit)
        for rec in class_notes:
            feed.append({
                'id': rec.id, 'kind': 'Class', 'desc': rec.desc or '',
                'date': rec.create_date,
                'url': '/class_comm/get_comm/%s' % rec.id,
            })

        teacher_notes = request.env['ala.teacher.student.parent'].sudo().search(
            [('student_id', '=', student.id), ('state', '=', 'done')],
            order='create_date desc', limit=limit)
        for rec in teacher_notes:
            feed.append({
                'id': rec.id, 'kind': 'Teacher', 'desc': rec.desc or '',
                'date': rec.create_date,
                'url': '/teacher_comm/get_comm/%s' % rec.id,
            })

        feed.sort(key=lambda m: m['date'], reverse=True)
        return feed[:limit]

    def _ala_fee_summary(self, student):
        """Totals for the enabled academic year + pre-computed donut dash."""
        values = {
            'fee_total': 0.0, 'fee_paid': 0.0, 'fee_balance': 0.0,
            'fee_paid_pct': 0, 'fee_dash_paid': '0 %s' % DONUT_CIRCUMFERENCE,
            'fee_status': False,
        }
        if not student:
            return values

        cr = request.env.cr
        cr.execute("""
            SELECT sf.id
            FROM ala_student_fees sf
            JOIN ala_education_academic_year ay ON sf.academic_year_id = ay.id
            WHERE sf.student_id = %s AND ay.enable = TRUE
            LIMIT 1
        """, (student.id,))
        row = cr.fetchone()
        if not row:
            return values

        fee = request.env['ala.student.fees'].sudo().browse(row[0])
        total = fee.amount_total or 0.0
        paid = fee.amount_paid or 0.0

        pct = (paid / total * 100.0) if total else 0.0
        paid_len = DONUT_CIRCUMFERENCE * (pct / 100.0)

        values.update({
            'fee_record': fee,
            'fee_total': total,
            'fee_paid': paid,
            'fee_balance': fee.amount_unpaid or 0.0,
            'fee_paid_pct': int(round(pct)),
            'fee_dash_paid': '%.2f %.2f' % (
                paid_len, DONUT_CIRCUMFERENCE - paid_len),
            'fee_status': fee.payment_status,
        })
        return values

    # ------------------------------------------------------------------
    # Home
    # ------------------------------------------------------------------
    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        values = self._prepare_portal_layout_values()

        if request.env.user._is_internal():
            return request.render(
                "ala_student_portal.teachsers_portal_my_home", values)

        cr = request.env.cr
        today = date.today()
        student = self._ala_student_from_partner()

        if not student:
            _logger.warning(
                "Portal user %s (partner %s) has no linked "
                "ala.education.student record",
                request.env.user.login, request.env.user.partner_id.id)

        division_id = student.class_division_id.id if student else False
        student_id = student.id if student else False

        cr.execute("""
            SELECT COUNT(*) FROM ala_web_info
            WHERE enable = TRUE AND date = %s
        """, (today,))
        today_announce_count = cr.fetchone()[0]

        cr.execute("""
            SELECT COUNT(*) FROM ala_teacher_class_parent
            WHERE class_div_id = %s AND state = 'done'
              AND DATE(create_date) = %s
        """, (division_id, today))
        today_cl_comm_count = cr.fetchone()[0]

        cr.execute("""
            SELECT COUNT(*) FROM ala_teacher_student_parent
            WHERE student_id = %s AND state = 'done'
              AND DATE(create_date) = %s
        """, (student_id, today))
        today_stu_comm_count = cr.fetchone()[0]

        cr.execute("""
            SELECT COUNT(*) FROM ala_student_homework
            WHERE class_div_id = %s AND homework_date = %s
        """, (division_id, today))
        today_home_work_count = cr.fetchone()[0]

        attendance = 'N/A'
        if student:
            cr.execute("""
                SELECT present FROM ala_education_attendance_line
                WHERE state = 'done' AND student_id = %s AND date = %s
                LIMIT 1
            """, (student.id, today))
            att_row = cr.fetchone()
            if att_row:
                attendance = 'Present' if att_row[0] else 'Absent'

        cr.execute("""
            SELECT id FROM ala_school_event WHERE event_date = %s LIMIT 1
        """, (today,))
        event_row = cr.fetchone()
        today_event = request.env['ala.school.event'].sudo().browse(
            event_row[0]) if event_row else False

        # legacy key, kept for any template still reading it
        cr.execute("""
            SELECT id FROM ala_student_fees WHERE student_id = %s
        """, (student_id,))
        student_fees = request.env['ala.student.fees'].sudo().browse(
            [r[0] for r in cr.fetchall()])

        values.update({
            'student': student,
            'student_fees': student_fees,
            'div_name': student.class_division_id.name if student else '',
            'greeting': self._ala_greeting(),
            'today_announce_count': today_announce_count,
            'today_cl_comm_count': today_cl_comm_count,
            'today_stu_comm_count': today_stu_comm_count,
            'today_home_work_count': today_home_work_count,
            'attendance': attendance,
            'today_event': today_event,
            'homework_cards': self._ala_recent_homework(student),
            'message_feed': self._ala_recent_messages(student),
        })
        values.update(self._ala_attendance_month(student))
        values.update(self._ala_fee_summary(student))

        return request.render(
            "ala_student_portal.student_portal_my_home", values)

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