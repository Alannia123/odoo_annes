# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TransferCertificateVerifyController(http.Controller):
    """Public landing page for the QR printed on the certificate.

    auth='public' is required: the person scanning is a college admissions
    clerk or an employer, not a portal user. Nothing here is writable and the
    payload is deliberately limited to what already appears on the paper the
    scanner is holding.
    """

    @http.route(
        ['/tc/verify/<int:tc_id>/<string:token>'],
        type='http', auth='public', csrf=False, website=True, sitemap=False)
    def verify_transfer_certificate(self, tc_id, token, **kwargs):
        company = request.env.company.sudo()

        tc = request.env['ala.transfer.certificate'].sudo().search([
            ('id', '=', tc_id),
            ('qr_token', '=', token),
            ('state', '=', 'issued'),
        ], limit=1)

        if not tc:
            _logger.info(
                "TC verification miss: id=%s token=%s", tc_id, (token or '')[:8])
            return request.render(
                'ala_education_tc.tc_verify_invalid', {'company': company})

        return request.render('ala_education_tc.tc_verify_valid', {
            'tc': tc,
            'company': tc.company_id or company,
        })

    @http.route(['/tc/verify'], type='http', auth='public', sitemap=False)
    def verify_missing_params(self, **kwargs):
        return request.render(
            'ala_education_tc.tc_verify_invalid',
            {'company': request.env.company.sudo()})
