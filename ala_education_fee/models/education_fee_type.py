# -*- coding: utf-8 -*-

from odoo import api, fields, models


class EducationFeeType(models.Model):
    """Creating model  'ala.education.fee.type' with fields"""
    _name = 'ala.education.fee.type'
    _inherits = {'product.product': 'product_variant_id'}

    payment_type = fields.Selection([
        ('onetime', 'One Time'),
        ('permonth', 'Per Month'),
        ('peryear', 'Per Year'),
        ('sixmonth', '6 Months'),
        ('threemonth', '3 Months')
    ], string='Payment Type', default='permonth',
        help='Payment type describe how much a payment effective.'
             ' Like, bus fee per month is 30 dollar, sports fee per '
             'year is 40 dollar, etc')
    interval = fields.Char(string='Payment Interval',
                           help='Interval describe the payment mode of the fee.'
                                'For example, Monthly means the fee must be '
                                'paid in each month.'
                                'Yearly means the payment paid only '
                                'one time uin year.')

    category_id = fields.Many2one('ala.education.fee.category',
                                  string='Category',
                                  required=True,
                                  help="Fee category",
                                  default=lambda self: self.env[
                                      'ala.education.fee.category'].search([],
                                                                       limit=1))

    