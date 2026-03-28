# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import RedirectWarning
from odoo.exceptions import AccessError
from datetime import timedelta



class EducationAttendance(models.Model):
    """For managing attendance details of class"""
    _name = 'ala.education.attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Students Attendance'

    name = fields.Char(string='Name', default='New', compute='_compute_name',
                       help="Name of the attendance")
    class_id = fields.Many2one('ala.education.class', string='Class',
                               help="Class of the attendance")
    division_id = fields.Many2one('ala.education.class.division',
                                  string='Division', required=True, tracking=True,
                                  help="Class division for attendance")
    date = fields.Date(string='Date', default=fields.Date.today, required=True, tracking=True,
                       help="Attendance date", readonly=True)
    attendance_line_ids = fields.One2many('ala.education.attendance.line',
                                          'attendance_id',
                                          string='Attendance Line', ondelete='cascade', tracking=True,
                                          help="Student attendance line")
    attendance_created = fields.Boolean(string='Attendance Created',
                                        help="Enable if attendance is created")
    all_marked_morning = fields.Boolean(string="All Present Morning",
                                        help='Enable if all students are '
                                             'present in the morning')
    all_marked_afternoon = fields.Boolean(string="All Present Afternoon",
                                          help='Enable if all students are '
                                               'present in the afternoon')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             default='draft', string="State", tracking=True,
                             help="Stages of attendance")
    academic_year_id = fields.Many2one(
        'ala.education.academic.year',
        string='Academic Year',
        domain=[('enable', '=', True)],
        default=lambda self: self.env['ala.education.academic.year'].search([('enable', '=', True)], limit=1),
    )
    faculty_id = fields.Many2one('ala.education.faculty',
                                 string='Faculty',
                                 related='division_id.faculty_id',
                                 help="Faculty of the class")
    company_id = fields.Many2one(
        'res.company', string='Company', help="Current Company",
        default=lambda self: self.env.company)
    absent_roll_nos = fields.Char('Absent Roll Nos', copy=False, help='Enter absent roll nos only')
    # attendance_image = fields.Binary(
    #     string="Capture Attendance Photo",
    #     help="Capture photo using camera"
    # )
    # attendance_image_name = fields.Char("Image Name")

    @api.depends('class_id', 'division_id', 'date')
    def _compute_name(self):
        for rec in self:
            parts = ["ATT"]
            if rec.division_id:
                rec.class_id = rec.division_id.class_id.id
            # if rec.class_id:
            #     parts.append(rec.class_id.name)
            if rec.division_id:
                parts.append(rec.division_id.name)
            if rec.date:
                parts.append(rec.date.strftime('%d-%m-%Y'))
            rec.name = "/".join(parts)

    @api.constrains('division_id', 'date')
    def _check_duplicate_attendance(self):
        for rec in self:
            if not rec.division_id or not rec.date:
                continue

            domain = [
                ('division_id', '=', rec.division_id.id),
                ('date', '=', rec.date),
                ('id', '!=', rec.id),
            ]

            if self.search_count(domain):
                raise ValidationError(_(
                    "Attendance Entry is already created for Division '%s' on %s."
                ) % (rec.division_id.name, rec.date))

    present_count = fields.Integer(
        string="Presents",
        compute="_compute_attendance_count"
    )

    absent_count = fields.Integer(
        string="Absents",
        compute="_compute_attendance_count"
    )

    @api.depends('attendance_line_ids.present_morning')
    def _compute_attendance_count(self):
        for rec in self:
            rec.present_count = len(
                rec.attendance_line_ids.filtered(lambda l: l.present_morning)
            )
            rec.absent_count = len(
                rec.attendance_line_ids.filtered(lambda l: not l.present_morning)
            )

    @api.model
    def generate_daily_attendance(self):
        """Delete previous day DRAFT attendance and create today's attendance"""

        today = fields.Date.context_today(self)
        yesterday = today - timedelta(days=1)

        # 🧹 DELETE previous day DRAFT attendance
        old_drafts = self.search([
            ('date', '=', yesterday),
            ('state', '=', 'draft'),
        ])
        if old_drafts:
            old_drafts.unlink()

        # 🔍 Get all divisions
        divisions = self.env['ala.education.class.division'].search([])
        if not divisions:
            return True

        for division in divisions:
            # ❌ Skip if attendance already exists for today
            exists = self.search_count([
                ('division_id', '=', division.id),
                ('date', '=', today),
            ])
            if exists:
                continue

            # ✅ Create today's attendance
            self.create({
                'division_id': division.id,
                'class_id': division.class_id.id,
                'date': today,
                'state': 'draft',
            })

        return True
    # 🔘 Smart button actions
    def action_view_present_students(self):
        self.ensure_one()
        return {
            'name': 'Present Students',
            'type': 'ir.actions.act_window',
            'res_model': 'ala.education.attendance.line',
            'view_mode': 'tree',
            'domain': [
                ('attendance_id', '=', self.id),
                ('present_morning', '=', True)
            ],
            'context': {'default_attendance_id': self.id},
        }

    def action_view_absent_students(self):
        self.ensure_one()
        return {
            'name': 'Absent Students',
            'type': 'ir.actions.act_window',
            'res_model': 'ala.education.attendance.line',
            'view_mode': 'tree',
            'domain': [
                ('attendance_id', '=', self.id),
                ('present_morning', '=', False)
            ],
            'context': {'default_attendance_id': self.id},
        }

    # @api.model
    # def create(self, vals):
    #     user = self.env.user
    #
    #     if not (
    #             user.has_group('ala_education_core.group_education_principal') or
    #             user.has_group('ala_education_core.group_education_office_admin')
    #     ):
    #         raise AccessError(_(
    #             "You are not allowed to create attendance records."
    #         ))
    #
    #     return super().create(vals)

    # def action_extract_absent_from_image(self):
    #     for rec in self:
    #         if not rec.attendance_image:
    #             raise UserError("Please upload an attendance image first.")
    #
    #         # Ensure attendance lines exist (needed for validation)
    #         if not rec.attendance_line_ids:
    #             rec.action_create_attendance_line()
    #
    #         # --- OCR PART ---
    #         image_data = base64.b64decode(rec.attendance_image)
    #         image = Image.open(io.BytesIO(image_data))
    #         extracted_text = pytesseract.image_to_string(image)
    #
    #
    #         # Extract numbers from OCR text
    #         roll_numbers = re.findall(r'\b\d+\b', extracted_text)
    #         print('wwwwwwwwwwwww',roll_numbers)
    #
    #         if not roll_numbers:
    #             raise UserError("No roll numbers detected from image.")
    #
    #         # --- VALIDATION PART (HERE) ---
    #         valid_rolls = set(
    #             (rec.attendance_line_ids.mapped('roll_no') or [])
    #         )
    #
    #         invalid_rolls = set(roll_numbers) - valid_rolls
    #         if invalid_rolls:
    #             raise UserError(
    #                 "Invalid roll numbers detected: %s"
    #                 % ", ".join(sorted(invalid_rolls, key=int))
    #             )
    #
    #         # --- SAVE RESULT ---
    #         rec.absent_roll_nos = ",".join(
    #             sorted(set(roll_numbers), key=int)
    #         )

    @api.constrains('date')
    def _check_not_holiday(self):
        for rec in self:
            holiday = self.env['ala.school.event'].search([
                ('event_date', '=', rec.date),
                ('is_holiday', '=', True)
            ], limit=1)
            if holiday:
                raise ValidationError(
                    "You cannot take attendance on %s because it is marked as a holiday (%s)."
                    % (rec.date, holiday.display_name))

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         division_id = vals.get('division_id')
    #         date = vals.get('date')
    #         company_id = vals.get('company_id')
    #
    #         if division_id and date and company_id:
    #             existing_attendance = self.sudo().search([
    #                 ('division_id', '=', division_id),
    #                 ('date', '=', date),
    #                 ('company_id', '=', company_id),
    #             ])
    #             print('sssssssssssssss',existing_attendance)
    #
    #             if existing_attendance:
    #                 # Instead of creating, open wizard
    #                 wizard = self.env['attendance.duplicate.wizard'].create({
    #                     'message': _(
    #                         'Attendance for %s on "%s" already exists.\n'
    #                         'Do you want to open the existing record?'
    #                     ) % (existing_attendance.division_id.name, existing_attendance.date),
    #                     'existing_id': existing_attendance.id,
    #                 })
    #                 return {
    #                     'type': 'ir.actions.act_window',
    #                     'res_model': 'attendance.duplicate.wizard',
    #                     'view_mode': 'form',
    #                     'res_id': wizard.id,
    #                     'target': 'new',
    #                 }
    #
    #     records = super().create(vals_list)
    #     for rec in records:
    #         rec.class_id = rec.division_id.class_id.id
    #     return records

    # def write(self, vals):
    #     """Check and return validation if attendance for this day exists"""
    #     res = super(EducationAttendance, self).write(vals)
    #
    #     # Update class_id if division changes
    #     if 'division_id' in vals:
    #         for record in self:
    #             record.class_id = record.division_id.class_id.id
    #
    #     attendance_obj = self.env['ala.education.attendance']
    #
    #     for record in self:
    #         existing_attendance = attendance_obj.sudo().search([
    #             ('division_id', '=', record.division_id.id),
    #             ('date', '=', record.date),
    #             ('company_id', '=', record.company_id.id)
    #         ])
    #
    #         if len(existing_attendance) > 1:
    #             # Find the already existing record (excluding the current one)
    #             existing = existing_attendance.filtered(lambda r: r.id != record.id)
    #             if existing:
    #                 existing_record = existing[0]
    #
    #                 # Create redirect action
    #                 action = self.env.ref('ala_education_attendances.education_attendance_action').id
    #
    #                 # Message shown in popup
    #                 message = _(
    #                     'Attendance for %s on "%s" already exists.\n'
    #                     'Do you want to open the existing record?'
    #                 ) % (record.division_id.name, record.date)
    #
    #                 # Raise RedirectWarning
    #                 raise RedirectWarning(message, action, _('Open Existing Record'))
    #
    #     return res


    def action_create_attendance_line(self):
        for rec in self:
            # Prevent duplicate creation
            if rec.attendance_line_ids:
                continue

            students = rec.division_id.student_ids.filtered(lambda s: not s.tc_issued and not s.drop_out)

            if not students:
                raise UserError(_('There are no students in this Division'))

            # Safe sorting: numeric roll_no first, then text
            students_sorted = students.sorted(
                key=lambda s: (not (s.roll_no or '').isdigit(),
                               int(s.roll_no) if (s.roll_no or '').isdigit() else (s.roll_no or ''))
            )

            values = []
            for student in students_sorted:
                values.append({
                    'name': rec.name,
                    'attendance_id': rec.id,
                    'student_id': student.id,
                    'student_name': student.name,
                    'class_id': rec.division_id.class_id.id,
                    'division_id': rec.division_id.id,
                    'date': rec.date,
                })

            # 🚀 Single DB call
            self.env['ala.education.attendance.line'].create(values)

            rec.attendance_created = True

    def action_mark_all_present_morning(self):
        """Mark all students as present (morning)"""
        self.attendance_line_ids.write({'present_morning': True})
        self.attendance_line_ids.write({'attendance_status': 'present'})
        self.all_marked_morning = True

    def action_un_mark_all_present_morning(self):
        """Unmark all students as present (morning)"""
        self.attendance_line_ids.write({'present_morning': False})
        self.attendance_line_ids.write({'attendance_status': 'absent'})
        self.all_marked_morning = False

    def action_attendance_done(self):
        """Set attendance and all lines to Done"""
        for rec in self:
            # Create lines if not created
            rec.action_create_attendance_line()

            lines = rec.attendance_line_ids
            if not lines:
                raise UserError(_("No attendance lines found."))

            # ✅ Step 1: Mark all students as present
            lines.write({'present_morning': True})
            lines.write({'attendance_status': 'present'})



            # ✅ Step 2: Handle absent roll numbers
            if rec.absent_roll_nos:

                # Convert "1,2,3,4" → ['1', '2', '3', '4']
                absent_rolls = [
                    r.strip()
                    for r in rec.absent_roll_nos.split(',')
                    if r.strip()
                ]

                valid_rolls = set(
                    str(r) for r in rec.attendance_line_ids.mapped('roll_no') if r
                )

                invalid_rolls = set(absent_rolls) - valid_rolls

                if invalid_rolls:
                    raise UserError(
                        "Invalid roll numbers detected: %s"
                        % ", ".join(sorted(invalid_rolls, key=int))
                    )

                # Find matching attendance lines
                absent_lines = lines.filtered(
                    lambda l: l.roll_no and l.roll_no in absent_rolls
                )

                # Mark them absent
                absent_lines.write({'present_morning': False})
                absent_lines.write({'attendance_status': 'absent'})

            # ✅ Step 3: Finalize attendance
            lines.write({'state': 'done'})
            rec.state = 'done'

    def action_set_to_draft(self):
        for rec in self:
            if rec.state == 'draft':
                continue
            rec.action_un_mark_all_present_morning()
            rec.attendance_line_ids.write({'state': 'draft'})
            rec.state = 'draft'

    def unlink(self):
        for record in self:
            if record.state == 'done':
                raise UserError("You cannot delete a record that is marked as Done.")
        return super(EducationAttendance, self).unlink()
