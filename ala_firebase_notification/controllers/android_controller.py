# controllers/android_user.py
import json
from odoo import http
from odoo.http import request, Response

class WebUserController(http.Controller):

    @http.route('/android/whoami', auth='user', type='http', methods=['GET'], csrf=False)
    def whoami(self, **kw):
        user = request.env.user
        data = {
            "user_id": user.id,
            "name": user.name,
            "login": user.login,
            "partner_id": user.partner_id.id,
        }
        return Response(json.dumps(data), content_type='application/json; charset=utf-8')
