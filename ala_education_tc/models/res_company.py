# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    tc_school_name = fields.Char(
        string='T.C. Header - School Name',
        help="Large heading printed on the Transfer Certificate. "
             "Falls back to the company name when empty.")
    tc_address_line1 = fields.Char(
        string='T.C. Header - Address Line 1',
        help="e.g. P.O.-Chotojagulia, P.S.- Duttapukur")
    tc_address_line2 = fields.Char(
        string='T.C. Header - Address Line 2',
        help="e.g. Dist.-North 24 Parganas, Pin-743294")
    tc_side_text = fields.Char(
        string='T.C. Side Band Text',
        help="Vertical text printed inside the decorative left band.")
