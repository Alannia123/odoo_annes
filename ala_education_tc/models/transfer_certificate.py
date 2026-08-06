# -*- coding: utf-8 -*-
import base64
import logging
import secrets
from io import BytesIO

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

try:
    import qrcode
except ImportError:  # pragma: no cover - qrcode ships with Odoo requirements
    qrcode = None
    _logger.info(
        "python-qrcode not available; Transfer Certificate QR codes will fall "
        "back to Odoo's built-in reportlab barcode renderer.")

ONES = [
    '', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE',
    'TEN', 'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'FIFTEEN', 'SIXTEEN',
    'SEVENTEEN', 'EIGHTEEN', 'NINETEEN',
]
TENS = ['', '', 'TWENTY', 'THIRTY', 'FORTY', 'FIFTY', 'SIXTY', 'SEVENTY',
        'EIGHTY', 'NINETY']

# Ordinals are what the printed stationery expects: "FOURTH JUNE ..."
ORDINALS = {
    1: 'FIRST', 2: 'SECOND', 3: 'THIRD', 4: 'FOURTH', 5: 'FIFTH', 6: 'SIXTH',
    7: 'SEVENTH', 8: 'EIGHTH', 9: 'NINTH', 10: 'TENTH', 11: 'ELEVENTH',
    12: 'TWELFTH', 13: 'THIRTEENTH', 14: 'FOURTEENTH', 15: 'FIFTEENTH',
    16: 'SIXTEENTH', 17: 'SEVENTEENTH', 18: 'EIGHTEENTH', 19: 'NINETEENTH',
    20: 'TWENTIETH', 21: 'TWENTY FIRST', 22: 'TWENTY SECOND',
    23: 'TWENTY THIRD', 24: 'TWENTY FOURTH', 25: 'TWENTY FIFTH',
    26: 'TWENTY SIXTH', 27: 'TWENTY SEVENTH', 28: 'TWENTY EIGHTH',
    29: 'TWENTY NINTH', 30: 'THIRTIETH', 31: 'THIRTY FIRST',
}
MONTHS = [
    '', 'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY',
    'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER',
]
MONTH_SELECTION = [(str(i), MONTHS[i].title()) for i in range(1, 13)]


def _hundreds_to_words(num):
    """0 <= num <= 999 -> english words (uppercase)."""
    parts = []
    if num >= 100:
        parts.append('%s HUNDRED' % ONES[num // 100])
        num %= 100
    if num >= 20:
        parts.append(TENS[num // 10])
        num %= 10
        if num:
            parts.append(ONES[num])
    elif num:
        parts.append(ONES[num])
    return ' '.join(parts)


def year_to_words(year):
    """Render a 4 digit year the way the register does: 2012 -> TWO THOUSAND TWELVE."""
    year = int(year)
    if year <= 0:
        return ''
    thousands, rest = divmod(year, 1000)
    words = []
    if thousands:
        words.append('%s THOUSAND' % ONES[thousands])
    if rest:
        words.append(_hundreds_to_words(rest))
    return ' '.join(w for w in words if w).strip()


def date_to_words(value):
    """date -> 'FOURTH JUNE TWO THOUSAND TWELVE'."""
    if not value:
        return ''
    return '%s %s %s' % (
        ORDINALS.get(value.day, ''),
        MONTHS[value.month],
        year_to_words(value.year),
    )


class AlaTransferCertificate(models.Model):
    _name = 'ala.transfer.certificate'
    _description = 'Transfer Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc, id desc'

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    tc_no = fields.Char(
        string='T.C. No.', required=True, copy=False, readonly=True,
        index=True, default=lambda self: _('New'), tracking=True)
    school_roll_no = fields.Char(related='student_id.roll_no', string='School Roll No.', tracking=True, store=True)
    company_id = fields.Many2one(
        'res.company', string='School', required=True,
        default=lambda self: self.env.company)

    # ------------------------------------------------------------------
    # Scholar particulars (all manual entry)
    # ------------------------------------------------------------------
    student_id = fields.Many2one('ala.education.student', string='Name of Scholar', required=True, tracking=True)
    student_name = fields.Char(related='student_id.name', string='Name of Scholar', required=False, tracking=True, store=True)
    father_name = fields.Char(related='student_id.father_name', string="Father's Name", store=True)
    mother_name = fields.Char(related='student_id.mother_name', string="Mother's Name", store=True)
    religion = fields.Char(related='student_id.religion', string='Religion', store=True)
    gender = fields.Selection(related='student_id.gender',

        string='Gender', default='male', required=False,
        help="Drives the pronouns printed on the certificate (He/She, his/her).", store=True)

    admission_date = fields.Date(related='student_id.date_of_addmission',string='Date of Admission', store=True)
    previous_school = fields.Char(
        string='T.C. Received From',
        help="Printed after 'on a transfer certificate from'.")
    leaving_date = fields.Date(string='Date of Leaving')
    character_conduct = fields.Char(string='Character', default='SATISFACTORY')

    studying_class = fields.Char(
        string='Class Studying In (1)',
        help="Printed in words on the certificate, e.g. CLASS - 7.")
    exam_stream = fields.Char(
        string='Stream / Board (2)', default='I.C.S.E.',
        help="I.C.S.E. / Madhyamik or any other examination stream, plus school code.")

    session_from = fields.Selection(
        MONTH_SELECTION, string='Session From (3)', default='4')
    session_to = fields.Selection(
        MONTH_SELECTION, string='Session To (3)', default='3')

    dues_status = fields.Selection(
        [('paid', 'Paid'), ('not_paid', 'Not Paid')],
        string='All Sums Due (4)', default='paid', required=True)

    dob = fields.Date(related='student_id.date_of_birth', string='Date of Birth', store=True)
    dob_in_words = fields.Char(
        string='Date of Birth (in words)', compute='_compute_dob_in_words',
        store=True, readonly=False,
        help="Auto-generated from the date of birth. You may override it.")

    promotion = fields.Selection(
        [('granted', 'Granted'), ('refused', 'Refused')],
        string='Promotion (5)', default='granted')

    issue_date = fields.Date(
        string='Date of Issue', default=fields.Date.context_today, tracking=True)
    remarks = fields.Text(string='Internal Remarks')

    state = fields.Selection(
        [('draft', 'Draft'),
         ('to_approve', 'Waiting Approval'),
         ('issued', 'Issued'),
         ('cancelled', 'Cancelled')],
        string='Status', default='draft', required=True, tracking=True)

    approved_by_id = fields.Many2one(
        'res.users', string='Approved By', readonly=True, copy=False, tracking=True)
    approved_on = fields.Datetime(
        string='Approved On', readonly=True, copy=False, tracking=True)

    # ------------------------------------------------------------------
    # Verification QR
    # ------------------------------------------------------------------
    qr_token = fields.Char(
        string='QR Token', copy=False, readonly=True, index=True, tracking=True,
        help="Public identifier embedded in the verification URL. Generated "
             "from a sequence and never reused.")
    qr_url = fields.Char(
        string='QR Url', copy=False, readonly=True,
        help="The URL a scanner is sent to. Rebuilt every time the QR is generated.")
    qr_code = fields.Binary(
        string='QR Code', copy=False, readonly=True, attachment=True,
        help="PNG image printed on the bottom-right of the certificate.")

    # ------------------------------------------------------------------
    # Print helpers
    # ------------------------------------------------------------------
    pronoun_subject = fields.Char(compute='_compute_pronouns')   # He / She
    pronoun_possessive = fields.Char(compute='_compute_pronouns')  # his / her
    pronoun_possessive_cap = fields.Char(compute='_compute_pronouns')  # His / Her
    session_from_label = fields.Char(compute='_compute_session_labels')
    session_to_label = fields.Char(compute='_compute_session_labels')
    dues_label = fields.Char(compute='_compute_print_labels')
    promotion_label = fields.Char(compute='_compute_print_labels')
    admission_date_str = fields.Char(compute='_compute_date_strings')
    leaving_date_str = fields.Char(compute='_compute_date_strings')
    dob_str = fields.Char(compute='_compute_date_strings')
    issue_date_str = fields.Char(compute='_compute_date_strings')

    _sql_constraints = [
        ('tc_no_company_uniq',
         'unique(tc_no, company_id)',
         'The T.C. number must be unique per school.'),
        ('qr_token_uniq',
         'unique(qr_token)',
         'The verification token must be unique.'),
    ]

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('dob')
    def _compute_dob_in_words(self):
        for rec in self:
            rec.dob_in_words = date_to_words(rec.dob)

    @api.depends('gender')
    def _compute_pronouns(self):
        for rec in self:
            female = rec.gender == 'female'
            rec.pronoun_subject = 'She' if female else 'He'
            rec.pronoun_possessive = 'her' if female else 'his'
            rec.pronoun_possessive_cap = 'Her' if female else 'His'

    @api.depends('session_from', 'session_to')
    def _compute_session_labels(self):
        for rec in self:
            rec.session_from_label = MONTHS[int(rec.session_from)] if rec.session_from else ''
            rec.session_to_label = MONTHS[int(rec.session_to)] if rec.session_to else ''

    @api.depends('dues_status', 'promotion')
    def _compute_print_labels(self):
        for rec in self:
            rec.dues_label = 'PAID' if rec.dues_status == 'paid' else 'NOT PAID'
            rec.promotion_label = (rec.promotion or '').upper()

    @api.depends('admission_date', 'leaving_date', 'dob', 'issue_date')
    def _compute_date_strings(self):
        """The stationery is filled in dd.mm.yyyy - keep that format in one place."""
        for rec in self:
            rec.admission_date_str = rec.admission_date and rec.admission_date.strftime('%d.%m.%Y') or ''
            rec.leaving_date_str = rec.leaving_date and rec.leaving_date.strftime('%d.%m.%Y') or ''
            rec.dob_str = rec.dob and rec.dob.strftime('%d.%m.%Y') or ''
            rec.issue_date_str = rec.issue_date and rec.issue_date.strftime('%d.%m.%Y') or ''

    @api.depends('tc_no', 'student_name')
    def _compute_display_name(self):
        for rec in self:
            if rec.student_name:
                rec.display_name = '%s - %s' % (rec.tc_no or '', rec.student_name)
            else:
                rec.display_name = rec.tc_no or ''

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('tc_no') or vals.get('tc_no') == _('New'):
                company_id = vals.get('company_id') or self.env.company.id
                seq = self.env['ir.sequence'].with_company(company_id)
                vals['tc_no'] = seq.next_by_code('ala.transfer.certificate') or _('New')
        return super().create(vals_list)

    def copy_data(self, default=None):
        default = dict(default or {})
        default.setdefault('tc_no', _('New'))
        default.setdefault('state', 'draft')
        return super().copy_data(default)

    def unlink(self):
        for rec in self:
            if rec.state == 'issued':
                raise UserError(_(
                    "T.C. %s has already been issued and cannot be deleted. "
                    "Cancel it instead so the number stays traceable.", rec.tc_no))
        return super().unlink()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _check_mandatory_fields(self):
        """Shared gate: the printed stationery has no room for blanks."""
        for rec in self:
            missing = [
                label for label, value in (
                    ('Name of Scholar', rec.student_name),
                    ('Date of Admission', rec.admission_date),
                    ('Date of Leaving', rec.leaving_date),
                    ('Date of Birth', rec.dob),
                    ('Class Studying In', rec.studying_class),
                ) if not value
            ]
            if missing:
                raise UserError(_(
                    "Fill the following before submitting the T.C.:\n- %s",
                    "\n- ".join(missing)))
            if rec.leaving_date and rec.admission_date and rec.leaving_date < rec.admission_date:
                raise UserError(_("Date of leaving cannot be earlier than date of admission."))

    def action_submit(self):
        """Officer hands the draft over to the Principal."""
        self._check_mandatory_fields()
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only a draft T.C. can be submitted for approval."))
        self.write({'state': 'to_approve'})
        return True

    def action_approve(self):
        """Principal-only approval. This is the moment the QR is minted."""
        if not self.env.user.has_group('ala_education_tc.group_ala_tc_principal'):
            raise AccessError(_(
                "Only the Principal can approve a Transfer Certificate."))
        self._check_mandatory_fields()
        for rec in self:
            if rec.state != 'to_approve':
                raise UserError(_(
                    "T.C. %s is not waiting for approval.", rec.tc_no))
            rec.write({
                'state': 'issued',
                'approved_by_id': self.env.user.id,
                'approved_on': fields.Datetime.now(),
                'issue_date': rec.issue_date or fields.Date.context_today(rec),
            })
            rec.action_generate_qr_code()
            rec.message_post(body=_(
                "Transfer Certificate approved and issued by %s.",
                self.env.user.display_name))
        return True

    def action_refuse(self):
        """Principal sends it back to the officer for correction."""
        if not self.env.user.has_group('ala_education_tc.group_ala_tc_principal'):
            raise AccessError(_(
                "Only the Principal can refuse a Transfer Certificate."))
        self.write({'state': 'draft'})
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state == 'issued' and not self.env.user.has_group(
                    'ala_education_tc.group_ala_tc_manager'):
                raise AccessError(_(
                    "An issued T.C. can only be reopened by a Certificate Manager."))
        self.write({'state': 'draft'})
        return True

    # ------------------------------------------------------------------
    # QR generation / verification
    # ------------------------------------------------------------------
    def _get_base_url(self):
        """web.base.url is the single source of truth behind an Nginx proxy."""
        return (self.env['ir.config_parameter'].sudo()
                .get_param('web.base.url', '') or '').rstrip('/')

    def _next_qr_token(self):
        """Sequence-derived token plus a short random suffix.

        The sequence keeps tokens traceable and ordered. The random suffix is
        what stops someone walking TCQR000031, TCQR000032, ... and harvesting
        student names, parents' names and dates of birth from the public verify
        page. Drop the suffix only if you accept that enumeration risk.
        """
        self.ensure_one()
        seq = (self.env['ir.sequence'].sudo()
               .next_by_code('ala.transfer.certificate.qr.token')
               or 'TCQR%s' % (self._origin.id or 0))
        return '%s%s' % (seq.replace('/', ''), secrets.token_hex(3).upper())

    def _build_qr_verify_url(self):
        self.ensure_one()
        return '%s/tc/verify/%s/%s' % (
            self._get_base_url(), self._origin.id or self.id, self.qr_token or '')

    def _render_qr_png(self, payload):
        """Return raw PNG bytes for `payload`.

        Primary path is python-qrcode. If it is missing we fall back to the
        renderer Odoo already ships (reportlab, via ir.actions.report.barcode)
        so the module never hard-fails on a lean server build.
        """
        if qrcode is not None:
            qr = qrcode.QRCode(version=None, box_size=10, border=2,
                               error_correction=qrcode.constants.ERROR_CORRECT_M)
            qr.add_data(payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()
        return self.env['ir.actions.report'].barcode(
            'QR', payload, width=256, height=256, humanreadable=0)

    def action_generate_qr_code(self):
        """Mint (or re-render) the verification QR.

        The token is created once and then frozen: regenerating the image must
        never invalidate a QR that is already printed on paper in a parent's
        hands.
        """
        for rec in self:
            if not rec._origin.id:
                raise UserError(_("Save the record before generating a QR code."))
            if not rec.qr_token:
                rec.qr_token = rec._next_qr_token()

            qr_data = rec._build_qr_verify_url()
            rec.qr_url = qr_data
            try:
                png = rec._render_qr_png(qr_data)
            except Exception:
                _logger.exception("QR generation failed for T.C. %s", rec.tc_no)
                raise UserError(_(
                    "Could not generate the QR code. Check that the 'qrcode' "
                    "Python package is installed on the server."))
            rec.qr_code = base64.b64encode(png)
        return True

    def get_verify_qr(self):
        """Called from QWeb. Renders on demand so old records still print a QR."""
        self.ensure_one()
        if not self.qr_code and self.state == 'issued':
            self.sudo().action_generate_qr_code()
        return self.qr_code

    # ------------------------------------------------------------------
    # Printing
    # ------------------------------------------------------------------
    def action_print_tc(self):
        self.ensure_one()
        if self.state != 'issued':
            raise UserError(_(
                "Only an approved (issued) T.C. can be printed."))
        return self.env.ref(
            'ala_education_tc.action_report_transfer_certificate').report_action(self)

    def action_print_blank(self):
        return self.env.ref(
            'ala_education_tc.action_report_transfer_certificate_blank').report_action(self)
