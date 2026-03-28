# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """This class extends the `res.config.settings` model to add configuration
     settings for the HR Attendance Dashboard's default present and absent
      marks.  """
    _inherit = 'res.config.settings'

    present = fields.Selection([('present', 'Present'),
                                ('\u2714', '✔'), ('\u2705', '✅ '), ('p', 'P')],
                               string='Default Present Mark',
                               config_parameter='ala_education_attendance_dashboard.present',
                               help='Select the default mark for present '
                                    'attendance.')
    absent = fields.Selection([('absent', 'Absent'),
                               ('\u2716', '✘'), ('\u274C', '❌'),
                               ('\u2B55', '⭕'), ('a', 'A')
                               ], string='Default Absent Mark',
                              config_parameter='ala_education_attendance_dashboard.absent',
                              help='Select the default mark for absent '
                                   'attendance.')
