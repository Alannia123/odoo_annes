# -*- coding: utf-8 -*-

from odoo import fields, models


class EducationAmenities(models.Model):
    """Used to manage amenities of institution"""
    _name = 'ala.education.amenities'
    _description = 'Amenities in Institution'

    name = fields.Char(string='Name', required=True, help='Name of amenity')
    description = fields.Char(string='Description',
                              help='Description about amenity')
    in_out_door = fields.Selection([('indoor', 'Indoor'),
                              ('outdoor', 'Outdoor')],
                             string='Indoor/Outdoor', required=True,
                             tracking=True, copy=False,)

