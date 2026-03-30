from odoo import models, fields, api
from datetime import date

class ApplicationFeeReceipt(models.Model):
    _name = 'ala.application.fee.receipt'
    _description = 'Application Fee Receipt'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char("Application No.", readonly=True)
    student_name = fields.Char("Student Name", required=True)
    class_id = fields.Many2one('ala.education.class', string='Class',
                               help="Class of the attendance", tracking=True)
    academic_year_id = fields.Many2one(
        'ala.education.academic.year',
        string='Academic Year',
        domain=[('next_academic_year', '=', True)],
        default=lambda self: self.env['ala.education.academic.year'].search([('next_academic_year', '=', True)], limit=1),
    )

    amount = fields.Monetary("Fee Amount", default=300, currency_field='currency_id',tracking=True)
    date = fields.Date(default=lambda self: fields.Date.today())


    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('cancel', 'Cancel'),
    ], default='draft', tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='School',
        default=lambda self: self.env.company,
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string='Currency',
               required=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        seq_obj = self.env['ir.sequence']
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') in ('New', '/'):
                vals['name'] = seq_obj.next_by_code('application.fee.seq') or '/'
        return super().create(vals_list)


    def reset_to_draft(self):
        self.write({'state' : 'draft'})


    def action_set_cancel(self):
        self.write({'state' : 'cancel'})

    def action_pay_and_print(self):
        """Mark as paid and return PDF report"""
        for rec in self:
            rec.state = 'paid'
        return self.env.ref('ala_education_fee.receipt_report_action').report_action(self)

    def action_print_receipt(self):
        """Mark as paid and return PDF report"""
        return self.env.ref('ala_education_fee.receipt_report_action').report_action(self)

