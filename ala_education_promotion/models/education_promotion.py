from dateutil import relativedelta
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class EducationPromotion(models.Model):
    """ Model to manage academic promotions. """
    _name = 'ala.education.promotion'
    _description = 'Promotion'

    name = fields.Many2one('ala.education.academic.year',
                           string="Academic Year", required=True,
                           help='Represents the academic year for which '
                                'promotion details are recorded.')
    academic_result_ids = fields.One2many(
        'ala.education.student.final.result',
        'closing_id', string="Results",
        help='Stores the final results of students associated with '
             'this promotion.')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('result_computed', 'Result Computed'),
         ('close', 'Closed')], default='draft', string='State',
        help='The states of the promotion')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
        help='Specifies the company associated with the academic promotion.')

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_(
                    "You can only delete a promotion record in Draft state."
                ))
        return super(EducationPromotion, self).unlink()

    def action_compute_final_result(self):
        """
            Compute and record final results based on exam outcomes.
            This method sets the state of the academic promotion to 'result_computed'.
            It retrieves exam results related to the academic year and updates the
            education.student.final.result records accordingly.
            Returns:
                None
            """
        self.state = 'result_computed'
        exam_result_env = self.env['ala.education.exam.results']
        if not exam_result_env.search([
            ('academic_year_id', '=', self.name.id)]).filtered(
            lambda l: l.exam_id.exam_type_id.exam_order == 'annual'):
            raise ValidationError(
                'No Final Result found for the Academic Year %s' % self.name.id)
        for i in exam_result_env.search([
            ('academic_year_id', '=', self.name.id)]).filtered(
            lambda l: l.exam_id.exam_type_id.exam_order == 'annual'):
            self.env['ala.education.student.final.result'].create({
                'student_id': i.student_id.id,
                'final_result': 'pass',
                'division_id': i.division_id.id,
                'academic_year_id': i.division_id.academic_year_id.id,
                'closing_id': self.id,
            })

    def close_academic_year(self):
        self.state = 'close'

        division_obj = self.env['ala.education.class.division']
        history_obj = self.env['ala.education.class.history']

        new_academic_year = self.env['ala.education.academic.year'].search(
            [('next_academic_year', '=', True)], limit=1
        )
        if not new_academic_year:
            raise UserError(_("No next academic year is configured."))

        current_academic_year = self.name   # change if your field is different

        current_divisions = division_obj.search([
            ('academic_year_id', '=', current_academic_year.id)
        ])

        # 1. Create/reuse same divisions in new academic year
        for div in current_divisions:
            if not div.is_last_class and (not div.promote_class_id or not div.promote_division_id):
                raise ValidationError(
                    _('Promotion Class or Promotion Division is not added for the class %s - %s') %
                    (div.class_id.name, div.division_id.name)
                )

            new_division = division_obj.search([
                ('academic_year_id', '=', new_academic_year.id),
                ('class_id', '=', div.class_id.id),
                ('division_id', '=', div.division_id.id),
            ], limit=1)

            if not new_division:
                new_division = division_obj.create({
                    'actual_strength': div.actual_strength,
                    'academic_year_id': new_academic_year.id,
                    'class_id': div.class_id.id,
                    'faculty_id': div.faculty_id.id,
                    'division_id': div.division_id.id,
                    'is_last_class': div.is_last_class,
                    'active': True,
                })
            else:
                new_division.write({
                    'actual_strength': div.actual_strength,
                    'faculty_id': div.faculty_id.id,
                    'is_last_class': div.is_last_class,
                    'active': True,
                })

            if not div.is_last_class:
                new_division.sudo().write({
                    'promote_class_id': div.promote_class_id.id,
                    'promote_division_id': div.promote_division_id.id,
                })

        # 2. Create promoted classes in new academic year only if missing
        new_year_divisions = division_obj.search([
            ('academic_year_id', '=', new_academic_year.id),
            ('is_last_class', '=', False)
        ])

        for new_div in new_year_divisions:
            if new_div.promote_class_id and new_div.promote_division_id:
                promote_div = division_obj.search([
                    ('academic_year_id', '=', new_academic_year.id),
                    ('class_id', '=', new_div.promote_class_id.id),
                    ('division_id', '=', new_div.promote_division_id.id),
                ], limit=1)

                if not promote_div:
                    division_obj.create({
                        'actual_strength': new_div.actual_strength,
                        'academic_year_id': new_academic_year.id,
                        'class_id': new_div.promote_class_id.id,
                        'division_id': new_div.promote_division_id.id,
                        'faculty_id': new_div.faculty_id.id,
                        'active': True,
                    })

        # 3. Promote / retain students and create history
        for div in current_divisions:
            current_class_new_year = division_obj.search([
                ('academic_year_id', '=', new_academic_year.id),
                ('class_id', '=', div.class_id.id),
                ('division_id', '=', div.division_id.id),
            ], limit=1)

            promotion_class = False
            if not div.is_last_class:
                if div.promote_class_id and div.promote_division_id:
                    promotion_class = division_obj.search([
                        ('academic_year_id', '=', new_academic_year.id),
                        ('class_id', '=', div.promote_class_id.id),
                        ('division_id', '=', div.promote_division_id.id),
                    ], limit=1)

                    if not promotion_class:
                        raise UserError(
                            _('Promotion class not found in new academic year for %s.') % div.name
                        )
                else:
                    raise UserError(_(
                        'There is no promotion class set for the class %s. '
                        '\nIf it is the last class, please mark the checkbox in Class Division.'
                    ) % div.name)

            for student_line in div.final_student_ids:
                student = student_line.student_id

                # Create class history for current academic year + old class
                existing_history = history_obj.search([
                    ('academic_year_id', '=', current_academic_year.id),
                    ('class_id', '=', div.id),
                    ('student_id', '=', student.id),
                ], limit=1)

                if not existing_history:
                    history_obj.create({
                        'academic_year_id': current_academic_year.id,
                        'class_id': div.id,
                        'student_id': student.id,
                    })

                # Move student
                if student_line.final_result == 'pass':
                    if div.is_last_class:
                        student.write({
                            'active': False
                        })
                    else:
                        student.write({
                            'class_division_id': promotion_class.id
                        })

                elif student_line.final_result == 'fail':
                    if current_class_new_year:
                        student.write({
                            'class_division_id': current_class_new_year.id
                        })

        # 4. Archive old academic year divisions
        current_divisions.write({'active': False})




    # def close_academic_year(self):
    #     """
    #         Close the current academic year and initiate the process of
    #         transitioning to a new academic year.
    #         This method sets the state of the academic promotion to 'close' and
    #          performs the following actions:
    #         1. Creates a new academic year for the subsequent year.
    #         2. Copies class divisions from the current academic year to the
    #         new academic year.
    #         3. Generates promotion classes for non-last classes in the new
    #         academic year.
    #         4. Promotes or retains students based on their final results.
    #         Returns:
    #             None
    #         Raises:
    #             UserError: Raised if no promotion class is set for a class with
    #             missing promotion details.
    #         """
    #     self.state = 'close'
    #     division_obj = self.env['ala.education.class.division']
    #     new_academic_year = self.env['ala.education.academic.year'].search([('next_academic_year', '=', True)], limit=1)
    #     print('nrrrrrrrrrrrrr',new_academic_year)
    #     for div in division_obj.search( [('academic_year_id', '=', self.name.id)]):
    #         if not div.is_last_class:
    #             if not div.promote_class_id or not div.promote_division_id:
    #                 raise ValidationError(
    #                     'Promotion Class or Promotion Division is not added '
    #                     'for the class %s - %s'
    #                     % (div.class_id.name, div.division_id.name))
    #         new_division = division_obj.create({
    #             'actual_strength': div.actual_strength,
    #             'academic_year_id': new_academic_year.id,
    #             'class_id': div.class_id.id,
    #             'faculty_id': div.faculty_id.id,
    #             'division_id': div.division_id.id,
    #             'is_last_class': div.is_last_class,
    #         })
    #         if not new_division.is_last_class:
    #             new_division.sudo().write({
    #                 'promote_division_id': div.promote_division_id,
    #                 'promote_class_id': div.promote_class_id,
    #             })
    #     for new_div in division_obj.search(
    #             [('academic_year_id', '=', new_academic_year.id),
    #              ('is_last_class', '=', False)]):
    #         promote = division_obj.search(
    #             [('academic_year_id', '=', new_academic_year.id),
    #              ('name', '=', str(new_div.promote_class_id.name) + "-" + str(
    #                  new_div.promote_division_id.name))])
    #         if not promote:
    #             division_obj.create({
    #                 'actual_strength': new_div.actual_strength,
    #                 'academic_year_id': new_academic_year.id,
    #                 'class_id': new_div.promote_class_id.id,
    #                 'division_id': new_div.promote_division_id.id,
    #                 'faculty_id': new_div.faculty_id.id,
    #             })
    #     for div in division_obj.search(
    #             [('academic_year_id', '=', self.name.id)]):
    #         current_class = division_obj.search([
    #             ('name', '=', div.name),
    #             ('academic_year_id', '=', new_academic_year.id)], limit=1)
    #         if div.is_last_class:
    #             promotion_class = False
    #         else:
    #             if div.promote_class_id and div.promote_division_id:
    #                 promotion_class = division_obj.search([
    #                     ('name', '=',
    #                      div.promote_class_id.name + "-" + div.promote_division_id.name),
    #                     ('academic_year_id', '=', new_academic_year.id)],
    #                     limit=1)
    #             else:
    #                 raise UserError(_(
    #                     'There is no promotion class is set for the class %s.'
    #                     '\nIf it is the last class, Please mark the Check box '
    #                     'in the Class Division', div.name))
    #         for student in div.final_student_ids:
    #             if student.final_result == 'pass':
    #                 if not promotion_class:
    #                     student.student_id.active = False
    #                 else:
    #                     student.student_id.class_division_id = promotion_class.id
    #             elif student.final_result == 'fail':
    #                 student.student_id.class_division_id = current_class.id
