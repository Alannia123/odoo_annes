# -*- coding: utf-8 -*-

from odoo import fields, models


class EducationClassHistory(models.Model):
    """Used for managing student previous class details """
    _name = 'ala.education.class.history'
    _description = "Class Room History"
    _rec_name = 'class_id'

    academic_year_id = fields.Many2one('ala.education.academic.year',
                                       string='Academic Year',
                                       help="Select the Academic Year")
    class_id = fields.Many2one('ala.education.class.division', domain=[('current_year', '=', True)],
                               string='Class', help="Select the class")
    student_id = fields.Many2one('ala.education.student',
                                 string='Students',
                                 help="Select Student of class")
