# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    Configure the access credentials
    """
    _inherit = 'res.config.settings'

    amazon_access_key = fields.Char(string='Amazon S3 Access Key', copy=False,
                                    config_parameter='ala_website_backend.amazon_access_key',
                                    help='Enter your Amazon S3 Access Key here.')
    amazon_secret_key = fields.Char(string='Amazon S3 Secret key',
                                    config_parameter='ala_website_backend.amazon_secret_key',
                                    help='Enter your Amazon S3 Secret Key here.')
    amazon_bucket_name = fields.Char(string='Folder ID',
                                     config_parameter='ala_website_backend.amazon_bucket_name',
                                     help='Enter the name of your Amazon S3 Bucket here.')
    amazon_region_name = fields.Char(string='Region Name',
                                     config_parameter='ala_website_backend.amazon_region_name',
                                     help='Enter the name of your Amazon S3 Region here.')
    is_amazon_connector = fields.Boolean(
        config_parameter='ala_website_backend.amazon_connector', default=False,
        help='Enable or disable the Amazon S3 connector.')

    facebook_link = fields.Char(
        string="Facebook Link",
        config_parameter='website.facebook_link'
    )

    instagram_link = fields.Char(
        string="Instagram Link",
        config_parameter='website.instagram_link'
    )

    youtube_link = fields.Char(
        string="YouTube Link",
        config_parameter='website.youtube_link'
    )

    twitter_link = fields.Char(
        string="Twitter Link",
        config_parameter='website.twitter_link'
    )
    google_map_link = fields.Char(
        string="Google Map Location",
        config_parameter='website.google_map_link'
    )
