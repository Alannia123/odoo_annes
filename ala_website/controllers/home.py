# -*- coding: utf-8 -*-

import base64
from odoo import http
from odoo.http import request
from datetime import datetime
from odoo import fields, models, api, _
import json


class home_controller(http.Controller):
    """Controller for taking Home"""

    @http.route('/ala_home', type='http', auth='public', website=True)
    def ala_home_temp(self):
        vals = {}
        today_date = fields.Datetime.now().strftime('%d-%m-%Y')

        # Fetch video + images
        video = request.env['ala.web.video'].sudo().search([('show_website', '=', True)], limit=1)
        video_urls = request.env['ala.web.video.youtube'].sudo().search([('show_website', '=', True)], limit=1)

        random_images = []
        if video and video.image_ids:
            for img in video.image_ids.sorted(lambda x: x.sequence):
                random_images.append({
                    "url": "/web/image/web.video.image/%s/image" % img.id,
                    "event_name": img.name,  # show name on slide
                })

        # Notices
        print('DDDDDDDDDDDDDD',random_images)
        notices = request.env['ala.web.info'].sudo().search([('enable', '=', True)], limit=1)
        raw_html = ""
        for notice in notices:
            date = notice.date.strftime('%d-%m-%Y')
            raw_html += f"""
                <div style="text-align:center;">
                    <h4 style="color:#331a00;"><u>{date}</u></h4>
                    <span style="color:{notice.color};"><strong>{notice.anounce}</strong></span>
                </div><br/>
            """

        # Birthdays
        today = datetime.today().strftime('%m-%d')
        students = request.env['ala.education.student'].sudo().search([])
        birthday_students = students.filtered(lambda s: s.date_of_birth.strftime('%m-%d') == today)

        birth_raw_html = ""
        for i, student in enumerate(birthday_students, start=1):
            birth_raw_html += f"""
                <div style="text-align:left;">
                    <span style="color:#992600;">{i}) <strong>{student.name}({student.class_division_id.name})</strong></span>
                </div>
            """

        # birth_raw_html += '<br/><h1 class="birthday-wish text-center">Happy Birthday! 🎉</h1>'

        vals = {
            'today_date': today_date,
            'banner': request.env['banner.info'].sudo().search([('enable', '=', True)], limit=1),
            'notices': raw_html,
            'birth_raw_html': birth_raw_html,
            'today_births': birthday_students,
            'media_url': video_urls.media_url,
            'school_video_url': video_urls.school_video_url,
            'member_id': request.env['ala.school.members'].sudo().search([]),
            'random_images': json.dumps(random_images),  # 🔥 DYNAMIC IMAGES FROM web.video.image
        }

        return request.render('ala_website.ala_home_page', vals)

    @http.route('/privacy_policy', type='http', auth='public', website=True)
    def ala_school_privacy_policy(self):
        """To redirect to contact page."""
        magazines = request.env['ala.school.magazine'].sudo().search([('state', '=', 'post')])
        return request.render('ala_website.ala_school_privacy_policy')
