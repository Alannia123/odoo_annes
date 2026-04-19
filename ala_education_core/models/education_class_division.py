# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EducationClassDivision(models.Model):
    """Manages class division details"""
    _name = 'ala.education.class.division'
    _description = "Class Division"
    _inherit = ['mail.thread']
    _order = "sequence asc"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('class_id') and vals.get('division_id'):
                class_rec = self.env['ala.education.class'].browse(vals['class_id'])
                division_rec = self.env['ala.education.division'].browse(vals['division_id'])
                vals['name'] = f"{class_rec.name}-{division_rec.name}"
        return super().create(vals_list)

    def action_view_students(self):
        """Return the list of current students in this class"""
        self.ensure_one()
        students = self.env['ala.education.student'].search(
            [('class_division_id', '=', self.id), ('tc_issued', '=', False), ('drop_out', '=', False)])
        students_list = students.mapped('id')
        return {
            'domain': [('id', 'in', students_list)],
            'name': _('Students'),
            'view_mode': 'list,form',
            'res_model': 'ala.education.student',
            'view_id': False,
            'context': {'default_class_id': self.id},
            'type': 'ir.actions.act_window'
        }

    def _compute_student_count(self):
        """Return the number of students in the class"""
        for rec in self:
            students = self.env['ala.education.student'].search(
                [('class_division_id', '=', rec.id)])
            student_count = len(students) if students else 0
            rec.update({
                'student_count': student_count,
                'actual_strength': student_count
            })

    name = fields.Char(string='Name', readonly=True,
                       help="Name of the Class division")
    sequence = fields.Integer(
        help="Gives the sequence category when displaying "
             "a list of menus at dashboard.",
    )
    actual_strength = fields.Integer(string='Class Strength',
                                     help="Total strength of the class", readonly=True)
    faculty_id = fields.Many2one('ala.education.faculty',
                                 string='Class Faculty', required=True,
                                 help="Class teacher/Faculty")
    academic_year_id = fields.Many2one('ala.education.academic.year',
                                       string='Academic Year',
                                       help="Select the Academic Year",
                                       required=True)
    class_id = fields.Many2one('ala.education.class', string='Class',
                               required=True, help="Select the Class")
    division_id = fields.Many2one('ala.education.division',
                                  string='Division', required=True,
                                  help="Select the Division")
    student_ids = fields.One2many('ala.education.student',
                                  'class_division_id',
                                  string='Students',
                                  help="Students under this division")
    amenities_ids = fields.One2many('ala.education.class.amenities',
                                    'class_id', string='Amenities',
                                    help="Amenities of this division")
    student_count = fields.Integer(string='Students Count',
                                   help="Count of the students in the "
                                        "division",
                                   compute='_compute_student_count')
    inv_generated = fields.Boolean('INV Generated?')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, index=True,
                                 default=lambda self: self.env.company,
                                 help="Company related to this journal")
    current_year = fields.Boolean(related='academic_year_id.enable', string='Current Year', store=True)


    # @api.constrains('actual_strength')
    # def validate_strength(self):
    #     """Return Validation error if
    #         the students strength is not a non-zero number"""
    #     for rec in self:
    #         if rec.actual_strength <= 0:
    #             raise ValidationError(_('Strength must be a Non-Zero value'))

    def action_generate_qr_code(self):
        for student in self.student_ids:
            student.action_generate_qr_code()

    def generate_portal_user(self):
        print('ffffffffffff')
        portal_group = self.env.ref('base.group_portal')
        created_users = []

        for student in self.student_ids:
            login = student.register_no

            # Determine password
            if student.aadhar_no and len(student.aadhar_no) >= 4:
                password = student.aadhar_no[-4:]
            elif student.date_of_birth:
                password = student.date_of_birth.strftime('%d%m%Y')
            else:
                continue  # Skip if neither Aadhaar nor birthdate

            # Create user
            user = self.env['res.users'].create({
                'name': student.name,
                'login': login,
                'password': password,
                'partner_id': student.partner_id.id if student.partner_id else False,
                'group_ids': [(6, 0, [portal_group.id])],
            })

            # Link to student
            student.user_id = user.id
            student.login = login
            student.ch_password = password

