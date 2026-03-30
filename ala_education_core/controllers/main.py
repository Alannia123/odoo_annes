from odoo import http
from odoo.http import request


class PrivacyPolicyController(http.Controller):

    @http.route('/privacy-policy', type='http', auth='public', website=True, sitemap=True)
    def privacy_policy(self, **kwargs):
        return request.render('ala_education_core.privacy_policy_page')