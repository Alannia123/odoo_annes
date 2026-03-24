# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EducationSubject(models.Model):
    """Manages subjects of institute"""
    _name = 'ala.education.subject'
    _description = 'Subject Details'

    name = fields.Char(string='Name', required=True,
                       help="Name of the Subject")
    type = fields.Selection([('lkg', 'LKG'),('ukg', 'UKG'), ('onetwo', '1-2 STD'), ('threefive', '3-5 STD'),
                             ('sixeight', '6-8 STD'), ('ninten', '9-10 STD')],
                            'Report Card', required=False)
    group_id = fields.Many2one(
        'ala.education.subject.group',
        string='Subject Group',
        help='Select the group this subject belongs to (Science, Language, etc.)'
    )



class EducationSubjectGroup(models.Model):
    _name = 'ala.education.subject.group'
    _description = 'Subject Group'

    name = fields.Char(string="Group Name", required=True)
    ref_name = fields.Char(string="Group Ref Name", required=True)
    code = fields.Char(string="Group Code")
    subject_ids = fields.One2many("ala.education.subject", "group_id", string="Subjects")
