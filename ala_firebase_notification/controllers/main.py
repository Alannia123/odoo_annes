# controllers/fcm.py
import json
from odoo import http
from odoo.http import request, Response

class FcmController(http.Controller):

    @http.route('/fcm/register', auth='user', type='http', methods=['POST'], csrf=False)
    def register_fcm(self, **kw):
        payload = request.jsonrequest or {}
        token = payload.get('fcm_token')
        device_name = payload.get('device_name')

        if token:
            request.env.user.sudo().write({
                'fcm_token': token,
                # optional fields if you add them
                # 'fcm_device_name': device_name,
            })

        return Response(json.dumps({"status": "ok"}), content_type='application/json; charset=utf-8')
