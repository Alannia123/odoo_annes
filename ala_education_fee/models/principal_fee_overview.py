# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StudentFeeLine(models.Model):
    _inherit = 'student.fee.line'

    @api.model
    def _principal_overview_domain(self, date_from=False, date_to=False,
                                   payment_mode=False):
        # Data is taken strictly by invoice date, per requirement.
        domain = []
        if date_from:
            domain.append(('invoice_date', '>=', date_from))
        if date_to:
            domain.append(('invoice_date', '<=', date_to))
        if payment_mode:
            domain.append(('payment_mode', '=', payment_mode))
        # Only count lines that actually have an invoice date.
        domain.append(('invoice_date', '!=', False))
        return domain

    @api.model
    def get_principal_fee_overview(self, date_from=False, date_to=False,
                                   payment_mode=False):
        """Single source of truth for the principal overview.
        Reused by the OWL grid, the XLSX export and the PDF so the figures
        on screen and in the files can never diverge.
        """
        domain = self._principal_overview_domain(
            date_from or False, date_to or False, payment_mode or False,
        )
        lines = self.search(
            domain, order='invoice_date asc, register_number asc, id asc'
        )

        mode_labels = dict(self._fields['payment_mode'].selection)

        rows = []
        for line in lines:
            rows.append({
                'id': line.id,
                'student': line.student_id.display_name or '',
                'division': line.student_division_id.display_name or '',
                'roll_no': line.student_id.roll_no or '',
                'register_number': line.register_number or '',
                'payment_mode': mode_labels.get(line.payment_mode, ''),
                'amount': line.amount,
                'invoice_date': fields.Date.to_string(line.invoice_date) or '',
            })

        totals = {
            'amount': sum(lines.mapped('amount')),
            'count': len(lines),
        }
        return {'lines': rows, 'totals': totals}