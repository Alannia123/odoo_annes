from odoo import http
from odoo.http import request

class WebsiteCertificateController(http.Controller):

    @http.route('/certificate/select', type='http', auth='public', website=True)
    def certificate_select(self, **kwargs):
        cert_types = request.env['ala.certificate'].sudo().read_group(
            [('certificate_type', '!=', False)],
            ['certificate_type'], ['certificate_type']
        )
        cert_list = [c['certificate_type'] for c in cert_types]
        return request.render("ala_website.website_certificate_select", {
            "certificate_types": cert_list
        })

    @http.route('/certificate/get_students', type='json', auth='public')
    def get_students(self, cert_type):
        cert = request.env['ala.certificate'].sudo().search([
            ('certificate_type', '=', cert_type)
        ], limit=1)

        if not cert:
            return []

        return [{
            'id': s.id,
            'name': s.student_id.name
        } for s in cert.student_line_ids]

    @http.route('/certificate/download/<int:line_id>', type='http', auth='public', website=True)
    def certificate_download(self, line_id, **kw):
        line = request.env['ala.certificate.line'].sudo().browse(line_id)
        if not line:
            return request.not_found()

        pdf = request.env.ref('ala_certificate.action_report_certificate')._render_qweb_pdf([line_id])[0]

        return request.make_response(
            pdf,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename=certificate.pdf')
            ]
        )
