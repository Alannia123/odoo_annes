# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import RedirectWarning


class EducationEvaluation(models.Model):
    """For managing attendance details of class"""
    _name = 'ala.education.evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Students Evaluation'

    name = fields.Char(string='Name', default='New',
                       help="Name of the evaluation")
    class_id = fields.Many2one('ala.education.class', string='Class',
                               help="Class of the attendance")
    division_id = fields.Many2one('ala.education.class.division', domain=[('current_year', '=', True)],
                                  string='Division', required=True, tracking=True,
                                  help="Class division for attendance")
    date = fields.Date(string='Date', default=fields.Date.today, required=True, tracking=True,
                       help="Attendance date", readonly=True)
    half_evaluation_line_ids = fields.One2many('ala.education.half.evaluation.line',
                                          'evaluation_id',
                                          string='Evaluation Line', ondelete='cascade', tracking=True,
                                          help="Student evaluation line")
    annual_evaluation_line_ids = fields.One2many('ala.education.annual.evaluation.line',
                                          'evaluation_id',
                                          string='Evaluation Line', ondelete='cascade', tracking=True,
                                          help="Student evaluation line")
    evaluation_created = fields.Boolean(string='Evaluation Created',
                                        help="Enable if attendance is created")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             default='draft', string="State", tracking=True,
                             help="Stages of attendance")
    academic_year_id = fields.Many2one(
        'ala.education.academic.year',
        string='Academic Year', readonly=True,
        default=lambda self: self.env['ala.education.academic.year'].search([('enable', '=', True)], limit=1).id
    )
    faculty_id = fields.Many2one('ala.education.faculty',
                                 string='Faculty',
                                 related='division_id.faculty_id',
                                 help="Faculty of the class")
    company_id = fields.Many2one(
        'res.company', string='Company', help="Current Company",
        default=lambda self: self.env.company)

    _sql_constraints = [
        ('unique_division_academic_year',
         'unique(division_id, academic_year_id)',
         'Evaluation already exists for this Division in the selected Academic Year!')
    ]

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):

            # seq = self.env['ir.sequence'].next_by_code('ala.education.evaluation') or _('New')

            # Get Academic Year
            academic_year = ''
            seq = 'EVA'
            if vals.get('academic_year_id'):
                year = self.env['ala.education.academic.year'].browse(vals['academic_year_id'])
                academic_year = year.name or ''

            # Get Division
            division_name = ''
            if vals.get('division_id'):
                division = self.env['ala.education.class.division'].browse(vals['division_id'])
                division_name = division.name or ''

            vals['name'] = f"{seq}/{academic_year}/{division_name}"

        return super().create(vals)


    def action_create_evaluation_line(self):
        """Ensure only one attendance per division/date — keep first, delete others."""
        self.ensure_one()
        self.class_id = self.division_id.class_id.id

        # Find all attendances with same division/date
        existing_evaluation = self.sudo().search([
            ('division_id', '=', self.division_id.id),
            ('academic_year_id', '=', self.academic_year_id.id),
        ], order='id asc')

        if len(existing_evaluation) > 1:
            # Keep the first (oldest) one
            first_record = existing_evaluation[0]
            duplicates = existing_evaluation - first_record

            # Delete duplicates safely
            duplicates.sudo().unlink()

            # # Redirect to the first record
            return {
                'type': 'ir.actions.act_window',
                'name': _('Evaluation'),
                'res_model': 'ala.education.evaluation',
                'view_mode': 'form',
                'res_id': first_record.id,
                'target': 'current',
            }
        else:
            # self.name = str(self.date)
            eval_half_line_obj = self.env['ala.education.half.evaluation.line']
            eval_annual_line_obj = self.env['ala.education.annual.evaluation.line']
            students = self.division_id.student_ids
            students_sorted = sorted(students, key=lambda s: int(s.roll_no) if s.roll_no.isdigit() else s.roll_no
            )
            if len(students) < 1:
                raise UserError(_('There are no students in this Division'))
            for student in students_sorted:
                data = {
                    'name': self.name,
                    'evaluation_id': self.id,
                    'student_id': student.id,
                    # 'roll_no': student.roll_no,
                    'student_name': student.name,
                    'class_id': self.division_id.class_id.id,
                    'division_id': self.division_id.id,
                    'date': self.date,
                }
                eval_half_line_obj.create(data)
                eval_annual_line_obj.create(data)
            self.evaluation_created = True


    def action_eveluation_done(self):
        self.state = 'done'

    def action_set_to_draft(self):
        self.state = 'draft'

    def unlink(self):
        for record in self:
            if record.state == 'done':
                raise UserError("You cannot delete a record that is marked as Done.")
        return super().unlink()



# -*- coding: utf-8 -*-

from odoo import models, fields


class EducationEvaluationLine(models.Model):
    """Used for managing attendance shift details"""
    _name = 'ala.education.half.evaluation.line'
    _description = 'Half Evaluation Lines'

    name = fields.Char(string='Name', help="Name of evaluation")
    evaluation_id = fields.Many2one('ala.education.evaluation',
                                    string='Evaluation Id', ondelete='cascade',
                                    help="Connected Attendance")
    student_id = fields.Many2one('ala.education.student',
                                 string='Student',
                                 help="Student ID for the attendance")
    register_no = fields.Char(related='student_id.register_no', string='Registration Number', required=False, readonly=True, store=True)
    roll_no = fields.Char(related='student_id.roll_no', string='Roll Number', readonly=True)
    student_name = fields.Char(string='Student', related='student_id.name',
                               help="Student name for attendance")
    class_id = fields.Many2one('ala.education.class', string='Class',
                               required=True,
                               help="Enter class for attendance")
    division_id = fields.Many2one('ala.education.class.division', domain=[('current_year', '=', True)],
                                  string='Division',
                                  help="Enter class division for attendance",
                                  required=True)
    date = fields.Date(string='Date', required=True, help="Date of attendance")
    emotional_maturity = fields.Selection([
                                            
                                            ('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Emotional Maturity', copy=False, )
    social_maturity = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Social Maturity', copy=False, )
    intellectual_maturity = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Intellectual Maturity', copy=False, )
    moral_maturity = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Moral/Ethical Maturity', copy=False, )
    personal_resp = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Personal Responsibility', copy=False, )
    adaptobilty_resilience = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Adaptability/Resilience', copy=False, )
    academic_year_id = fields.Many2one('ala.education.academic.year',
                                       string='Academic Year',
                                       related='evaluation_id.academic_year_id',
                                       help="Academic year of education")

class AnnualEvaluationLine(models.Model):
    """Used for managing attendance shift details"""
    _name = 'ala.education.annual.evaluation.line'
    _description = 'Annual Evaluation Lines'

    name = fields.Char(string='Name', help="Name of evaluation")
    evaluation_id = fields.Many2one('ala.education.evaluation',
                                    string='Evaluation Id', ondelete='cascade',
                                    help="Connected Attendance")
    student_id = fields.Many2one('ala.education.student',
                                 string='Student',
                                 help="Student ID for the attendance")
    register_no = fields.Char(related='student_id.register_no', string='Registration Number', required=False, readonly=True, store=True)
    roll_no = fields.Char(related='student_id.roll_no', string='Roll Number', readonly=True)
    student_name = fields.Char(string='Student', related='student_id.name',
                               help="Student name for attendance")
    class_id = fields.Many2one('ala.education.class', string='Class',
                               required=True,
                               help="Enter class for attendance")
    division_id = fields.Many2one('ala.education.class.division', domain=[('current_year', '=', True)],
                                  string='Division',
                                  help="Enter class division for attendance",
                                  required=True)
    date = fields.Date(string='Date', required=True, help="Date of attendance")
    emotional_maturity = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Emotional Maturity', copy=False, )
    social_maturity = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Social Maturity', copy=False, )
    intellectual_maturity = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Intellectual Maturity', copy=False, )
    moral_maturity = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Moral/Ethical Maturity', copy=False, )
    personal_resp = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Personal Responsibility', copy=False, )
    adaptobilty_resilience = fields.Selection([('high_mature', 'Highly Mature'),
                                           ('mature', 'Mature'),
                                           ('develop', 'Developing'),
                                           ('need_guide', 'Needs Guidence'),
                                           ('immature', 'Immature')], 'Adaptability/Resilience', copy=False, )
    academic_year_id = fields.Many2one('ala.education.academic.year',
                                       string='Academic Year',
                                       related='evaluation_id.academic_year_id',
                                       help="Academic year of education")

