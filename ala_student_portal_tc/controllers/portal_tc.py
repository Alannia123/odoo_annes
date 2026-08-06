# -*- coding: utf-8 -*-
import logging

from werkzeug.exceptions import Forbidden, NotFound

from odoo import http
from odoo.http import content_disposition, request

_logger = logging.getLogger(__name__)


class StudentPortalTransferCertificate(http.Controller):
    """Parent-facing download of an approved Transfer Certificate."""

    def _portal_student(self):
        """Resolve the student behind the logged-in portal user."""
        partner = request.env.user.partner_id
        if not partner:
            return request.env['ala.education.student']
        return request.env['ala.education.student'].sudo().search(
            [('partner_id', '=', partner.id)], limit=1)

    @http.route(['/my/tc/download/<int:tc_id>'],
                type='http', auth='user', website=True, sitemap=False)
    def portal_download_tc(self, tc_id, **kw):
        tc = request.env['ala.transfer.certificate'].sudo().browse(tc_id)

        # exists + approved.  A draft or cancelled T.C. must never leave the
        # building, so this is checked before ownership - a 404 leaks less
        # than a 403 about which ids are real.
        if not tc.exists() or tc.state != 'issued':
            raise NotFound()

        student = tc.student_id
        if not student or not student.sudo()._portal_tc_is_owner():
            _logger.warning(
                "Portal user %s attempted to download T.C. %s belonging to "
                "student %s", request.env.user.login, tc.tc_no, student.id or 0)
            raise Forbidden()

        pdf, _content_type = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'ala_education_tc.action_report_transfer_certificate', [tc.id])

        filename = 'Transfer_Certificate_%s.pdf' % (
            (tc.tc_no or str(tc.id)).replace('/', '-').replace(' ', '_'))

        return request.make_response(pdf, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', content_disposition(filename)),
        ])
