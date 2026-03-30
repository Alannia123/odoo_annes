# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountJournal(models.Model):
    """Inherited 'account.journal' model"""
    _inherit = 'account.journal'

    is_fee = fields.Boolean(string='Is Educational fee?',
                            help="Whether educational fee or not.")





class AccountMoveLine(models.Model):
    """Inherited 'account.journal' model"""
    _inherit = 'account.move.line'

    monthly_fee = fields.Boolean('Is monthly?', copy=False)
