# -*- coding: utf-8 -*-
from odoo import models


class AlaEducationStudent(models.Model):
    _inherit = 'ala.education.student'

    # ------------------------------------------------------------------
    # Portal helpers
    # ------------------------------------------------------------------
    def _portal_tc_is_owner(self):
        """True when the caller is entitled to see this student's T.C.

        The portal page itself already scopes to the logged-in parent, but this
        method is reachable over RPC too.  Without this guard a portal user who
        can reach any student record could enumerate certificates, so the check
        lives on the method rather than on the page.
        """
        self.ensure_one()
        user = self.env.user
        if user.has_group('base.group_user'):
            return True
        return bool(self.partner_id) and self.partner_id == user.partner_id

    def get_portal_transfer_certificates(self):
        """Approved certificates this parent may download.  Newest first."""
        self.ensure_one()
        if not self._portal_tc_is_owner():
            return self.env['ala.transfer.certificate']
        return self.env['ala.transfer.certificate'].sudo().search(
            [('student_id', '=', self.id), ('state', '=', 'issued')],
            order='issue_date desc, id desc')

    def has_pending_transfer_certificate(self):
        """A T.C. exists but the Principal has not approved it yet.

        Drives a 'being processed' notice instead of 'contact the office',
        which saves the front desk a phone call.
        """
        self.ensure_one()
        if not self._portal_tc_is_owner():
            return False
        return bool(self.env['ala.transfer.certificate'].sudo().search_count(
            [('student_id', '=', self.id),
             ('state', 'in', ('draft', 'to_approve'))]))
