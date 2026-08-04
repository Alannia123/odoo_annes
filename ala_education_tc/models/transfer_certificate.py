# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

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
    student_name = fields.Char(related='student_id.name', string='Name of Scholar', required=True, tracking=True, store=True)
    father_name = fields.Char(related='student_id.father_name', string="Father's Name", store=True)
    mother_name = fields.Char(related='student_id.mother_name', string="Mother's Name", store=True)
    religion = fields.Char(related='student_id.religion', string='Religion', store=True)
    gender = fields.Selection(related='student_id.gender',

        string='Gender', default='male', required=True,
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
        [('draft', 'Draft'), ('issued', 'Issued'), ('cancelled', 'Cancelled')],
        string='Status', default='draft', required=True, tracking=True)

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
    def action_issue(self):
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
                    "Fill the following before issuing the T.C.:\n- %s",
                    "\n- ".join(missing)))
            if rec.leaving_date and rec.admission_date and rec.leaving_date < rec.admission_date:
                raise UserError(_("Date of leaving cannot be earlier than date of admission."))
            rec.state = 'issued'
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        return True

    def action_print_tc(self):
        self.ensure_one()
        return self.env.ref(
            'ala_education_tc.action_report_transfer_certificate').report_action(self)

    def action_print_blank(self):
        return self.env.ref(
            'ala_education_tc.action_report_transfer_certificate_blank').report_action(self)
