# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models


class AccountMove(models.Model):
    """Inherited model 'account.move' """
    _inherit = 'account.move'


    student_fee_id = fields.Many2one('ala.student.fees', 'Student Fee')
