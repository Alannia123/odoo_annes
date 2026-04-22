from odoo import http
from odoo.http import request


class FacultyTimetableController(http.Controller):

    @http.route('/faculty_timetable/preview/<int:record_id>', type='http', auth='user', website=True)
    def faculty_timetable_preview(self, record_id, **kwargs):
        record = request.env['ala.education.faculty.timetable'].sudo().browse(record_id)

        if not record.exists():
            return request.not_found()

        values = {
            'record': record,
        }
        return request.render('ala_education_time_table.faculty_timetable_preview_template', values)