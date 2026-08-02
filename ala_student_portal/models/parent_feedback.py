# -*- coding: utf-8 -*-
"""Parent feedback captured from the student portal.

Portal users create records through the controller with sudo(); they never
get direct ACL on this model. Every new record notifies the principal
configured in Settings, both as a chatter message and as a scheduled
activity so it lands in the principal's Odoo activity list.
"""

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class AlaParentFeedback(models.Model):
    _name = "ala.parent.feedback"
    _description = "Parent Feedback"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(
        string="Reference", required=True, copy=False, readonly=True,
        default=lambda self: _("New"))

    # --- who -----------------------------------------------------------
    student_id = fields.Many2one(
        "ala.education.student", string="Student",
        required=True, ondelete="cascade", tracking=True)
    partner_id = fields.Many2one(
        "res.partner", string="Submitted By", required=True, ondelete="restrict")
    class_division_id = fields.Many2one(
        related="student_id.class_division_id", store=True, readonly=True,
        string="Class")

    # --- what ----------------------------------------------------------
    category = fields.Selection(
        selection=[
            ("academic", "Academics & Teaching"),
            ("teacher", "Teacher Conduct"),
            ("facility", "Infrastructure & Facilities"),
            ("transport", "Transport"),
            ("fees", "Fees & Billing"),
            ("safety", "Safety & Wellbeing"),
            ("suggestion", "Suggestion"),
            ("other", "Other"),
        ],
        string="Category", required=True, default="other", tracking=True)
    subject = fields.Char(string="Subject", required=True, tracking=True)
    description = fields.Text(string="Feedback", required=True)
    rating = fields.Selection(
        selection=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")],
        string="Rating")

    priority = fields.Selection(
        selection=[("0", "Normal"), ("1", "Important"), ("2", "Urgent")],
        string="Priority", default="0", tracking=True)

    # --- handling ------------------------------------------------------
    state = fields.Selection(
        selection=[
            ("new", "New"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        string="Status", default="new", required=True, tracking=True)
    response = fields.Text(string="School Response", tracking=True)
    responded_by_id = fields.Many2one(
        "res.users", string="Responded By", readonly=True)
    response_date = fields.Datetime(string="Responded On", readonly=True)

    company_id = fields.Many2one(
        "res.company", string="School", default=lambda self: self.env.company)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ala.parent.feedback") or _("New")
        records = super().create(vals_list)
        records._notify_principal()
        return records

    def write(self, vals):
        if "response" in vals and vals.get("response"):
            vals.setdefault("responded_by_id", self.env.user.id)
            vals.setdefault("response_date", fields.Datetime.now())
        return super().write(vals)

    # ------------------------------------------------------------------
    # Notification
    # ------------------------------------------------------------------
    def _principal_user(self):
        """User configured as principal in Settings, if any."""
        param = self.env["ir.config_parameter"].sudo().get_param(
            "ala_student_portal.principal_user_id")
        if not param:
            return self.env["res.users"]
        try:
            user = self.env["res.users"].browse(int(param)).exists()
        except (TypeError, ValueError):
            return self.env["res.users"]
        return user

    def _notify_principal(self):
        """Post to chatter and schedule an activity for the principal.

        Never raises: a mail configuration problem must not roll back the
        parent's submission.
        """
        principal = self._principal_user()
        if not principal:
            _logger.warning(
                "ala.parent.feedback: no principal configured "
                "(ir.config_parameter ala_student_portal.principal_user_id); "
                "records %s created without notification", self.ids)
            return

        for record in self:
            body = _(
                "New parent feedback %(ref)s\n"
                "Student: %(student)s (%(klass)s)\n"
                "Category: %(category)s\n"
                "Subject: %(subject)s"
            ) % {
                "ref": record.name,
                "student": record.student_id.name or "",
                "klass": record.class_division_id.name or "",
                "category": dict(
                    self._fields["category"].selection).get(record.category, ""),
                "subject": record.subject or "",
            }
            try:
                record.message_post(
                    body=body,
                    subject=_("Parent Feedback: %s") % record.subject,
                    partner_ids=principal.partner_id.ids,
                    message_type="notification",
                    subtype_xmlid="mail.mt_comment",
                )
                record.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=principal.id,
                    summary=_("Review parent feedback %s") % record.name,
                    note=record.subject or "",
                )
            except Exception:
                _logger.exception(
                    "ala.parent.feedback: notification failed for %s",
                    record.name)

    # ------------------------------------------------------------------
    # Status buttons
    # ------------------------------------------------------------------
    def action_start(self):
        self.write({"state": "in_progress"})

    def action_resolve(self):
        for record in self:
            if not record.response:
                from odoo.exceptions import UserError
                raise UserError(
                    _("Add a response before marking %s as resolved.")
                    % record.name)
        self.write({"state": "resolved"})

    def action_close(self):
        self.write({"state": "closed"})

    def action_reset(self):
        self.write({"state": "new"})