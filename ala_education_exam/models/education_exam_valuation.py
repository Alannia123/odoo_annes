# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EducationExamValuation(models.Model):
    """
        Model representing Exam Valuation for Education.

        This model is used to store information about the valuation of exams,
        including details like the maximum mark, pass mark, students, and results.
    """
    _name = 'ala.education.exam.valuation'
    _description = "Exam Valuation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    name = fields.Char(
        string='Name', default='New', help='Name of the exam valuation.')
    exam_id = fields.Many2one(
        'ala.education.exam', string='Exam', required=True, tracking=True,
        domain=[('state', '=', 'ongoing')], help='Associated exam for'
                                                 ' valuation.')
    class_id = fields.Many2one(
        'ala.education.class', string='Class', tracking=True,
        required=True, help='Class associated with the exam valuation.')
    division_id = fields.Many2one(
        'ala.education.class.division', domain=[('current_year', '=', True)],
        string='Division', required=True, tracking=True,
        help='Division associated with the exam valuation.')
    teachers_id = fields.Many2one(
        'ala.education.faculty', string='Evaluator', tracking=True,
        help='Teacher or faculty responsible for exam valuation.')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)
    mark = fields.Integer(
        string='Max Mark', required=True,
        help='Maximum mark for the exam.')
    pass_mark = fields.Integer(
        string='Pass Mark', required=True,
        help='Passing mark for the exam.')
    state = fields.Selection(
        [('draft', 'Draft'), ('completed', 'Completed'),
         ('cancel', 'Canceled')], tracking=True,
        default='draft', help='State of the exam valuation.')
    valuation_line_ids = fields.One2many(
        'ala.exam.valuation.line',
        'valuation_id', string='Students', tracking=True,
        help='Students and their marks in the valuation.', )
    subject_id = fields.Many2one(
        'ala.education.subject',
        string='Subject', required=True, tracking=True,
        help='Subject for which the valuation is conducted.')
    mark_sheet_created = fields.Boolean(
        string='Mark sheet Created', copy=False,
        help='Flag indicating whether the mark sheet is created.')
    date = fields.Date(
        string='Date', default=fields.Date.today, readonly=True,
        help='Date of the exam valuation.')
    academic_year_id = fields.Many2one(
        'ala.education.academic.year', string='Academic Year',
        related='division_id.academic_year_id', store=True,
        help='Academic year associated with the exam valuation.')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, readonly=True,
        help='Company associated with the exam.')
    subject_ids = fields.Many2many('ala.education.subject', 'Subjects')
    division_ids = fields.Many2many('ala.education.class.division', 'Divisions')
    faculty_ids = fields.Many2many('ala.education.faculty', 'edu_fac_rel', 'exam_val', 'education_faculty_id', string='Faculties')
    # edu_faculty_ids = fields.Many2many('ala.education.faculty', 'edu_faculty_rel', 'fac_exam_val', 'edu_faculty_id', string='Faculties')
    is_assign_mark = fields.Boolean(related='exam_id.is_assign_mark', string='Is Assigment Mark?', copy=False)
    # assign_marks = fields.Char('Assignment Marks', copy=False, help='Enter Assignment marks by 1-20,2-34, etc...')
    # exam_marks = fields.Char('Exam Marks', copy=False, help='Enter Exam marks by 1-20,2-34, etc...')

    def name_get(self):
        result = []
        for rec in self:
            display = f"{rec.name} - {rec.subject_id.name}"
            result.append((rec.id, display))
        return result

    def view_subject_entry(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exam Valuations ',
            'res_model': 'ala.education.exam.valuation',
            'view_id': self.env.ref('ala_education_exam.education_exam_valuation_view_form').id,
            'view_mode': 'form',
            'res_id': self.id,
            # 'context': {'default_valuation_id': self.id},
        }


    def action_open_exam_valuation_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exam Valuation Lines',
            'res_model': 'ala.exam.valuation.line',
            'view_id': self.env.ref('ala_education_exam.exam_valuation_line_view_tree').id,
            'view_mode': 'tree',
            'domain': [('valuation_id', '=', self.id)],
            'context': {'default_valuation_id': self.id},
        }

    @api.onchange('exam_id')
    def _onchange_exam_type(self):
        if self.exam_id:
            self.mark = self.exam_id.mark
            self.pass_mark = self.exam_id.pass_mark
            class_divisions = self.env['ala.education.class.division'].search([('class_id', '=', self.exam_id.class_id.id)])
            self.division_ids = class_divisions.ids

    @api.onchange('division_id')
    def _onchange_division_id(self):
        self.subject_ids = False
        self.subject_id = False
        if self.division_id:
            subjects = self.division_id.class_id.subject_ids.mapped('subject_id')
            domain = [('id', 'in', subjects.ids)]
            self.subject_ids = subjects.ids

    # @api.onchange('subject_id')
    # def _onchange_subject_id(self):
    #     self.edu_faculty_ids = False
    #     self.teachers_id = False
    #     if self.subject_id:
    #         class_subjects = self.division_id.class_id.subject_ids
    #         sub_faculty_ids = class_subjects.filtered(lambda sub : sub.subject_id == self.subject_id).faculty_ids
    #         self.edu_faculty_ids = sub_faculty_ids.ids

    # @api.onchange('pass_mark')
    # def _onchange_pass_mark(self):
    #     """
    #        Update the 'pass_or_fail' field for valuation_line records
    #        when 'pass_mark' changes.
    #
    #        This onchange method is triggered when the 'pass_mark' field changes.
    #        It updates the 'pass_or_fail' field for all valuation_line records
    #        based on the new 'pass_mark'.
    #
    #        :raises UserError: If 'pass_mark' is greater than 'mark'.
    #     """
    #     if self.pass_mark > self.mark:
    #         raise UserError(_('Pass mark must be less than Max Mark'))
    #     for records in self.valuation_line_ids:
    #         records.pass_or_fail = True if (records.mark_scored >=
    #                                         self.pass_mark) else False

    @api.onchange('exam_id', 'subject_id')
    def _onchange_exam_id(self):

        if self.exam_id:
            if self.exam_id.division_id:
                self.class_id = self.exam_id.class_id
                self.division_id = self.exam_id.division_id
            elif self.exam_id.class_id:
                self.class_id = self.exam_id.class_id
            else:
                self.class_id = ''
                self.division_id = ''
            # self.mark = ''
            # if self.subject_id:
            #     for sub in self.exam_id.subject_line_ids:
            #         if sub.subject_id.id == self.subject_id.id:
            #             if sub.mark:
            #                 self.mark = sub.mark
        domain = []
        subjects = self.exam_id.subject_line_ids
        for items in subjects:
            domain.append(items.subject_id.id)
        return {'domain': {'subject_id': [('id', 'in', domain)]}}

    # @api.model
    # def create(self, vals):
    #     res = super().create(vals)
    #     valuation_obj = self.env['ala.education.exam.valuation']
    #     search_valuation = valuation_obj.sudo().search(
    #         [('exam_id', '=', res.exam_id.id),
    #          ('division_id', '=', res.division_id.id),
    #          ('subject_id', '=', res.subject_id.id), ('state', '!=', 'cancel')])
    #     if len(search_valuation) > 1:
    #         raise UserError(
    #             _(
    #                 'Valuation Sheet for \n Subject --> %s \nDivision --> %s'
    #                 ' \nExam --> %s \n is already created') % (
    #                 res.subject_id.name, res.division_id.name,
    #                 res.exam_id.name))
    #     return res

    def action_create_mark_sheet(self):
        """
            Create exam valuation lines for all students in the division.
            """

        valuation_obj = self.env['ala.education.exam.valuation']
        search_valuation = valuation_obj.sudo().search(
            [('exam_id', '=', self.exam_id.id),
             ('division_id', '=', self.division_id.id),
             ('subject_id', '=', self.subject_id.id), ('state', '!=', 'cancel')], order='id asc')
        print('wwwwwwwwwwww',search_valuation)
        if len(search_valuation) > 1:
            # Keep the first (oldest) one
            first_record = search_valuation[0]
            duplicates = search_valuation - first_record

            # Delete duplicates safely
            # duplicates.sudo().unlink()

            # # Redirect to the first record
            return {
                'type': 'ir.actions.act_window',
                'name': _('Attendance'),
                'res_model': 'ala.education.exam.valuation',
                'view_mode': 'form',
                'res_id': first_record.id,
                'target': 'current',
            }

        else:
            valuation_line_obj = self.env['ala.exam.valuation.line']
            tc_students = self.division_id.student_ids.filtered(lambda s: not s.tc_issued and not s.drop_out)
            students = tc_students.sorted(lambda s: int(s.roll_no) if s.roll_no and s.roll_no.isdigit() else 0 )
            if not students:
                raise UserError(_('There are no students in this Division'))
            # if len(students) < 1:
            #     raise UserError(_('There are no students in this Division'))
            # valuation_obj = self.env['ala.education.exam.valuation']
            # search_valuation = valuation_obj.sudo().sudo().search(
            #     [('exam_id', '=', self.exam_id.id),
            #      ('division_id', '=', self.division_id.id),
            #      ('subject_id', '=', self.subject_id.id), ('state', '!=', 'cancel')])
            # if len(search_valuation) > 1:
            #     raise UserError(
            #         _(
            #             'Valuation Sheet for \n Subject --> %s \nDivision --> %s'
            #             ' \nExam --> %s \n is already created') % (
            #             self.subject_id.name, self.division_id.name,
            #             self.exam_id.name))
            for student in students:
                data = {
                    'student_id': student.id,
                    'student_name': student.name,
                    'roll_no': student.roll_no,
                    'valuation_id': self.id,
                }
                valuation_line_obj.create(data)
            self.mark_sheet_created = True

    def action_valuation_completed(self):
        valuation_obj = self.env['ala.education.exam.valuation']
        search_valuation = valuation_obj.sudo().search(
            [('exam_id', '=', self.exam_id.id),
             ('division_id', '=', self.division_id.id),
             ('subject_id', '=', self.subject_id.id), ('state', '!=', 'cancel')])
        if len(search_valuation) > 1:
            raise UserError(
                _(
                    'Valuation Sheet for \n Subject --> %s \nDivision --> %s'
                    ' \nExam --> %s \n is already created') % (
                    self.subject_id.name, self.division_id.name,
                    self.exam_id.name))
        self.name = f"{self.exam_id.exam_type_id.name} ({self.division_id.name}) - {self.subject_id.name}"
        result_obj = self.env['ala.education.exam.results']
        result_line_obj = self.env['ala.results.subject.line']
        for students in self.valuation_line_ids:
            search_result = result_obj.sudo().search(
                [('exam_id', '=', self.exam_id.id),
                 ('division_id', '=', self.division_id.id),
                 ('student_id', '=', students.student_id.id)])
            if len(search_result) < 1:
                result_data = {
                    'name': self.name,
                    'exam_id': self.exam_id.id,
                    'class_id': self.class_id.id,
                    'division_id': self.division_id.id,
                    'student_id': students.student_id.id,
                    'student_name': students.student_id.name,
                }
                result = result_obj.create(result_data)
                result_line_data = {
                    'name': self.name,
                    'subject_id': self.subject_id.id,
                    'max_mark': self.mark,
                    'pass_mark': self.pass_mark,
                    'exam_mark': students.exam_mark,
                    'assign_mark': students.assign_mark,
                    'mark_scored': students.mark_scored,
                    'pass_or_fail': students.pass_or_fail,
                    'result_id': result.id,
                    'exam_id': self.exam_id.id,
                    'class_id': self.class_id.id,
                    'division_id': self.division_id.id,
                    'student_id': students.student_id.id,
                    'student_name': students.student_id.name,
                }
                result_line_obj.create(result_line_data)
                result._total_marks_calculate_percentage()
            else:
                result_line_data = {
                    'subject_id': self.subject_id.id,
                    'max_mark': self.mark,
                    'pass_mark': self.pass_mark,
                    'exam_mark': students.exam_mark,
                    'assign_mark': students.assign_mark,
                    'mark_scored': students.mark_scored,
                    'pass_or_fail': students.pass_or_fail,
                    'result_id': search_result.id,
                    'exam_id': self.exam_id.id,
                    'class_id': self.class_id.id,
                    'division_id': self.division_id.id,
                    'student_id': students.student_id.id,
                    'student_name': students.student_id.name,
                }
                result_line_obj.create(result_line_data)
                search_result._total_marks_calculate_percentage()

        self.state = 'completed'

    def action_set_to_draft(self):
        if self.exam_id.state == 'close':
            raise UserError(_('Not allowed to edit or reset to draft. its already in Closed State.'))

        """
           Set the exam valuation back to draft state and unlink related
           result line records.
           """
        result_line_obj = self.env['ala.results.subject.line']
        result_obj = self.env['ala.education.exam.results']
        for students in self.valuation_line_ids:
            search_result = result_obj.sudo().search(
                [('exam_id', '=', self.exam_id.id),
                 ('division_id', '=', self.division_id.id),
                 ('student_id', '=', students.student_id.id)])
            search_result_line = result_line_obj.sudo().search(
                [('result_id', '=', search_result.id),
                 ('subject_id', '=', self.subject_id.id)])
            search_result_line.sudo().unlink()
        result_obj._total_marks_calculate_percentage()
        self.state = 'draft'

    def action_valuation_canceled(self):
        """
            Set the exam valuation state to 'cancel'.
        """
        result_line_obj = self.env['ala.results.subject.line']
        result_obj = self.env['ala.education.exam.results']
        for students in self.valuation_line_ids:
            search_result = result_obj.sudo().search(
                [('exam_id', '=', self.exam_id.id),
                 ('division_id', '=', self.division_id.id),
                 ('student_id', '=', students.student_id.id)])
            search_result_line = result_line_obj.sudo().search(
                [('result_id', '=', search_result.id),
                 ('subject_id', '=', self.subject_id.id)])
            search_result_line.sudo().unlink()
        self.state = 'cancel'


class StudentsExamValuationLine(models.Model):
    """
        Model representing the lines for each student's exam valuation.
        """
    _name = 'ala.exam.valuation.line'
    _description = 'Exam Valuation Line'

    student_id = fields.Many2one('ala.education.student', string='Student',
                                 help='Student associated with this'
                                      ' valuation line.')
    student_name = fields.Char(string='Student Name',
                               help='Name of the student.')
    roll_no = fields.Char('Roll Number')
    exam_mark = fields.Integer(string='Exam Mark',
                               help='Marks obtained by the student in the exam.')
    assign_mark = fields.Integer(string='Asign. Mark',
                               help='Marks obtained by the student in the exam.', tracking=True,)
    mark_scored = fields.Integer(string='Total Mark',
                               help='Marks obtained by the student in the exam.')
    pass_or_fail = fields.Boolean(string='Pass/Fail',
                                  help='Indicates whether the student has ' 
                                       'passed or failed in the exam.', tracking=True)
    valuation_id = fields.Many2one('ala.education.exam.valuation',
                                   string='Valuation',
                                   help='Exam Valuation to which this line '
                                        'belongs.')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, readonly=True,
        help='Company associated with the exam.')

    @api.onchange('assign_mark', 'exam_mark', 'mark_scored', 'pass_or_fail')
    def _onchange_mark_scored(self):
        """
            Onchange method to validate mark_scored and update pass_or_fail.
        """
        # if self.valuation_id.is_assign_mark:
        print('5555555555555555222222', self.exam_mark)
        if self.exam_mark or self.assign_mark:
            print('5555555555555555',self.exam_mark)
            self.mark_scored = self.exam_mark + self.assign_mark
        if self.mark_scored > self.valuation_id.mark:
            raise UserError(_('Mark Scored must be less than Max Mark'))
        if self.mark_scored >= self.valuation_id.pass_mark:
            self.pass_or_fail = True
        else:
            self.pass_or_fail = False
    #
    # def calculate_total(self):
    #     for rec in self:
    #         if rec.exam_mark or rec.assign_mark:
    #             rec.mark_scored = rec.exam_mark + rec.assign_mark
    #         if rec.mark_scored > rec.valuation_id.mark:
    #             raise UserError(_('Mark Scored must be less than Max Mark'))
    #         if rec.mark_scored >= rec.valuation_id.pass_mark:
    #             rec.pass_or_fail = True
    #         else:
    #             rec.pass_or_fail = False

    # @api.depends('exam_mark')
    # def compute_total_marks(self):
    #     """
    #         Onchange method to validate mark_scored and update pass_or_fail.
    #     """
    #     for rec in self:
    #         rec.mark_scored = rec.exam_mark