from odoo import http
from odoo.http import request


class StudentFeePortal(http.Controller):

    @http.route('/my/fees/invoice/download/<int:fee_id>', type='http', auth='user', website=True)
    def download_fee_invoice(self, fee_id, **kw):
        fee = request.env['ala.student.fee.line'].sudo().browse(fee_id)

        if not fee.exists():
            return request.not_found()

        if fee.payment_status != 'paid':
            return request.redirect('/my/fees?payment=failed')

        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'ala_education_fee.action_generate_fees_invoice_report',
            [fee.id]
        )

        filename = '%s_invoice.pdf' % (fee.fee_description or 'fee')

        return request.make_response(
            pdf,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename="%s"' % filename),
            ]
        )