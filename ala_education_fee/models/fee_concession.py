# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StudentFeeConcession(models.Model):
    _name = "ala.student.fee.concession"
    _description = "Student Fee Concession"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'

    student_id = fields.Many2one( "ala.education.student", required=True)
    student_fee_id = fields.Many2one( "ala.student.fees", readonly=True)
    date = fields.Date('Date', default=fields.Date.today, copy=False)
    class_division_id = fields.Many2one('ala.education.class.division', string="Division",
                                        help="Class of the student")
    concession_line_ids = fields.One2many('ala.student.fee.concession.line', 'concession_id', 'Concession Lines')
    # concession_type = fields.Selection([('admission', 'Admission'),('monthly', 'Monthly'), ], required=True)
    old_admission_fee = fields.Float('Current Admission Fee', default=False, readonly=True)
    concession_amount = fields.Float('Concession Given', default=False, tracking=True)
    last_ad_fee = fields.Float('Final Amount', default=False, tracking=True)
    old_monthly_fee = fields.Float('Current Monthly Fee', default=False,  readonly=True)
    monthly_concession_amount = fields.Float('Monthly Concession Given', default=False, tracking=True)
    last_monthly_fee = fields.Float('Amount Per Month', default=False, tracking=True)

    ad_concession_value = fields.Float('Admission Concession Value', required=False, tracking=True)
    monthly_concession_value = fields.Float(required=False, tracking=True)
    total_concession_amount = fields.Float( compute="_compute_total_concession",  store=True )
    state = fields.Selection([('draft', 'Draft'),('to_approve', 'To Approve'),('approved', 'Approved'),('reject', 'Rejected')], default='draft', tracking=True)
    academic_year_id = fields.Many2one(
        'ala.education.academic.year',
        string="Academic Year",
        readonly=True,
        default=lambda self: self._get_default_academic_year()
    )
    unpaid_month_fee_count = fields.Integer('Unpaid Fee Count', copy=False)

    _sql_constraints = [
        (
            'unique_student_academic_year_id',
            'unique(student_id, academic_year_id)',
            'A concession already exists for this student in the selected Academic Year.'
        )
    ]

    @api.model
    def _get_default_academic_year(self):
        return self.env['ala.education.academic.year'].search([('enable', '=', True)], limit=1)


    @api.onchange('concession_amount', 'monthly_concession_amount')
    def _onchange_new_admission_fee(self):
        for rec in self:
            if rec.old_admission_fee and rec.concession_amount:
                rec.last_ad_fee = rec.old_admission_fee - rec.concession_amount
            else:
                rec.last_ad_fee = 0.0
            if rec.old_monthly_fee and rec.monthly_concession_amount:
                rec.last_monthly_fee = rec.old_monthly_fee - rec.monthly_concession_amount
            else:
                rec.last_monthly_fee = 0.0
            if rec.concession_line_ids:
                admission_lines = rec.concession_line_ids.filtered(lambda l: l.fee_type == 're_admission')
                for line in admission_lines:
                    line.concession_amount = rec.concession_amount

                # Monthly
                monthly_lines = rec.concession_line_ids.filtered(lambda l: l.fee_type == 'monthly'  )
                for line in monthly_lines:
                    line.concession_amount = rec.monthly_concession_amount

            rec.ad_concession_value = rec.concession_amount
            rec.monthly_concession_value = rec.monthly_concession_amount * rec.unpaid_month_fee_count
            rec.total_concession_amount = rec.ad_concession_value + rec.monthly_concession_value

    def action_view_student_fees(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fee Lines',
            'res_model': 'ala.student.fees',
            'view_mode': 'form',
            'res_id': self.student_fee_id.id,
            'target': 'current',
        }


    @api.onchange('student_id')
    def _onchange_student_cons_id(self):
        if not self.student_id:
            return
        self.class_division_id = self.student_id.class_division_id.id
        student_fee = self.env['ala.student.fees'].search([ ('student_id', '=', self.student_id.id), ('academic_year_id', '=', self.academic_year_id.id)], limit=1)
        print('DDDDDDDDDDDDDDDDDDDDD',self.student_id, self.academic_year_id)
        print('DDDDDDDDDDDDDDDDDDDDD---------------',student_fee)
        # ✅ Raise error if no fee found
        if not student_fee:
            raise ValidationError("There are no fees found for this student in the selected Academic Year." )
        lines = []
        self.concession_line_ids = [fields.Command.clear()]
        self.student_fee_id = student_fee.id
        # Admission Fee
        admission_fee = student_fee.fee_line_ids.filtered(lambda fee_line: fee_line.fee_type == 're_admission' and fee_line.payment_status != 'paid')
        print('FFFFFFFFFFFFFFF',admission_fee,student_fee)
        if admission_fee:
            self.old_admission_fee = admission_fee.amount
            lines.append((0, 0, {
                'stu_fee_line_id': admission_fee.id,
                'student_id': admission_fee.student_id.id,
                'product_id': admission_fee.product_id.id,
                'amount': admission_fee.amount,
                'concession_amount': admission_fee.concession_amount,
                'amount_to_paid': admission_fee.amount_to_paid,
                'fee_type': admission_fee.fee_type,
                'payment_status': admission_fee.payment_status,
            }))

        # Monthly Fees
        monthly_fees = student_fee.fee_line_ids.filtered(lambda fee_line: fee_line.fee_type == 'monthly' and fee_line.payment_status != 'paid' )

        if monthly_fees:
            self.old_monthly_fee = monthly_fees[0].amount
            self.unpaid_month_fee_count = len(monthly_fees)
            for month in monthly_fees:
                lines.append((0, 0, {
                    'stu_fee_line_id': month.id,
                    'student_id': month.student_id.id,
                    'product_id': month.product_id.id,
                    'amount': month.amount,
                    'concession_amount': month.concession_amount,
                    'amount_to_paid': month.amount_to_paid,
                    'fee_type': month.fee_type,
                    'payment_status': month.payment_status,
                }))

        self.concession_line_ids = lines
        if not self.concession_line_ids:
            raise ValidationError("No more fees found for paying fees All fees were paid already.")

    def _compute_total_concession(self):
        for rec in self:
            print('dddddddddddddddd')

    def action_confirm(self):
        for rec in self:
            rec.state = 'to_approve'

    def action_approve(self):
        for rec in self:
            rec.student_fee_id.conseesion_id = rec.id
            for line in rec.concession_line_ids:
                line.stu_fee_line_id.concession_amount = line.concession_amount
            rec.state = 'approved'

    def action_reset(self):
        for rec in self:
            for line in rec.concession_line_ids:
                if line.stu_fee_line_id.payment_status == 'paid' :
                    raise ValidationError("Fees status already set to paid with this values. ")
                line.concession_amount = 0
                line.stu_fee_line_id.concession_amount = 0
                rec.concession_amount = 0
                rec.monthly_concession_value = 0
            rec.state = 'draft'

    def action_reject(self):
        for rec in self:
            for line in rec.concession_line_ids:
                if line.stu_fee_line_id.payment_status == 'paid' :
                    raise ValidationError("Fees status already set to paid with this values. ")
                line.concession_amount = 0
                line.stu_fee_line_id.concession_amount = 0
                rec.concession_amount = 0
                rec.monthly_concession_value = 0
            rec.state = 'reject'


class StudentFeeConcessionLine(models.Model):
    _name = 'ala.student.fee.concession.line'
    _description = 'Student Fee Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'product_id'

    concession_id = fields.Many2one('ala.student.fee.concession', required=False, ondelete='cascade',index=True)
    stu_fee_line_id = fields.Many2one('ala.student.fee.line', required=False, ondelete='cascade',index=True)
    student_id = fields.Many2one('ala.education.student', 'Student',store=True,index=True)
    product_id = fields.Many2one('product.product', string='Fee', copy=True,
                                 required=False,
                                 help='Fee Type of fee structure', domain=[('type', '=', 'service')])
    amount = fields.Float('Fees Amount', copy=False)
    concession_amount = fields.Float('Concession Amount', copy=False)
    amount_to_paid = fields.Float(
        'Amount Payable',
        compute="_compute_amount_to_paid",
        store=True
    )
    payment_status = fields.Selection([
        ('upcoming', 'Upcoming'),
        ('unpaid', 'Un Paid'),
        ('over_due', 'Over Due'),
        ('paid', 'Paid')], string='Payment Status', copy=False, default='upcoming' )

    fee_type = fields.Selection([
        ('admission', 'Admission'),
        ('re_admission', 'Re-Admission'),
        ('monthly', 'Monthly'),
        ('other', 'Others')], string='Fee Type', required=True, copy=False)


class EducationStudent(models.Model):
    _inherit = "ala.education.student"
    concession_ids = fields.One2many( "ala.student.fee.concession",  "student_id",  string="Fee Concessions" )

    def action_view_student_consessions(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Concessions',
            'res_model': 'ala.student.fee.concession',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {
                'default_student_id': self.id,
            },
            'target': 'current',
        }


