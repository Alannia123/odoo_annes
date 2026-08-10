# -*- coding: utf-8 -*-
import logging
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import is_html_empty

_logger = logging.getLogger(__name__)

LANG_RE = re.compile(r'^[a-z]{2,3}(_[A-Z]{2})?$')

# Frontend paths on which a popup may be rendered.
PORTAL_HOME_PATHS = (('my',), ('my', 'home'))


class AlaPortalAnnouncement(models.Model):
    _name = 'ala.portal.announcement'
    _description = 'Portal / Website Announcement Popup'
    _order = 'sequence, id desc'

    name = fields.Char(
        string='Internal Reference', required=True,
        help="Only used in the back-office list. Not shown to visitors.")
    active = fields.Boolean(default=True)
    sequence = fields.Integer(
        default=10,
        help="When several announcements are live, the lowest sequence is shown first.")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------
    display_mode = fields.Selection(
        selection=[
            ('image', 'Image only'),
            ('message', 'Message only'),
            ('both', 'Image + Message'),
        ],
        string='Show', default='image', required=True)
    title = fields.Char(string='Heading', translate=True)
    body = fields.Html(string='Message', translate=True, sanitize=True)
    image = fields.Image(string='Poster', max_width=1920, max_height=1920)
    image_alt = fields.Char(
        string='Image Description', default='Announcement',
        help="Read out by screen readers and shown while the image loads.")
    cta_label = fields.Char(string='Button Label')
    cta_url = fields.Char(string='Button Link')

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------
    date_start = fields.Datetime(
        string='Show From', required=True, default=fields.Datetime.now)
    date_end = fields.Datetime(
        string='Show Until', required=True,
        help="After this moment the popup stops appearing. No manual cleanup needed.")
    frequency = fields.Selection(
        selection=[
            ('once', 'Once per visitor'),
            ('session', 'Once per browser session'),
            ('daily', 'Once per day'),
            ('always', 'Every page load'),
        ],
        default='always', required=True)

    # ------------------------------------------------------------------
    # Placement & audience
    # ------------------------------------------------------------------
    show_on_website = fields.Boolean(string='Website Home Page', default=True)
    show_on_portal = fields.Boolean(string='Portal Home Page', default=True)
    audience = fields.Selection(
        selection=[
            ('all', 'Everyone'),
            ('public', 'Public visitors only'),
            ('logged', 'Logged-in users only'),
        ],
        default='all', required=True)
    group_ids = fields.Many2many(
        'res.groups', string='Restrict to Groups',
        help="Leave empty for no group restriction. When set, only users in at "
             "least one of these groups see the popup (public visitors never do).")

    # ------------------------------------------------------------------
    # Computed helpers
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('live', 'Live'),
            ('expired', 'Expired'),
            ('archived', 'Archived'),
        ],
        compute='_compute_state', string='Status')
    token = fields.Char(
        compute='_compute_token',
        help="Changes whenever the record is edited, so updated content is shown "
             "again to visitors who already dismissed the previous version.")

    @api.depends('active', 'date_start', 'date_end')
    def _compute_state(self):
        now = fields.Datetime.now()
        for rec in self:
            if not rec.active:
                rec.state = 'archived'
            elif rec.date_start and rec.date_start > now:
                rec.state = 'scheduled'
            elif rec.date_end and rec.date_end < now:
                rec.state = 'expired'
            else:
                rec.state = 'live'

    @api.depends('write_date')
    def _compute_token(self):
        for rec in self:
            # _origin guards against NewId pseudo-records in onchange context.
            rec_id = rec._origin.id or 0
            stamp = int(rec.write_date.timestamp()) if rec.write_date else 0
            rec.token = '%s-%s' % (rec_id, stamp)

    # ------------------------------------------------------------------
    # Constraints (kept as constrains, not onchange, so REST/RPC writes
    # are validated too)
    # ------------------------------------------------------------------
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end <= rec.date_start:
                raise ValidationError(
                    _("'Show Until' must be later than 'Show From' on %s.", rec.name))

    @api.constrains('display_mode', 'image', 'body')
    def _check_content(self):
        for rec in self:
            if rec.display_mode in ('image', 'both') and not rec.image:
                raise ValidationError(
                    _("Add a poster image, or switch '%s' to Message only.", rec.name))
            if rec.display_mode in ('message', 'both') and is_html_empty(rec.body):
                raise ValidationError(
                    _("Add a message, or switch '%s' to Image only.", rec.name))

    @api.constrains('show_on_website', 'show_on_portal')
    def _check_placement(self):
        for rec in self:
            if not rec.show_on_website and not rec.show_on_portal:
                raise ValidationError(
                    _("Pick at least one page for '%s': website home or portal home.",
                      rec.name))

    @api.constrains('cta_label', 'cta_url')
    def _check_cta(self):
        for rec in self:
            if rec.cta_label and not rec.cta_url:
                raise ValidationError(_("The button on '%s' needs a link.", rec.name))

    # ------------------------------------------------------------------
    # Public API used by the frontend controller (and reusable from the
    # mobile REST layer)
    # ------------------------------------------------------------------
    @api.model
    def _live_domain(self, scope):
        now = fields.Datetime.now()
        domain = [('date_start', '<=', now), ('date_end', '>=', now)]
        if scope == 'portal':
            domain.append(('show_on_portal', '=', True))
        else:
            domain.append(('show_on_website', '=', True))
        return domain

    def _user_group_ids(self, user):
        """Odoo renamed res.users.groups_id over recent versions; resolve safely."""
        for fname in ('all_group_ids', 'group_ids', 'groups_id'):
            if fname in user._fields:
                return user[fname]
        return self.env['res.groups'].browse()

    @api.model
    def _fetch_for_visitor(self, scope='website', is_public=True, limit=5):
        """Return a JSON-serialisable list of popups for the current visitor."""
        scope = 'portal' if scope == 'portal' else 'website'
        records = self.sudo().search(self._live_domain(scope), limit=limit)
        user = self.env.user
        user_groups = self._user_group_ids(user)
        payload = []
        for rec in records:
            if rec.audience == 'public' and not is_public:
                continue
            if rec.audience == 'logged' and is_public:
                continue
            if rec.group_ids and (is_public or not (user_groups & rec.group_ids)):
                continue
            payload.append(rec._prepare_popup_payload())
        return payload

    def _prepare_popup_payload(self):
        self.ensure_one()
        wants_image = self.display_mode in ('image', 'both')
        wants_text = self.display_mode in ('message', 'both')
        return {
            'id': self.id,
            'token': self.token,
            'mode': self.display_mode,
            'title': (self.title or '') if wants_text or self.title else '',
            'body': (self.body or '') if wants_text else '',
            'image_url': ('/ala/announcement/%s/image?u=%s' % (self.id, self.token)
                          if wants_image else ''),
            'image_alt': self.image_alt or '',
            'cta_label': self.cta_label or '',
            'cta_url': self.cta_url or '',
            'frequency': self.frequency,
        }

    # ------------------------------------------------------------------
    # Where should the popup mount?
    # ------------------------------------------------------------------
    @api.model
    def _popup_scope_for_request(self):
        """Return 'website', 'portal' or False for the current request path.

        Handles the website language prefix (/en/, /fr_BE/...) so the home page
        is still detected on multi-language sites.
        """
        if not request:
            return False
        try:
            path = (request.httprequest.path or '/').split('?')[0]
            parts = [p for p in path.split('/') if p]
            if parts and LANG_RE.match(parts[0]):
                installed = request.env['res.lang'].sudo().get_installed()
                codes = set()
                for code, _name in installed:
                    codes.add(code)
                    codes.add(code.split('_')[0])
                if parts[0] in codes:
                    parts = parts[1:]
            if not parts:
                return 'website'
            if tuple(parts) in PORTAL_HOME_PATHS:
                return 'portal'
        except Exception:  # never break page rendering because of a popup
            _logger.exception("Announcement: could not resolve popup scope")
        return False

    def action_preview(self):
        """Open the website / portal home page to preview the popup."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/my/home' if self.show_on_portal else '/',
        }
