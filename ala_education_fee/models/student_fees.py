from odoo import models, fields, api
from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)
import re

class StudentFees(models.Model):
    _name = 'ala.student.fees'
    _description = 'Student Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    register_number = fields.Char( string='Register Number', readonly=True, required=True)
    student_id = fields.Many2one('ala.education.student', 'Student', required=True)
    student_division_id = fields.Many2one('ala.education.class.division', string= 'Division', readonly=True)
    academic_year_id = fields.Many2one('ala.education.academic.year', readonly=True)
    edu_start_date = fields.Date('Start date', readonly=True)
    edu_end_date = fields.Date('End date', readonly=True)
    fee_line_ids = fields.One2many('ala.student.fee.line', 'student_fee_id', string="Fees")
    amount_total = fields.Monetary(string='Amount Payable',
                                currency_field='company_currency_id',
                                required=False, compute='compute_total',
                                help='Total amount')
    final_amount_total = fields.Monetary(string='Actual Amount Payable',
                                currency_field='company_currency_id',
                                required=False, compute='compute_total',tracking=True,
                                help='Total amount')
    amount_paid = fields.Monetary(string='Amount Paid',
                                currency_field='company_currency_id',
                                required=False, compute='compute_total',tracking=True,
                                help='Total amount')
    amount_unpaid = fields.Monetary(string='Amount Pending',
                                currency_field='company_currency_id',
                                required=False, compute='compute_total',
                                help='Amount Unpaid')
    amount_fine = fields.Monetary(string='Total Fine Amount',
                                currency_field='company_currency_id',
                                required=False, compute='compute_total',tracking=True,
                                help='Amount Unpaid')
    amount_due = fields.Monetary(string='Amount in OverDue',
                                currency_field='company_currency_id',
                                required=False, compute='compute_total',tracking=True,
                                help='Amount Due')
    amount_concession = fields.Monetary(string='Concession Given',
                                currency_field='company_currency_id',
                                required=False,tracking=True,
                                help='Amount Concession')
    amount_upcoming = fields.Monetary(string='Amount Upcoming',
                                currency_field='company_currency_id',
                                required=False, compute='compute_total',tracking=True,
                                help='Amount Due')
    comment = fields.Text(string='Additional Information',
                          help="Additional information regarding the fee"
                               " structure")
    company_id = fields.Many2one('res.company', 'Company', index=True,
        default=lambda self: self.env.company)
    company_currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id.id,
        required=True )
    fee_structure_id = fields.Many2one('ala.education.fee.structure', 'Fees Structure', readonly=True)
    non_edit = fields.Boolean('Non Edit')
    invoice_count = fields.Integer(string="Invoice Count", compute="_compute_invoice_count")
    fee_line_count = fields.Integer(string="Fee Lines Count", compute="_compute_fee_line_count")
    payment_status = fields.Selection([
        ('upcoming', 'Upcoming'),
        ('unpaid', 'Un Paid'),
        ('over_due', 'Over Due'),
        ('paid', 'Paid')], string='Payment Status', copy=False,store=True, tracking=True)
    overdue_fee_len = fields.Integer('Fee len')
    image_1920 = fields.Image('Image', copy=False)
    conseesion_id = fields.Many2one('ala.student.fee.concession', 'Consession', copy=False)
    last_fee_line_id = fields.Many2one('ala.student.fee.line', 'last Paid Fee Line', copy=False)

    def action_open_concession(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consession',
            'res_model': 'ala.student.fee.concession',
            'view_mode': 'form',
            'res_id': self.conseesion_id.id,
            'target': 'current',
        }

    @api.onchange('student_id')
    def _onchange_image_1920(self):
        if self.student_id:
            self.image_1920 = self.student_id.image_1920

    @api.model_create_multi
    def create(self, vals_list):
        student_model = self.env['ala.education.student']
        for vals in vals_list:
            if vals.get('student_id'):
                student = student_model.browse(vals['student_id'])
                vals['image_1920'] = student.image_1920
        return super().create(vals_list)

    def write(self, vals):
        if 'student_id' in vals:
            student = self.env['ala.education.student'].browse(vals['student_id'])
            for record in self:
                record.image_1920 = student.image_1920
            return super().write(vals)
        return super().write(vals)

    @api.depends('fee_line_ids.payment_status')
    def _get_overall_payment_state(self):
        for rec in self:
            un_paid = rec.fee_line_ids.filtered(lambda fee_line: fee_line.payment_status == 'unpaid')
            over_due = rec.fee_line_ids.filtered(lambda fee_line: fee_line.payment_status == 'over_due')
            upcoming = rec.fee_line_ids.filtered(lambda fee_line: fee_line.payment_status == 'upcoming')
            rec.overdue_fee_len = len(over_due)
            if over_due:
                rec.payment_status = 'over_due'
            elif un_paid:
                rec.payment_status = 'un_paid'
            elif upcoming:
                rec.payment_status = 'upcoming'
            else:
                rec.payment_status = 'paid'

    @api.constrains('student_id', 'academic_year_id')
    def _check_duplicate_student_fee(self):
        for rec in self:
            domain = [
                ('student_id', '=', rec.student_id.id),
                ('academic_year_id', '=', rec.academic_year_id.id)
            ]
            if self.search_count(domain) > 1:
                raise ValidationError("Fee for this student and academic year already exists.")

    @api.depends('fee_line_ids')
    def _compute_fee_line_count(self):
        for rec in self:
            rec.fee_line_count = len(rec.fee_line_ids)
            un_paid = rec.fee_line_ids.filtered(lambda fee_line: fee_line.payment_status == 'unpaid')
            over_due = rec.fee_line_ids.filtered(lambda fee_line: fee_line.payment_status == 'over_due')
            upcoming = rec.fee_line_ids.filtered(lambda fee_line: fee_line.payment_status == 'upcoming')
            rec.overdue_fee_len = len(over_due)
            if over_due:
                rec.payment_status = 'over_due'
            elif un_paid:
                rec.payment_status = 'unpaid'
            elif upcoming:
                rec.payment_status = 'upcoming'
            else:
                rec.payment_status = 'paid'

    def update_fee_status_students(self):
        for rec in self:
            un_paid = rec.fee_line_ids.filtered(lambda fee_line: fee_line.payment_status == 'unpaid')
            over_due = rec.fee_line_ids.filtered(lambda fee_line: fee_line.payment_status == 'over_due')
            upcoming = rec.fee_line_ids.filtered(lambda fee_line: fee_line.payment_status == 'upcoming')
            rec.overdue_fee_len = len(over_due)
            if over_due:
                rec.payment_status = 'over_due'
            elif un_paid:
                rec.payment_status = 'unpaid'
            elif upcoming:
                rec.payment_status = 'upcoming'
            else:
                rec.payment_status = 'paid'



    def _compute_invoice_count(self):
        for fee in self:
            fee.invoice_count = self.env['account.move'].search_count([
                ('student_fee_id', '=', fee.id),
                ('move_type', '=', 'out_invoice')
            ])

    def action_open_fee_lines_kanban(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fee Lines',
            'res_model': 'ala.student.fee.line',
            'view_mode': 'kanban,list,form',
            'domain': [('student_fee_id', '=', self.id)],
            'context': {'default_student_fee_id': self.id},
            'target': 'current',
        }

    def action_view_fee_invoice(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([
            ('student_fee_id', '=', self.id),
            ('move_type', '=', 'out_invoice')
        ])
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
        return action

    @api.depends('fee_line_ids', 'fee_line_ids.amount', 'fee_line_ids.payment_mode', 'fee_line_ids.invoice_id', 'fee_line_ids.amount', 'fee_line_ids.amount_to_paid')
    def compute_total(self):
        for rec in self:
            rec.amount_total = sum(line.amount for line in rec.fee_line_ids)
            rec.amount_fine = sum(line.fine_amount for line in rec.fee_line_ids)
            rec.amount_concession = sum(line.concession_amount for line in rec.fee_line_ids)
            rec.final_amount_total = sum(line.amount_to_paid for line in rec.fee_line_ids)
            rec.amount_paid = sum(line.amount_to_paid for line in rec.fee_line_ids.filtered(lambda r: r.payment_status == 'paid'))
            amount_unpaid = sum(line.amount_to_paid for line in rec.fee_line_ids.filtered(lambda r: r.payment_status == 'unpaid'))
            rec.amount_due = sum(line.amount_to_paid for line in rec.fee_line_ids.filtered(lambda r: r.payment_status == 'over_due'))
            rec.amount_upcoming = sum(line.amount_to_paid for line in rec.fee_line_ids.filtered(lambda r: r.payment_status == 'upcoming'))
            rec.amount_unpaid = amount_unpaid + rec.amount_due + rec.amount_upcoming
            paid_entries = rec.fee_line_ids.filtered(lambda r: r.payment_status == 'paid')
            if paid_entries:
                rec.non_edit = True

    # @api.model
    # def _get_default_academic_year(self):
    #     return self.env['ala.education.academic.year'].search(
    #         [('enable', '=', True)],
    #         limit=1
    #     ).id

    @api.onchange('student_id')
    def _onchange_assign_all_values(self):
        if not self.student_id:
            self.edu_end_date = False
            self.edu_start_date = False
            return

        self.name = f"{self.student_id.name} - {self.student_id.register_no}"
        self.register_number = self.student_id.register_no
        self.student_division_id = self.student_id.class_division_id.id

        fee_structure = self.env['ala.education.fee.structure'].search([
            ('class_ids', 'in', [self.student_id.class_division_id.class_id.id])], limit=1)

        if not fee_structure:
            raise UserError(_("Fee structure not found. Please check."))

        self.fee_structure_id = fee_structure
        self.academic_year_id = fee_structure.academic_year_id.id
        self.edu_start_date = fee_structure.academic_year_id.ay_start_date
        self.edu_end_date = fee_structure.academic_year_id.ay_end_date

        # Clear existing lines
        self.fee_line_ids = [fields.Command.clear()]

        lines = []
        student_type = self.student_id.student_new_old

        for fee in fee_structure.fee_type_ids:
            # NEW student
            if student_type == 'new' and fee.fee_type == 're_admission':
                continue
            # OLD student
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

        self.fee_line_ids = lines

    def action_create_invoice_and_payment(self):
        selected_lines = self.fee_line_ids.filtered(lambda l: l.select_for_invoice and l.payment_status != 'paid')
        if not selected_lines:
            raise ValidationError("No fee lines selected for Payment.")
        modes = selected_lines.mapped('payment_mode')
        if len(set(modes)) > 1:
            raise UserError("Selected lines must have the same payment mode.")

        student = selected_lines[0].student_id
        partner = student.partner_id
        journal = selected_lines[0].journal_id

        # Create ONE invoice with multiple lines
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'journal_id': journal.id,
            'student_fee_id': self.id,
            'invoice_line_ids': [],
        }

        for line in selected_lines:
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.fee_description,
                'quantity': 1,
                'price_unit': line.amount,
            }))
            line.select_for_invoice = False

        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()
        invoice.student_fee_id = self.id

        # Create ONE payment
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': partner.id,
            'amount': invoice.amount_total,
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'journal_id': journal.id,
        })
        payment.action_post()

        # Reconcile payment and invoice
        (payment.move_id.line_ids + invoice.line_ids).filtered(
            lambda l: l.account_id.account_type == 'asset_receivable').reconcile()

        # Mark all selected lines as paid and link invoice
        for line in selected_lines:
            line.invoice_id = invoice.id
            line.payment_status = 'paid'
            line.select_for_invoice = False  # Reset selection

    def unlink(self):
        for record in self:
            if record.non_edit:
                raise UserError(_("You cannot delete this student already made some payments."))
        return super(StudentFees, self).unlink()

class StudentFeeLine(models.Model):
    _name = 'ala.student.fee.line'
    _description = 'Student Fee Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'product_id'

    select_for_invoice = fields.Boolean('Select', default=False)
    student_fee_id = fields.Many2one('ala.student.fees', required=False, ondelete='cascade',index=True)
    register_number = fields.Char(related='student_fee_id.register_number', string='Register Number', readonly=True,store=True,index=True)
    student_id = fields.Many2one(related='student_fee_id.student_id', string= 'Student',store=True,index=True)
    student_division_id = fields.Many2one(related='student_fee_id.student_division_id', string='Division', readonly=True,store=True,index=True)
    academic_year_id = fields.Many2one(related='student_fee_id.academic_year_id', string='Academic year', readonly=True,store=True,index=True)
    product_id = fields.Many2one('product.product', string='Fee', copy=True,
                                 required=False,
                                 help='Fee Type of fee structure', domain=[('type', '=', 'service')])
    fee_description = fields.Text('Description',
                                  related='product_id.description_sale',
                                  help='Give the fee description.', copy=True, store=True, readonly=False)
    payment_mode = fields.Selection([
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('online', 'Online')], string='Payment Mode', copy=False, default='cash',index=True)
    journal_id = fields.Many2one('account.journal', 'Receive On', copy=False, default=lambda self: self.env['account.journal'].search([('type', '=', 'cash')], limit=1))
    amount = fields.Float('Fees Amount', copy=False)
    fine_amount = fields.Float('Fine Amount', copy=False)
    concession_amount = fields.Float('Concession Amount', copy=False)
    amount_to_paid = fields.Float(
        'Amount Payable',
        compute="_compute_amount_to_paid",
        store=True
    )
    invoice_id = fields.Many2one('account.move', string='Invoice',index=True)
    payment_status = fields.Selection([
        ('upcoming', 'Upcoming'),
        ('unpaid', 'Un Paid'),
        ('over_due', 'Over Due'),
        ('paid', 'Paid')], string='Payment Status', copy=False, default='upcoming' )
    overdue_date = fields.Date('Due Date', copy=False,index=True)
    reminder_date = fields.Date('Reminder Date', required=False, copy=True)
    # pay_status = fields.Boolean('Pay status?', compute="_compute_payment_status")
    fee_month_range = fields.Char('Fee Month Range', copy=False)
    monthly_fee = fields.Boolean('Is monthly?', copy=False)
    overdue_days = fields.Integer(
        string="Overdue Days",
        compute="_compute_overdue_days",
        store=False
    )
    fee_type = fields.Selection([
        ('admission', 'Admission'),
        ('re_admission', 'Re-Admission'),
        ('monthly', 'Monthly'),
        ('other', 'Others')], string='Fee Type', required=True, copy=False)
    fine_log_ids = fields.One2many('ala.student.fine.log', 'fee_line_id', string="Fine Logs")
    


    @api.depends('amount', 'concession_amount', 'fine_amount')
    def _compute_amount_to_paid(self):
        for rec in self:
            rec.amount_to_paid = (
                    rec.amount
                    - rec.concession_amount
            )

    def action_open_fine_wizard(self):
        self.ensure_one()

        return {
            'name': 'Edit Fine Amount',
            'type': 'ir.actions.act_window',
            'res_model': 'ala.fine.remove.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_fee_line_id': self.id,
                'default_ex_fine_amount': self.fine_amount,
                'default_fine_amount': self.fine_amount,
            }
        }

    def _cron_update_overdue_fees(self):

        today = fields.Date.today()

        overdue_fees = self.search([
            ('payment_status', 'in', ['unpaid', 'upcoming', 'over_due']),
            ('overdue_date', '<', today),
            ('invoice_id', '=', False),
        ])

        print('lEEEEEEEEEEEEEEEEEE',len(overdue_fees))

        for fee in overdue_fees:

            # Update status
            fee.payment_status = 'over_due'

            # Add fine only once
            if fee.fine_amount == 0:
                fee.fine_amount = 20

    @api.model
    def action_pay_selected_fees(self, fee_ids, payment_date=None, payment_mode=None):

        if not fee_ids:
            raise UserError(_("Please select at least one fee."))

        fees = self.browse(fee_ids)

        already_paid = fees.filtered(lambda f: f.payment_status == 'paid')
        if already_paid:
            raise UserError(_("Some selected fees are already paid."))

        # 🔹 Determine journal type
        journal_type = {
            'cash': 'cash',
            'bank': 'bank',
            'online': 'bank',
        }.get(payment_mode)

        journal = False
        if journal_type:
            journal = self.env['account.journal'].search([
                ('type', '=', journal_type),
                ('company_id', '=', self.env.company.id)
            ], limit=1)

        # 🔹 Write payment details + journal
        fees.write({
            'payment_mode': payment_mode,
            'journal_id': journal.id if journal else False,
        })

        # ✅ Call your existing invoice logic
        fees.action_create_invoice(fee_ids, payment_date)

        if fees:
            fees[0].student_fee_id.last_fee_line_id = fees[0].id

        return {
            "report_name": "ala_education_fee.report_ala_fee_invoices",
            "res_id": fees[0].id,
        }

    @api.model
    def get_fee_lines(self, search=None, roll_no=None, division_id=None, academic_year_id=None):
        domain = []

        # Division filter
        if division_id:
            domain.append(('student_division_id', '=', int(division_id)))

        # Academic Year filter
        if academic_year_id:
            domain.append(('academic_year_id', '=', int(academic_year_id)))

        # Roll No filter
        if roll_no:
            domain.append(('student_id.roll_no', '=', roll_no))

        # Search filter
        elif search:
            domain += [
                '|',
                ('student_id.name', 'ilike', search),
                ('register_number', 'ilike', search),
            ]

        # Get grouped students
        student_groups = self.read_group(
            domain,
            ['student_id'],
            ['student_id'],
            limit=50
        )

        student_ids = [
            group['student_id'][0]
            for group in student_groups
            if group.get('student_id')
        ]

        if not student_ids:
            return []

        # Fetch all fee lines for matched students
        fee_domain = [('student_id', 'in', student_ids)]

        if division_id:
            fee_domain.append(('student_division_id', '=', int(division_id)))

        if academic_year_id:
            fee_domain.append(('academic_year_id', '=', int(academic_year_id)))

        fees = self.search(fee_domain)

        fee_type_order = {
            'admission': 1,
            're_admission': 2,
            'other': 3,
            'monthly': 4,
        }

        students_map = {}

        for f in fees:
            student_id = f.student_id.id

            if student_id not in students_map:
                monthly_lines = f.student_fee_id.fee_line_ids
                if academic_year_id:
                    monthly_lines = monthly_lines.filtered(
                        lambda line: line.academic_year_id and line.academic_year_id.id == int(academic_year_id)
                    )

                paid_months = len(
                    monthly_lines.filtered(
                        lambda line: line.fee_type == 'monthly' and line.payment_status == 'paid'
                    )
                )
                remaining_months = len(
                    monthly_lines.filtered(
                        lambda line: line.fee_type == 'monthly' and line.payment_status != 'paid'
                    )
                )

                students_map[student_id] = {
                    'id': student_id,
                    'student_fee_id': f.student_fee_id.id if f.student_fee_id else False,
                    'last_fee_line_id': f.student_fee_id.last_fee_line_id.id if f.student_fee_id and f.student_fee_id.last_fee_line_id else False,
                    'register_number': f.register_number or '',
                    'total_payable': f.student_fee_id.final_amount_total if f.student_fee_id else 0.0,
                    'total_paid': f.student_fee_id.amount_paid if f.student_fee_id else 0.0,
                    'total_unpaid': f.student_fee_id.amount_unpaid if f.student_fee_id else 0.0,
                    'total_overdue': f.student_fee_id.amount_due if f.student_fee_id else 0.0,
                    'paid_months': paid_months,
                    'remaining_months': remaining_months,
                    'student': f.student_id.name or '',
                    'roll_no': f.student_id.roll_no or '',
                    'division': f.student_division_id.name or '',
                    'fees': [],
                }

            students_map[student_id]['fees'].append({
                'id': f.id,
                'name': f.product_id.name or '',
                'concession_amount': f.concession_amount or 0.0,
                'fine_amount': f.fine_amount or 0.0,
                'amount': f.amount_to_paid or 0.0,
                'payment_status': f.payment_status or '',
                'fee_type': f.fee_type or '',
            })

        for student in students_map.values():
            student['fees'] = sorted(
                student['fees'],
                key=lambda x: fee_type_order.get(x['fee_type'], 99)
            )

        return list(students_map.values())

    def action_create_invoice(self, fee_ids, payment_date):
        fees = self.browse(fee_ids).exists()
        if not fees:
            raise UserError(_("No valid fees found."))

        # All lines must belong to one student fee record — the invoice is per student
        if len(fees.mapped('student_fee_id')) > 1:
            raise UserError(_("All selected fees must belong to the same student."))

        monthly_fees = fees.filtered(lambda f: f.fee_type == 'monthly')
        other_fees = fees - monthly_fees

        invoice_lines = []

        # ------------------------------------------------------------------
        # 1. Monthly fees (combined into one Tuition Fee line, EXCLUDING fine)
        # ------------------------------------------------------------------
        if monthly_fees:
            tuition_product = self.env.ref(
                'ala_education_fee.product_tuition_fee', raise_if_not_found=False)
            if not tuition_product:
                raise UserError(_("Tuition Fee product is not configured. "
                                  "Please upgrade the Fees module."))

            month_names = [
                (fee.fee_description or fee.product_id.name).replace(' Fee', '').strip()
                for fee in monthly_fees
            ]
            combined_desc = "Tuition Fee (%s)" % ", ".join(month_names)

            # Base amount only: amount - concession (fine goes on its own line)
            total_monthly_amount = sum(
                fee.amount - fee.concession_amount for fee in monthly_fees
            )

            invoice_lines.append((0, 0, {
                'product_id': tuition_product.id,
                'name': combined_desc,
                'monthly_fee': True,
                'quantity': 1,
                'price_unit': total_monthly_amount,
            }))

        # ------------------------------------------------------------------
        # 2. Other fees (one line each, EXCLUDING fine)
        # ------------------------------------------------------------------
        for fee in other_fees:
            invoice_lines.append((0, 0, {
                'product_id': fee.product_id.id,
                'name': fee.fee_description or fee.product_id.name,
                'quantity': 1,
                'price_unit': fee.amount - fee.concession_amount,
            }))

        # ------------------------------------------------------------------
        # 3. Late fee (combined, on dedicated product → separate income account)
        # ------------------------------------------------------------------
        total_fine = sum(fees.mapped('fine_amount'))
        if total_fine > 0:
            late_fee_product = self.env.ref(
                'ala_education_fee.product_late_fee', raise_if_not_found=False)
            if not late_fee_product:
                raise UserError(_("Late Fee product is not configured. "
                                  "Please upgrade the Fees module."))

            fined_months = [
                re.sub(r'\s*Fee\s*$', '', name, flags=re.IGNORECASE)
                for name in fees.filtered('fine_amount').mapped(lambda f: f.product_id.name)
            ]
            invoice_lines.append((0, 0, {
                'product_id': late_fee_product.id,
                'name': _("Late Fee (%s)", ", ".join(fined_months)),
                'quantity': 1,
                'price_unit': total_fine,
            }))

        # ------------------------------------------------------------------
        # 4. Invoice
        # ------------------------------------------------------------------
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': fees[0].student_id.partner_id.id,
            'journal_id': fees[0].journal_id.id,
            'invoice_date': payment_date,
            'student_fee_id': fees.student_fee_id.id,  # set at create, not post-write
            'invoice_line_ids': invoice_lines,
        })
        invoice.action_post()

        # ------------------------------------------------------------------
        # 5. Payment + reconciliation
        # ------------------------------------------------------------------
        payment_method_line = fees[0].journal_id.inbound_payment_method_line_ids[:1]
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': invoice.partner_id.id,
            'date': invoice.invoice_date,
            'amount': invoice.amount_total,
            'journal_id': invoice.journal_id.id,
            'payment_method_line_id': payment_method_line.id,
        })
        payment.action_post()

        (payment.move_id.line_ids + invoice.line_ids).filtered(
            lambda l: l.account_id.account_type == 'asset_receivable'
        ).reconcile()

        fees.write({
            'invoice_id': invoice.id,
            'payment_status': 'paid',
        })

        _logger.info("Fee invoice %s created and settled for student fee %s "
                     "(%s lines, fine %.2f)", invoice.name,
                     fees.student_fee_id.id, len(fees), total_fine)

        return {"invoice_id": invoice.id}

    def _compute_overdue_days(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.overdue_days = (today - rec.overdue_date).days if rec.overdue_date else 0



    @api.onchange('payment_mode')
    def _onchange_payment_mode_set_journal(self):
        if self.payment_mode:
            journal_type = {
                'cash': 'cash',
                'bank': 'bank',
                'online': 'bank',  # treat online as bank journal
            }.get(self.payment_mode)

            journal = self.env['account.journal'].search([
                ('type', '=', journal_type),
                ('company_id', '=', self.env.company.id)
            ], limit=1)

            self.journal_id = journal

    @api.onchange('select_for_invoice')
    def _onchange_select_inv_button(self):
        if self.select_for_invoice and self.payment_status == 'paid':
            raise UserError(_("Fees already paid. Please select another fees for payment"))

    # @api.depends('reminder_date', 'overdue_date', 'invoice_id')
    # def _compute_payment_status(self):
    #     today = date.today()
    #     for rec in self:
    #         rec.pay_status = True
    #         if rec.invoice_id:
    #             rec.payment_status = 'paid'
    #         elif rec.overdue_date and today > rec.overdue_date:
    #             rec.payment_status = 'over_due'
    #         elif rec.reminder_date and today < rec.reminder_date:
    #             rec.payment_status = 'upcoming'
    #         else:
    #             rec.payment_status = 'unpaid'

    def print_invoice(self):
        print('PRITNT REPORT____________,self',self)
        return self.env.ref('ala_education_fee.action_generate_fees_invoice_report').report_action(self)

    def unlink(self):
        for record in self:
            if record.payment_status == 'paid':
                raise UserError(_("You cannot delete this student already made some payments."))
        return super().unlink()

    @api.model
    def _cron_update_payment_status_and_fines(self):
        """Daily cron (early morning):
        1. Normalize payment_status for all fee lines.
        2. Apply late fine (once) to lines that are past due.
        """
        today = fields.Date.context_today(self)

        # ------------------------------------------------------------------
        # Step 1: STATUS TRANSITIONS (only touch rows whose status changes)
        # ------------------------------------------------------------------
        # paid: invoice exists but status not yet 'paid' (safety net —
        # settlement flow should already set this)
        self.search([
            ('invoice_id', '!=', False),
            ('payment_status', '!=', 'paid'),
        ]).write({'payment_status': 'paid'})

        # over_due: past due date, no invoice
        newly_overdue = self.search([
            ('invoice_id', '=', False),
            ('overdue_date', '<', today),
            ('payment_status', '!=', 'over_due'),
        ])
        newly_overdue.write({'payment_status': 'over_due'})

        # upcoming: before reminder date
        self.search([
            ('invoice_id', '=', False),
            ('reminder_date', '>', today),
            ('payment_status', '!=', 'upcoming'),
        ]).write({'payment_status': 'upcoming'})

        # unpaid: inside the reminder→due window
        self.search([
            ('invoice_id', '=', False),
            ('reminder_date', '<=', today),
            ('overdue_date', '>=', today),
            ('payment_status', '!=', 'unpaid'),
        ]).write({'payment_status': 'unpaid'})

        # ------------------------------------------------------------------
        # Step 2: FINE APPLICATION (after statuses are correct)
        # ------------------------------------------------------------------
        fine_amount = float(self.env['ir.config_parameter'].sudo().get_param(
            'ala_education_fee.late_fine_amount', default='0.0'))

        if fine_amount <= 0:
            _logger.info("Fee cron: no fine configured "
                         "(ala_education_fee.late_fine_amount), skipping fines.")
            return

        fine_candidates = self.search([
            ('payment_status', '=', 'over_due'),
            ('invoice_id', '=', False),
            ('fine_amount', '=', 0.0),
        ])

        if not fine_candidates:
            _logger.info("Fee cron: statuses updated, no new fines to apply.")
            return

        # Batch write the fine
        fine_candidates.write({'fine_amount': fine_amount})

        # # Log each fine for the audit trail (Fine Change Logs)
        # log_vals = [{
        #     'fee_line_id': line.id,
        #     # adjust field names to your ala.student.fine.log model:
        #     'old_amount': 0.0,
        #     'new_amount': fine_amount,
        #     'reason': 'Automated late fine (cron)',
        # } for line in fine_candidates]
        # self.env['ala.student.fine.log'].create(log_vals)

        _logger.info(
            "Fee cron: %s lines marked over_due, fine of %.2f applied to %s lines.",
            len(newly_overdue), fine_amount, len(fine_candidates),
        )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    late_fine_amount = fields.Float(
        string='Late Fee Fine Amount',
        config_parameter='ala_education_fee.late_fine_amount')

