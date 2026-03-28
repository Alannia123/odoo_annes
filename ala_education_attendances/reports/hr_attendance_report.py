# -*- coding: utf-8 -*-

from odoo import api, models
from markupsafe import Markup



class ReportHrAttendance(models.AbstractModel):
    """This is an abstract model for the Attendance Report of Employees."""
    _name = 'report.ala_education_attendances.report_student_attendance'
    _description = 'Attendance Report  of Students'

    @api.model
    def _get_report_values(self, doc_ids, data=None):
        data = data or {}  # ✅ CRITICAL

        return {
            'doc_model': 'ala.education.attendance.line',
            'data': {
                'tHead': Markup(data.get('tHead', '')),
                'tBody': Markup(data.get('tBody', '')),
            },
        }
