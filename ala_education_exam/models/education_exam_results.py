# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError



class EducationExamResults(models.Model):
    """
        Model to store and manage Education Exam Results.
        """
    _name = 'ala.education.exam.results'
    _description = 'Exam Results'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    name = fields.Char(string='Name',
                       help='Name associated with the exam result entry.')
    exam_id = fields.Many2one('ala.education.exam', string='Exam',
                              help='Select the exam associated with the result.')
    class_id = fields.Many2one('ala.education.class', string='Class',
                               help='Select the class for which the exam '
                                    'result is recorded.')
    division_id = fields.Many2one('ala.education.class.division', string='Division',
                                  help='Select the division within the class.')
    student_id = fields.Many2one('ala.education.student', string='Student',
                                 help='Select the student for whom the '
                                      'result is recorded.')
    student_name = fields.Char(string='Student',
                               help='Name of the student associated with the'
                                    ' exam result.')
    subject_line_ids = fields.One2many('ala.results.subject.line',
                                       'result_id',
                                       string='Subjects',
                                       help='List of subjects and their '
                                            'corresponding results for the'
                                            ' exam.')
    academic_year_id = fields.Many2one('ala.education.academic.year',
                                       string='Academic Year',
                                       related='division_id.academic_year_id',
                                       store=True,
                                       help='Academic year associated with'
                                            ' the division.')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get(),
        help='Company associated with the exam results.'
    )

    total_pass_mark = fields.Float(string='Total Pass Mark', store=True,
                                   readonly=True, compute='_total_marks_all',compute_sudo=True,
                                   help='Total pass marks obtained by the '
                                        'student.')
    total_max_mark = fields.Float(string='Total Max Mark', store=True,
                                  readonly=True, compute='_total_marks_all', compute_sudo=True,
                                  help='Total maximum marks for the exam.')
    total_mark_scored = fields.Float(string='Total Marks Scored', store=True,
                                     readonly=True, compute='_total_marks_all',compute_sudo=True,
                                     help='Total marks scored by the student.')
    total_mark_percentage = fields.Float(string='Total Marks Percentage', store=True,
                                     readonly=True, compute='_total_marks_all',compute_sudo=True,
                                     help='Total marks scored by the student.')
    overall_pass = fields.Boolean(string='Overall Pass/Fail', store=True,
                                  readonly=True, compute='_total_marks_all',compute_sudo=True,
                                  help='Overall pass or fail status based '
                                       'on subject results.')
    grade = fields.Char('Grade', compute='_total_marks_all',compute_sudo=True, store=True)

    @api.depends('subject_line_ids.mark_scored')
    def _total_marks_all(self):
        """
            Compute total pass marks, total max marks, total marks scored,
            and overall pass/fail status for the exam results.
            """
        for results in self:
            total_pass_mark = 0
            total_max_mark = 0
            total_mark_scored = 0
            overall_pass = True
            for subjects in results.subject_line_ids:
                total_pass_mark += subjects.pass_mark
                total_max_mark += subjects.max_mark
                total_mark_scored += subjects.mark_scored
                if not subjects.pass_or_fail:
                    overall_pass = False
            results.total_pass_mark = total_pass_mark
            results.total_max_mark = total_max_mark
            results.total_mark_scored = total_mark_scored
            results.overall_pass = overall_pass
            if results.total_max_mark > 0 and results.total_mark_scored:
                results.total_mark_percentage = (results.total_mark_scored / results.total_max_mark) * 100
                print('eeeeeeeeeeeeeeee', results.total_mark_percentage)
            if results.total_mark_percentage >= 90:
                results.grade = 'AA'
            elif results.total_mark_percentage >= 80 and results.total_mark_percentage < 90:
                results.grade = 'A+'
            elif results.total_mark_percentage >= 70 and results.total_mark_percentage < 80:
                results.grade = 'A'
            elif results.total_mark_percentage >= 60 and results.total_mark_percentage < 70:
                results.grade = 'B'
            elif results.total_mark_percentage >= 50 and results.total_mark_percentage < 60:
                results.grade = 'C'
            else:
                results.grade = 'D'

    def _total_marks_calculate_percentage(self):
        print('eeeeetttttttttttt',self)
        total_pass_mark = 0
        total_max_mark = 0
        total_mark_scored = 0
        overall_pass = True
        for subjects in self.subject_line_ids:
            total_pass_mark += subjects.pass_mark
            total_max_mark += subjects.max_mark
            total_mark_scored += subjects.mark_scored
            if not subjects.pass_or_fail:
                overall_pass = False
        self.total_pass_mark = total_pass_mark
        self.total_max_mark = total_max_mark
        self.total_mark_scored = total_mark_scored
        self.overall_pass = overall_pass
        total_max_mark = self.exam_id.no_of_subjects * self.exam_id.mark
        if total_max_mark > 0 and self.total_mark_scored:
            if self.exam_id.no_of_subjects == 0:
                raise UserError("Please Contact Administartor to configure No of Subjects.")
            self.total_mark_percentage = (self.total_mark_scored / total_max_mark) * 100
        if self.total_mark_percentage >= 90:
            self.grade = 'AA'
        elif self.total_mark_percentage >= 80 and self.total_mark_percentage < 90:
            self.grade = 'A+'
        elif self.total_mark_percentage >= 70 and self.total_mark_percentage < 80:
            self.grade = 'A'
        elif self.total_mark_percentage >= 60 and self.total_mark_percentage < 70:
            self.grade = 'B'
        elif self.total_mark_percentage >= 50 and self.total_mark_percentage < 60:
            self.grade = 'C'
        else:
            self.grade = 'D'


class ResultsSubjectLine(models.Model):
    """
        Model to store individual subject results for exams.
        """
    _name = 'ala.results.subject.line'
    _description = 'Results Subject Line'

    name = fields.Char(string='Name',
                       help='Name associated with the subject result entry.')
    subject_id = fields.Many2one('ala.education.subject',
                                 string='Subject',
                                 help='Select the subject for which the'
                                      ' result is recorded.')
    max_mark = fields.Float(string='Max Mark',
                            help='Maximum marks achievable for the subject.')
    pass_mark = fields.Float(string='Pass Mark',
                             help='Passing marks for the subject.')
    exam_mark = fields.Integer(string='Exam Mark',
                               help='Marks obtained by the student in the exam.')
    assign_mark = fields.Integer(string='Asign. Mark',
                                 help='Marks obtained by the student in the exam.', tracking=True, )
    mark_scored = fields.Float(string='Mark Scored',
                               help='Marks obtained by the student in the '
                                    'subject.')
    pass_or_fail = fields.Boolean(string='Pass/Fail',
                                  help='Pass or fail status for the '
                                       'subject result.')
    result_id = fields.Many2one('ala.education.exam.results',
                                string='Result Id',
                                help='Reference to the parent exam result.')
    exam_id = fields.Many2one('ala.education.exam', string='Exam',
                              help='Reference to the exam associated with the '
                                   'subject result.')
    class_id = fields.Many2one('ala.education.class', string='Class',
                               help='Reference to the class associated with'
                                    ' the subject result.')
    division_id = fields.Many2one('ala.education.class.division',
                                  string='Division',
                                  help='Reference to the division within the'
                                       ' class.')
    student_id = fields.Many2one('ala.education.student', string='Student',
                                 help='Reference to the student associated '
                                      'with the subject result.')
    student_name = fields.Char(string='Student',
                               help='Name of the student associated with the '
                                    'subject result.')
    academic_year_id = fields.Many2one('ala.education.academic.year',
                                       string='Academic Year',
                                       related='division_id.academic_year_id',
                                       store=True,
                                       help='Academic year associated '
                                            'with the subject result.')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get(),
        help='Company associated with the subject result.')
