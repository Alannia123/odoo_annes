# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


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






