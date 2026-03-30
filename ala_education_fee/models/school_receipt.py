from odoo import models, fields, api
from odoo.exceptions import UserError

class SchoolReceipt(models.Model):
    _name = 'ala.school.receipt'
    _description = 'School Receipt'
    _order = 'id desc'

    name = fields.Char("Receipt No.", default="New", readonly=True)
    date = fields.Date("Date", default=fields.Date.context_today)

    student_name = fields.Char("Received From", required=True)
    student_class = fields.Char("Class", required=True)
    session = fields.Char("Session", default="2025-2026")

    line_ids = fields.One2many(
        'ala.school.receipt.line',
        'receipt_id',
        string="Fee Lines"
    )

    total_amount = fields.Float(
        "Total Amount",
        compute='_compute_total',
        store=True
    )

    amount_words = fields.Char("Amount in Words")
    state = fields.Selection(
        [('draft','Draft'), ('confirmed','Confirmed')],
        default='draft'
    )

    move_id = fields.Many2one("account.move", string="Journal Entry", readonly=True)

    journal_id = fields.Many2one(
        'account.journal',
        string="Journal",
        required=True,
        default=lambda self: self.env['account.journal'].search([('type','=','cash')], limit=1)
    )

    @api.depends('line_ids.amount')
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped('amount'))

    @api.model
    def create(self, vals):
        if vals.get('name') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('ala.school.receipt')
        return super().create(vals)

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError("Please add at least one fee line.")

            if rec.total_amount <= 0:
                raise UserError("Total amount must be greater than zero.")

            debit_line = {
                'name': f"Receipt {rec.name} – {rec.student_name}",
                'account_id': rec.journal_id.default_account_id.id,
                'debit': rec.total_amount,
                'credit': 0,
            }

            credit_lines = []
            for line in rec.line_ids:
                credit_lines.append((0, 0, {
                    'name': line.description,
                    'account_id': line.account_id.id,
                    'credit': line.amount,
                    'debit': 0,
                }))

            move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': rec.date,
                'journal_id': rec.journal_id.id,
                'ref': rec.name,
                'line_ids': [(0, 0, debit_line)] + credit_lines
            })

            move.action_post()
            rec.move_id = move.id
            rec.state = 'confirmed'


class SchoolReceiptLine(models.Model):
    _name = 'ala.school.receipt.line'
    _description = "Receipt Fee Line"

    receipt_id = fields.Many2one('ala.school.receipt', ondelete='cascade')
    description = fields.Char("Description", required=True)
    amount = fields.Float("Amount", required=True)

    account_id = fields.Many2one(
        'account.account',
        string="Income Account",
        required=True,
        help="Income account for this fee item.",
    )
