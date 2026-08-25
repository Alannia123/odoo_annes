# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
import logging
_logger = logging.getLogger(__name__)


class EducationFeeStructure(models.Model):
    """Creating model 'ala.education.fee.structure'"""
    _name = 'ala.education.fee.structure'
    _description = 'Education Fee Structure'
    _rec_name = 'fee_structure_name'

    @api.depends('fee_type_ids.fee_amount')
    def compute_total(self):
        for rec in self:
            rec.amount_total = sum(line.fee_amount for line in rec.fee_type_ids)

    company_currency_id = fields.Many2one('res.currency',
                                          string='Company Currency',
                                          compute='get_company_id',
                                          readonly=True, related_sudo=False,
                                          help='Company currency')
    fee_structure_name = fields.Char(string='Name', required=True,
                                     help='Name of fee structure')
    fee_type_ids = fields.One2many('ala.education.fee.structure.lines',
                                   'fee_structure_id',
                                   string='Fee Types', help='Specify the '
                                                            'fee types.')
    comment = fields.Text(string='Additional Information',
                          help="Additional information regarding the fee"
                               " structure")
    academic_year_id = fields.Many2one('ala.education.academic.year',
                                       string='Academic Year', required=True,default=lambda self: self._get_default_academic_year() ,
                                       help='Mention the academic year.')
    amount_total = fields.Float(string='Amount',
                                currency_field='company_currency_id',
                                required=True, compute='compute_total',
                                help='Total amount')
    class_ids = fields.Many2many('ala.education.class', string="Applied Classes")



    @api.model
    def _get_default_academic_year(self):
        return self.env['ala.education.academic.year'].search(
            [('enable', '=', True)],
            limit=1
        ).id



    def action_create_student_fees(self):

        StudentFees = self.env['ala.student.fees']
        Student = self.env['ala.education.student']

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for structure in self:

            if not structure.class_ids:
                raise UserError(_("Please assign classes in the fee structure."))

            # Get all students in selected classes
            students = Student.search([
                ('class_division_id.class_id', 'in', structure.class_ids.ids),
                ('class_division_id.academic_year_id', '=', structure.academic_year_id.id),
                ('tc_issued', '=', False),
                ('drop_out', '=', False),
            ])

            for student in students:

                    # Check existing student fees for same academic year
                    existing_fee = StudentFees.search([
                        ('student_id', '=', student.id),
                        ('academic_year_id', '=', structure.academic_year_id.id)
                    ], limit=1)

                    if existing_fee:

                        # Check if any line is paid
                        paid_lines = existing_fee.fee_line_ids.filtered(
                            lambda l: l.payment_status == 'paid'
                        )

                        # If any paid lines → skip this student
                        if paid_lines:
                            skipped_count += 1
                            continue

                        # No paid lines → clear existing lines
                        existing_fee.write({
                            'fee_line_ids': [(5, 0, 0)]
                        })

                        student_fee = existing_fee
                        updated_count += 1
                        existing_fee._get_overall_payment_state()
                        existing_fee.compute_total()

                    else:
                        # Create new student fees record
                        student_fee = StudentFees.create({
                            'student_id': student.id,
                            'name': f"{student.name} - {student.register_no}",
                            'register_number': student.register_no,
                            'student_division_id': student.class_division_id.id,
                            'fee_structure_id': structure.id,
                            'academic_year_id': structure.academic_year_id.id,
                            'edu_start_date': structure.academic_year_id.ay_start_date,
                            'edu_end_date': structure.academic_year_id.ay_end_date,
                        })
                        created_count += 1

                    # Prepare new fee lines
                    lines = []
                    student_type = student.student_new_old

                    for fee in structure.fee_type_ids:

                        # Skip based on student type
                        if student_type == 'new' and fee.fee_type == 're_admission':
                            continue

                        if student_type == 'old' and fee.fee_type == 'admission':
                            continue

                        lines.append((0, 0, {
                            'product_id': fee.product_id.id,
                            'fee_description': fee.fee_description,
                            'amount': fee.fee_amount,
                            'amount_to_paid': fee.fee_amount,
                            'fee_type': fee.fee_type,
                            'overdue_date': fee.due_date,
                            'reminder_date': fee.reminder_date,
                            'monthly_fee': fee.monthly_fee,
                        }))

                    # Assign fresh lines
                    student_fee.write({
                        'fee_line_ids': lines
                    })
                    student_fee._get_overall_payment_state()
                    student_fee.compute_total()

        # Optional: Show summary message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Student Fees Generation Completed"),
                'message': _(
                    f"Created: {created_count}\n"
                    f"Updated: {updated_count}\n"
                    f"Skipped (paid exists): {skipped_count}"
                ),
                'sticky': False,
            }
        }


class EducationFeeStructureLines(models.Model):
    """Creating model 'ala.education.fee.structure.lines'"""
    _name = 'ala.education.fee.structure.lines'
    _description = 'Education Fee Structure Lines'

    fee_structure_id = fields.Many2one('ala.education.fee.structure', 'Fee Structure')
    product_id = fields.Many2one('product.product', string='Fee', copy=True,
                                  required=True,
                                  help='Fee Type of fee structure', domain=[('type', '=', 'service')])
    fee_amount = fields.Float('Amount', required=True,
                              help='Corresponding fee amount.',  readonly=False )
    payment_type = fields.Selection([
        ('onetime', 'One Time'),
        ('permonth', 'Per Month'),
        ('peryear', 'Per Year'),
        ('sixmonth', '6 Months'),
        ('threemonth', '3 Months')
    ], string='Payment Type', default='onetime',
        help='Payment type describe how much a payment effective Like,'
             ' bus fee per month is 30 dollar, sports fee per year'
             ' is 40 dollar, etc')
    fee_type = fields.Selection([
        ('admission', 'Admission'),
        ('re_admission', 'Re-Admission'),
        ('monthly', 'Monthly'),
        ('other', 'Others')  ], string='Fee Type', required=True, copy=False)
    fee_description = fields.Text('Description',
                                  related='product_id.description_sale',
                                  help='Give the fee description.', copy=True,store=True, readonly=False)
    reminder_date = fields.Date('Reminder Date', required=True, copy=True)
    due_date = fields.Date('Due Date', required=True, copy=True)
    monthly_fee = fields.Boolean('Is monthly?', copy=False)

    # ------------------------------------------------------------------
    # Bulk Pay / Unpay for all students of this structure's academic year
    # ------------------------------------------------------------------

    #: students processed between two intermediate commits when the caller
    #: explicitly opts in via context (``ala_bulk_commit=True``). Never
    #: commits by default -- see action_pay_all_students docstring.
    _BULK_COMMIT_EVERY = 50

    def _assert_saved(self):
        """Buttons inside a one2many row can fire on an unsaved line."""
        for rec in self:
            if not rec._origin.id:
                raise UserError(_("Please save the fee structure before "
                                  "using Pay All / Unpay All."))

    def _assert_bulk_rights(self):
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_("Only an Accounting Manager can run "
                              "Pay All / Unpay All."))

    def _get_student_fee_line_domain(self):
        """Student fee lines generated from THIS structure line, limited to
        the structure's academic year and applied classes."""
        self.ensure_one()
        structure = self.fee_structure_id

        if not structure.academic_year_id:
            raise UserError(_("Set the Academic Year on the fee structure first."))
        if not structure.class_ids:
            raise UserError(_("Assign Applied Classes on the fee structure first."))
        if not self.product_id:
            raise UserError(_("Set the Fee product on this line first."))

        return [
            ('academic_year_id', '=', structure.academic_year_id.id),
            ('product_id', '=', self.product_id.id),
            ('fee_type', '=', self.fee_type),
            ('student_division_id.class_id', 'in', structure.class_ids.ids),
            ('student_id.tc_issued', '=', False),
            ('student_id.drop_out', '=', False),
        ]

    def _bulk_env(self):
        """Context for mass accounting writes.

        ala.student.fees and ala.student.fee.line both inherit mail.thread and
        carry tracked monetary fields. Without this, a 900-student run writes
        thousands of mail.message / mail.tracking.value rows and roughly
        doubles the runtime.
        """
        return self.with_context(
            tracking_disable=True,
            mail_create_nolog=True,
            mail_notrack=True,
            mail_auto_subscribe_no_notify=True,
            ala_bulk_skip_line_log=True,
        ).env

    def _resolve_bulk_journal(self, payment_mode):
        journal_type = {
            'cash': 'cash',
            'bank': 'bank',
            'online': 'bank',
        }.get(payment_mode)
        if not journal_type:
            raise UserError(_("Unsupported payment mode %s.", payment_mode))

        journal = self.env['account.journal'].search([
            ('type', '=', journal_type),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not journal:
            raise UserError(_(
                "No %(type)s journal configured for company %(company)s.",
                type=journal_type, company=self.env.company.display_name))
        if not journal.inbound_payment_method_line_ids:
            raise UserError(_(
                "Journal %s has no inbound payment method line; the payment "
                "cannot be created.", journal.display_name))
        return journal

    def _group_by_student_fee(self, lines):
        """{ala.student.fees record: ala.student.fee.line recordset}.

        The invoice is per student -- action_create_invoice() refuses a mixed
        recordset -- so the batch has to be sliced this way.
        """
        FeeLine = lines.browse()
        grouped = defaultdict(lambda: FeeLine)
        for line in lines:
            grouped[line.student_fee_id] |= line
        return grouped

    def _notify_bulk_result(self, title, message, warning=False):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': 'warning' if warning else 'success',
                'sticky': True,
            },
        }

    # ------------------------------------------------------------------
    # PAY ALL
    # ------------------------------------------------------------------

    def action_pay_all_students(self, payment_mode=None, payment_date=None):
        """Settle this fee for every active student of the structure's
        academic year: one posted customer invoice + one posted payment +
        reconciliation per student, exactly like action_pay_selected_fees().

        Each student is wrapped in its own SQL savepoint, so a student with a
        broken configuration (no partner, locked period, ...) is reported and
        skipped instead of rolling back the whole run.

        Payment mode / date default to cash / today and can be overridden
        through the context keys ``bulk_payment_mode`` / ``bulk_payment_date``.
        """
        self.ensure_one()
        self._assert_saved()
        self._assert_bulk_rights()

        ctx = self.env.context
        payment_mode = payment_mode or ctx.get('bulk_payment_mode') or 'cash'
        payment_date = (payment_date or ctx.get('bulk_payment_date')
                        or fields.Date.context_today(self))
        journal = self._resolve_bulk_journal(payment_mode)

        env = self._bulk_env()
        FeeLine = env['ala.student.fee.line']
        lines = FeeLine.search(self._get_student_fee_line_domain())

        # A line that already carries an invoice must never be re-invoiced,
        # even if its status drifted away from 'paid'.
        todo = lines.filtered(lambda l: l.payment_status != 'paid' and not l.invoice_id)
        already = len(lines) - len(todo)

        if not todo:
            return self._notify_bulk_result(
                _("Nothing to Pay"),
                _("All %s student fee lines for this fee are already settled.",
                  len(lines)))

        grouped = self._group_by_student_fee(todo)
        commit_every = self._BULK_COMMIT_EVERY if ctx.get('ala_bulk_commit') else 0

        paid_lines = zero_lines = failed_lines = 0
        invoices_created = 0
        failures = []

        for seq, (student_fee, fee_lines) in enumerate(grouped.items(), start=1):
            partner = student_fee.student_id.partner_id
            if not partner:
                failed_lines += len(fee_lines)
                failures.append(_("%s: student has no linked contact",
                                  student_fee.display_name))
                continue

            payable = sum(
                l.amount - l.concession_amount + l.fine_amount for l in fee_lines)

            try:
                with self.env.cr.savepoint():
                    if float_compare(payable, 0.0,
                                     precision_rounding=student_fee.company_currency_id.rounding or 0.01) <= 0:
                        # Fully waived / zero fee: no accounting entry is
                        # possible (a 0.00 payment cannot be posted), so the
                        # line is closed without an invoice.
                        fee_lines.write({
                            'payment_mode': payment_mode,
                            'journal_id': journal.id,
                            'payment_status': 'paid',
                            'select_for_invoice': False,
                        })
                        zero_lines += len(fee_lines)
                    else:
                        fee_lines.write({
                            'payment_mode': payment_mode,
                            'journal_id': journal.id,
                            'select_for_invoice': False,
                        })
                        FeeLine.action_create_invoice(fee_lines.ids, payment_date)
                        invoices_created += 1
                        paid_lines += len(fee_lines)

                    student_fee.last_fee_line_id = fee_lines[0].id
                    student_fee.update_fee_status_students()
            except Exception as err:
                failed_lines += len(fee_lines)
                failures.append("%s: %s" % (student_fee.display_name, err))
                _logger.exception(
                    "Bulk PAY failed for student fee %s (structure line %s)",
                    student_fee.id, self.id)
                continue

            if commit_every and seq % commit_every == 0:
                self.env.cr.commit()  # noqa: E8102 - opt-in, see docstring

        _logger.info(
            "Bulk PAY structure line %s (%s / AY %s) by %s: %s invoices, "
            "%s lines settled, %s zero-value, %s already paid, %s failed",
            self.id, self.product_id.display_name,
            self.fee_structure_id.academic_year_id.display_name,
            self.env.user.login, invoices_created, paid_lines, zero_lines,
            already, failed_lines)

        message = _(
            "Students processed: %(students)s\n"
            "Invoices created and settled: %(invoices)s\n"
            "Fee lines paid: %(paid)s\n"
            "Zero-value lines closed without invoice: %(zero)s\n"
            "Already settled (skipped): %(already)s\n"
            "Failed: %(failed)s",
            students=len(grouped), invoices=invoices_created, paid=paid_lines,
            zero=zero_lines, already=already, failed=failed_lines)

        if failures:
            message += _("\n\nFirst errors:\n%s", "\n".join(failures[:10]))

        return self._notify_bulk_result(
            _("Bulk Payment Completed"), message, warning=bool(failures))

    # ------------------------------------------------------------------
    # UNPAY ALL
    # ------------------------------------------------------------------

    def action_unpay_all_students(self):
        """Reverse this fee for every active student of the academic year:
        cancel the linked invoice and its payment, unlink the invoice from the
        fee lines and put them back on their date-based status.

        Delegates to ala.student.fee.line.reset_payment_to_draft() so the
        accounting behaviour is identical to the single-line reset (sibling
        lines sharing a monthly invoice are pulled in, payments that also
        settle other invoices are left alone).

        Hash-locked invoices raise inside reset_payment_to_draft(); that
        student is rolled back to its savepoint, reported, and the run
        continues.
        """
        self.ensure_one()
        self._assert_saved()
        self._assert_bulk_rights()

        env = self._bulk_env()
        FeeLine = env['ala.student.fee.line']
        lines = FeeLine.search(self._get_student_fee_line_domain())
        paid = lines.filtered(lambda l: l.payment_status == 'paid' or l.invoice_id)

        if not paid:
            return self._notify_bulk_result(
                _("Nothing to Revert"),
                _("None of the %s student fee lines for this fee is settled.",
                  len(lines)))

        grouped = self._group_by_student_fee(paid)
        commit_every = (self._BULK_COMMIT_EVERY
                        if self.env.context.get('ala_bulk_commit') else 0)

        reverted_lines = failed_lines = 0
        cancelled_invoices = []
        skipped_payments = 0
        failures = []

        for seq, (student_fee, fee_lines) in enumerate(grouped.items(), start=1):
            try:
                with self.env.cr.savepoint():
                    result = fee_lines.reset_payment_to_draft()
                reverted_lines += result.get('reset_count', 0)
                cancelled_invoices += result.get('invoices', [])
                skipped_payments += result.get('skipped_payments', 0)
            except Exception as err:
                failed_lines += len(fee_lines)
                failures.append("%s: %s" % (student_fee.display_name, err))
                _logger.exception(
                    "Bulk UNPAY failed for student fee %s (structure line %s)",
                    student_fee.id, self.id)
                continue

            if commit_every and seq % commit_every == 0:
                self.env.cr.commit()  # noqa: E8102 - opt-in, see docstring

        _logger.warning(
            "Bulk UNPAY structure line %s (%s / AY %s) by %s: %s lines "
            "reverted, %s invoices cancelled, %s payments left untouched, "
            "%s lines failed",
            self.id, self.product_id.display_name,
            self.fee_structure_id.academic_year_id.display_name,
            self.env.user.login, reverted_lines, len(cancelled_invoices),
            skipped_payments, failed_lines)

        # reset_payment_to_draft() also reverts sibling lines that shared a
        # monthly invoice, so the reverted count can exceed the selection.
        collateral = max(reverted_lines - len(paid), 0)

        message = _(
            "Students processed: %(students)s\n"
            "Invoices cancelled: %(invoices)s\n"
            "Fee lines reverted: %(reverted)s\n"
            "Sibling lines reverted (shared invoice): %(collateral)s\n"
            "Payments left untouched (shared with other invoices): %(skipped)s\n"
            "Failed: %(failed)s",
            students=len(grouped), invoices=len(cancelled_invoices),
            reverted=reverted_lines, collateral=collateral,
            skipped=skipped_payments, failed=failed_lines)

        if failures:
            message += _("\n\nFirst errors:\n%s", "\n".join(failures[:10]))

        return self._notify_bulk_result(
            _("Bulk Reversal Completed"), message, warning=bool(failures))