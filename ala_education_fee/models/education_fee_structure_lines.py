# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError



class EducationFeeStructureLines(models.Model):
    """Creating model 'ala.education.fee.structure.lines'"""
    _name = 'ala.education.fee.structure.lines'
    _description = 'Education Fee Structure Lines'

    @api.onchange('fee_type_id')
    def _onchange_fee_type(self):
        """Function to return Fee type ids"""
        return {
            'domain': {
                'fee_type_id': [('category_id', '=',
                                 self.fee_structure_id.category_id.id)]
            }
        }

    fee_type_id = fields.Many2one('ala.education.fee.type', string='Fee',
                                  required=True,
                                  help='Fee Type of fee structure')
    fee_structure_id = fields.Many2one('ala.education.fee.structure',
                                       string='Fee Structure',
                                       ondelete='cascade', index=True,
                                       help='Education fee structure of lines')
    fee_amount = fields.Float('Amount', required=True,
                              related='fee_type_id.lst_price',
                              help='Corresponding fee amount.')
    payment_type = fields.Selection([
        ('onetime', 'One Time'),
        ('permonth', 'Per Month'),
        ('peryear', 'Per Year'),
        ('sixmonth', '6 Months'),
        ('threemonth', '3 Months')
    ], string='Payment Type',
        help='Payment type describe how much a payment effective Like,'
             ' bus fee per month is 30 dollar, sports fee per year'
             ' is 40 dollar, etc')
    interval = fields.Char(related="fee_type_id.interval", string="Interval",
                           help='Specify the interval.')
    fee_description = fields.Text('Description',
                                  related='fee_type_id.description_sale',
                                  help='Give the fee description.')
    monthly_fee = fields.Boolean('Is monthly?', copy=False)


    # ------------------------------------------------------------------
    # Bulk Pay / Unpay for all students of this structure's academic year
    # ------------------------------------------------------------------

    def _assert_saved(self):
        """Buttons inside a one2many row can fire on an unsaved line."""
        for rec in self:
            if not rec._origin.id:
                raise UserError(_("Please save the fee structure before "
                                  "using Pay All / Unpay All."))

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

    def _notify_bulk_result(self, title, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': False,
            },
        }

    def action_pay_all_students(self):
        """Mark this fee as PAID for every active student of the structure's
        academic year. Does NOT create invoices or payments."""
        self.ensure_one()
        self._assert_saved()

        FeeLine = self.env['ala.student.fee.line']
        lines = FeeLine.search(self._get_student_fee_line_domain())
        to_pay = lines.filtered(lambda l: l.payment_status != 'paid')

        if to_pay:
            to_pay.write({'payment_status': 'paid'})
            to_pay.student_fee_id.update_fee_status_students()

        _logger.info(
            "Bulk PAY on structure line %s (%s / AY %s): %s of %s lines marked paid by %s",
            self.id, self.product_id.display_name,
            self.fee_structure_id.academic_year_id.display_name,
            len(to_pay), len(lines), self.env.user.login)

        return self._notify_bulk_result(
            _("Fees Marked Paid"),
            _("%(done)s of %(total)s student fee lines marked as Paid.\n"
              "Already paid: %(skipped)s",
              done=len(to_pay), total=len(lines),
              skipped=len(lines) - len(to_pay)))

    def action_unpay_all_students(self):
        """Revert this fee to its date-based status for every active student
        of the structure's academic year. Lines already settled through an
        invoice are skipped — they represent real accounting entries."""
        self.ensure_one()
        self._assert_saved()

        FeeLine = self.env['ala.student.fee.line']
        lines = FeeLine.search(self._get_student_fee_line_domain())
        paid = lines.filtered(lambda l: l.payment_status == 'paid')

        settled = paid.filtered(lambda l: l.invoice_id)
        revertible = paid - settled

        today = fields.Date.context_today(self)
        buckets = {'over_due': FeeLine, 'unpaid': FeeLine, 'upcoming': FeeLine}

        for line in revertible:
            if line.overdue_date and line.overdue_date < today:
                status = 'over_due'
            elif line.reminder_date and line.reminder_date > today:
                status = 'upcoming'
            else:
                status = 'unpaid'
            buckets[status] |= line

        for status, recs in buckets.items():
            if recs:
                recs.write({'payment_status': status})

        if revertible:
            # drop stale "last paid line" pointers
            parents = revertible.student_fee_id
            stale = parents.filtered(lambda p: p.last_fee_line_id in revertible)
            if stale:
                stale.write({'last_fee_line_id': False})
            parents.update_fee_status_students()

        _logger.warning(
            "Bulk UNPAY on structure line %s (%s / AY %s): %s reverted, "
            "%s skipped (invoiced) by %s",
            self.id, self.product_id.display_name,
            self.fee_structure_id.academic_year_id.display_name,
            len(revertible), len(settled), self.env.user.login)

        return self._notify_bulk_result(
            _("Fees Reverted"),
            _("%(done)s student fee lines reverted to unpaid status.\n"
              "Skipped (already invoiced): %(skipped)s",
              done=len(revertible), skipped=len(settled)))
