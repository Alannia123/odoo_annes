# -*- coding: utf-8 -*-
import logging

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

MODEL = 'ala.portal.announcement'


class AlaAnnouncementController(http.Controller):

    @http.route('/ala/announcement/active', type='http', auth='public',
                methods=['GET'], website=True, sitemap=False, csrf=False)
    def announcement_active(self, scope='website', **kwargs):
        """Return the popups the current visitor is allowed to see."""
        # request.session.uid is falsy for the public user, truthy for portal
        # and internal users - reliable across versions.
        is_public = not bool(request.session.uid)
        try:
            data = request.env[MODEL].sudo()._fetch_for_visitor(
                scope=scope, is_public=is_public)
        except Exception:
            _logger.exception("Announcement: failed to build popup payload")
            data = []
        response = request.make_json_response({'announcements': data})
        # Per-visitor content: never let a proxy or CDN share this.
        response.headers['Cache-Control'] = 'no-store, private'
        return response

    @http.route('/ala/announcement/<int:announcement_id>/image', type='http',
                auth='public', methods=['GET'], website=True, sitemap=False)
    def announcement_image(self, announcement_id, **kwargs):
        """Serve the poster without granting public read on the model."""
        record = request.env[MODEL].sudo().browse(announcement_id).exists()
        # 404 before 403: never confirm that a hidden record exists.
        if not record or not record.active or not record.image:
            return request.not_found()
        now = fields.Datetime.now()
        if record.date_start > now or record.date_end < now:
            return request.not_found()

        stream = request.env['ir.binary']._get_image_stream_from(
            record, field_name='image')
        response = stream.get_response()
        # The URL carries ?u=<token>, so it is safe to cache aggressively.
        response.headers['Cache-Control'] = 'public, max-age=604800'
        return response
