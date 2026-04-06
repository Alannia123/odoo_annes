# -*- coding: utf-8 -*-

import base64
from odoo import http
from odoo.http import request


class ala_prospectus(http.Controller):
    """Controller for taking Prospectus"""

    @http.route('/prospectus', type='http', auth='public', website=True)
    def about_ala_prospectus_cont(self):
        """To redirect to contact page."""
        return request.render('ala_website.ala_propectus_page')

    @http.route('/ala_oblates', type='http', auth='public', website=True)
    def ala_oblates_cont(self):
        """To redirect to contact page."""
        return request.render('ala_website.ala_oblates')

    @http.route('/omi_and_education', type='http', auth='public', website=True)
    def omi_and_education_cont(self):
        """To redirect to contact page."""
        return request.render('ala_website.omi_and_education')

    @http.route('/mission_and_vission', type='http', auth='public', website=True)
    def vision_mission_cont(self):
        """To redirect to contact page."""
        return request.render('ala_website.mission_and_vission')


    @http.route('/govering_body_members', type='http', auth='public', website=True)
    def govering_body_members_cont(self):
        """To redirect to contact page."""
        return request.render('ala_website.govering_body_members')


    @http.route('/academic_council', type='http', auth='public', website=True)
    def academic_council_cont(self):
        """To redirect to contact page."""
        return request.render('ala_website.academic_council')


    @http.route('/core_commitee', type='http', auth='public', website=True)
    def core_commitee_cont(self):
        """To redirect to contact page."""
        return request.render('ala_website.core_commitee')


    @http.route('/alumni_ae_associates', type='http', auth='public', website=True)
    def alumni_ae_associates_cont(self):
        """To redirect to contact page."""
        return request.render('ala_website.alumni_ae_associates')

