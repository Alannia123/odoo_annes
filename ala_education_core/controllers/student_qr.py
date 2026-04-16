from odoo import http
from odoo.http import request


class StudentVerificationController(http.Controller):

    @http.route(
        ['/student/verify/<int:student_id>/<string:token>'],
        type='http',
        auth='public',
        website=True,
        csrf=False
    )
    def verify_student(self, student_id, token, **kwargs):
        student = request.env['ala.education.student'].sudo().search([
            ('id', '=', student_id),
            ('qr_token', '=', token),
        ], limit=1)
        print('----------==================',student)

        values = {
            'student': student,
            'is_valid': bool(student),
        }
        return request.render('ala_education_core.student_qr_verify_template', values)