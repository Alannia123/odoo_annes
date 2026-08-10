# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website


class CustomLoginRedirect(Website):
    """Send portal (student / parent) logins straight to the portal home url.

    Odoo's website layer already redirects non-internal users to ``/my`` after
    login. We make that explicit and point it at the real home page
    (``/my/home``) so a portal user always lands on their dashboard. Internal
    users (staff / admin) are left to the standard backend redirect.
    """

    def _login_redirect(self, uid, redirect=None):
        if not redirect and request.params.get('login_success'):
            user = request.env['res.users'].sudo().browse(uid)
            if not user._is_internal():
                redirect = '/my/home'
        return super()._login_redirect(uid, redirect=redirect)


class CustomLogout(http.Controller):
    @http.route('/web/session/logout', type='http', auth="public", website=True)
    def logout(self, redirect='/web/login'):
        request.session.logout()
        return request.redirect(redirect)
