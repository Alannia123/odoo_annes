# -*- coding: utf-8 -*-
"""Portal routes for parent feedback.

Portal users have no ACL on ala.parent.feedback; everything here goes
through sudo() after the student link is verified from the session partner,
so a parent can only ever file or read feedback for their own child.
"""

import logging

from odoo import http
from odoo.http import request, route

_logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "academic", "teacher", "facility", "transport",
    "fees", "safety", "suggestion", "other",
}


class AlaFeedbackPortal(http.Controller):

    def _student_for_user(self):
        cr = request.env.cr
        cr.execute("""
            SELECT id FROM ala_education_student
            WHERE partner_id = %s LIMIT 1
        """, (request.env.user.partner_id.id,))
        row = cr.fetchone()
        if not row:
            return request.env["ala.education.student"]
        return request.env["ala.education.student"].sudo().browse(row[0])

    @route(["/my/feedback"], type="http", auth="user", website=True)
    def feedback_home(self, submitted=None, error=None, **kw):
        student = self._student_for_user()
        history = request.env["ala.parent.feedback"]
        if student:
            history = request.env["ala.parent.feedback"].sudo().search(
                [("student_id", "=", student.id)], limit=20)
        return request.render("ala_student_portal.portal_parent_feedback", {
            "student": student,
            "history": history,
            "submitted": submitted,
            "error": error,
        })

    @route(["/my/feedback/submit"], type="http", auth="user",
           website=True, methods=["POST"], csrf=True)
    def feedback_submit(self, **post):
        student = self._student_for_user()
        if not student:
            return request.redirect("/my/feedback?error=nostudent")

        subject = (post.get("subject") or "").strip()
        description = (post.get("description") or "").strip()
        category = post.get("category") or "other"
        rating = post.get("rating") or False

        if not subject or not description:
            return request.redirect("/my/feedback?error=missing")
        if category not in VALID_CATEGORIES:
            category = "other"
        if rating not in {"1", "2", "3", "4", "5"}:
            rating = False

        try:
            request.env["ala.parent.feedback"].sudo().create({
                "student_id": student.id,
                "partner_id": request.env.user.partner_id.id,
                "category": category,
                "subject": subject[:200],
                "description": description[:5000],
                "rating": rating,
            })
        except Exception:
            _logger.exception(
                "Parent feedback submission failed for student %s", student.id)
            return request.redirect("/my/feedback?error=server")

        return request.redirect("/my/feedback?submitted=1")