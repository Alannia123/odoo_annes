# -*- coding: utf-8 -*-

import base64
from odoo import http
from odoo.http import request


class ala_academics(http.Controller):
    """Controller for taking Prospectus"""

    @http.route('/ala_academics', type='http', auth='public', website=True)
    def academic_ala_cont(self):
        """To redirect to contact page."""
        return request.render('ala_website.ala_academics')

    @http.route('/student_performance', type='http', auth='public', website=True)
    def ala_student_performance_cont(self):
        """To redirect to contact page."""
        return request.render('ala_website.student_performance')

