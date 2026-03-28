# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from html.parser import HTMLParser

class HTMLFilter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = ''

    def handle_data(self, data):
        self.text += f'{data}\n'

def html2text(html):
    parser = HTMLFilter()
    parser.feed(html)
    return parser.text



class EducationStudent(models.Model):
    """For managing student records"""
    _name = 'ala.education.student'
    _inherit = ['mail.thread']
    _inherits = {'res.partner': 'partner_id'}
    _description = 'Student Record'
    # _order = "roll_no asc"
    _rec_name = "name"

    def action_student_documents(self):
        """Return the documents student submitted
        along with the admission application"""
        self.ensure_one()
        if self.application_id.id:
            documents = self.env['ala.education.document'].search(
                [('application_ref_id', '=', self.application_id.id)])
            documents_list = documents.mapped('id')
            return {
                'domain': [('id', 'in', documents_list)],
                'name': _('Documents'),
                'view_mode': 'tree,form',
                'res_model': 'ala.education.document',
                'view_id': False,
                'context': {
                    'default_application_ref_id': self.application_id.id},
                'type': 'ir.actions.act_window'
            }

    def action_open_camera(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'open_camera_widget',
            'params': {
                'record_id': self.id,
                'model': self._name,
                'field_name': 'image_1920',
            }
        }


    def action_view_student_discipline_history(self):
        discipline_id = self.env['ala.student.green.book'].search([('student_id', '=', self.id)])

        return {
            'name': _('Student Discipline'),
            'view_mode': 'form',
            'res_model': 'ala.student.green.book',
            'res_id': discipline_id.id,
            'view_id': self.env.ref('ala_education_core.student_green_book_form').id,
            'type': 'ir.actions.act_window'
        }

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     if name:
    #         recs = self.search(
    #             [('name', operator, name)] + (args or []), limit=limit)
    #         if not recs:
    #             recs = self.search(
    #                 [('ad_no', operator, name)] + (args or []), limit=limit)
    #         return recs.name_get()
    #     return super(EducationStudent, self).name_search(
    #         name, args=args, operator=operator, limit=limit)
    #

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('register_no'):
                vals['register_no'] = self.env['ir.sequence'].next_by_code(
                    'ala.education.student'
                ) or '/'
        return super().create(vals_list)

    partner_id = fields.Many2one(
        'res.partner', string='Partner', required=True,
        ondelete="cascade", help="Related partner of the student")
    last_name = fields.Char(string='Last Name', help="Enter last name")
    register_no = fields.Char('Registration Number', required=False)
    roll_no = fields.Char('Roll Number', required=False)

    date_of_birth = fields.Date(string="Date of Birth", required=True,
                                help="Enter date of birth of student")
    date_of_addmission = fields.Date(string="Date of Addmission", required=False,
                                help="Enter date of addmission of student")
    # guardian_id = fields.Many2one('res.partner', string="Guardian",
    #                               domain=[('is_parent', '=', True)],
    #                               help="Select guardian of the student")
    father_name = fields.Char(string="Father's Name", help="Father of the student")
    father_qualify = fields.Char(string="Father's Qualification", required=False)
    father_occupation = fields.Char(string="Father's Occupation", required=False)
    mother_name = fields.Char(string="Mother's Name", help="Mother of the student")
    mother_qualify = fields.Char(string="Mother's Qualification", required=False)
    mother_occupation = fields.Char(string="Mother's Occupation", required=False)
    mother_tongue = fields.Char(string="Mother Tongue", help="Enter Student's Mother Tongue")
    class_division_id = fields.Many2one('ala.education.class.division',
                                        string="Division",
                                        help="Class of the student")
    admission_class_id = fields.Many2one('ala.education.class',
                                         string="Class",
                                         help="Admission taken class")
    ad_no = fields.Char(string="Admission Number", readonly=True,
                        help="Admission number of student")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'),
                               ('other', 'Other')], string='Gender',
                              required=True, default='male',
                              tracking=True,
                              help="Gender details")
    blood_group = fields.Selection(
        [('none', 'None'),('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'), ('o+', 'O+'),
         ('o-', 'O-'), ('ab-', 'AB-'), ('ab+', 'AB+')],
        string='Blood Group', required=False, help="Blood group of student",
        default='none', tracking=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Current company")
    per_street = fields.Char(string="Street", help="Enter the street")
    per_street2 = fields.Char(string="Street2", help="Enter the street2")
    per_zip = fields.Char(change_default=True, string='ZIP code',
                          help="Enter the Zip Code")
    per_city = fields.Char(string='City', help="Enter the City name")
    per_state_id = fields.Many2one("res.country.state",
                                   string='State', ondelete='restrict',
                                   help="Select the State where you are from")
    per_country_id = fields.Many2one('res.country',
                                     string='Country', ondelete='restrict',
                                     help="Select the Country")
    medium_id = fields.Many2one('ala.education.medium',
                                string="Medium", required=False,
                                help="Choose the Medium of class,"
                                     " like English, Hindi etc")
    sec_lang_id = fields.Many2one('ala.education.subject',
                                  string="Second language",
                                  required=False,
                                  help="Choose the Second language")
    mother_tongue = fields.Char(string="Mother Tongue", required=False,      help="Enter Student's Mother Tongue")
    caste = fields.Char(string="Caste", help="My Caste is ")
    religion = fields.Char(string="Religion", help="My Religion is ")
    is_same_address = fields.Boolean(string="Is same Address?",
                                     help="Tick the field if the Present and "
                                          "permanent address is same")
    application_id = fields.Many2one('ala.education.application',
                                     string="Application No",
                                     help="Application number of student")
    class_history_ids = fields.One2many('ala.education.class.history',
                                        'student_id',
                                        string="Class Details",
                                        help="Previous class history details")
    exist_sis_bro_info = fields.Boolean('Student has a sister/brother in this school(not cousin/relatives)')
    exist_name = fields.Char('Name')
    exist_name = fields.Char('Name')
    exist_class = fields.Many2one('ala.education.class', 'Class')
    exist_section = fields.Many2one('ala.education.division', 'Section')
    special_concern = fields.Char('Special Concern regarding Child')
    no_of_discipline_history = fields.Integer('Disp History', compute='_compute_no_of_discipline_history')
    aadhar_no = fields.Char('Aadhar Number', required=False)
    user_id = fields.Many2one('res.users')
    ch_password = fields.Char('Password Sample', readonly=False)
    login = fields.Char('Login', readonly=True)
    hide_result = fields.Boolean('Hide Result', readonly=False)
    promoted = fields.Boolean('Promoted?', readonly=False)
    # student_html = fields.Html('Attendance & Fees',  compute="_compute_student_html", sanitize=False)
    student_html = fields.Html('Attendance & Fees',  sanitize=False)
    student_html_compute = fields.Boolean('StudentHtmlComp')
    tc_issued = fields.Boolean('TC Issued', copy=False, tracking=True)
    tc_issue_reason_id = fields.Many2one( 'ala.tc.issue.wizard.reason', string="TC Issue Reason", help="Give tc issue reason", required=False)
    drop_out = fields.Boolean('Dropout Student', copy=False, tracking=True)
    drop_out_reason_id = fields.Many2one('ala.dropout.wizard.reason', string="TC Issue Reason",
                                         help="Give tc issue reason", required=False)
    student_new_old = fields.Selection([
                        ('new', 'New Student'),
                        ('old', 'Old Student')], 'Student(Old Or New)', default='old',  copy=False)
    mobile = fields.Char('Mobile')

    def tc_issue_reason_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Issue TC',
            'res_model': 'ala.tc.issue.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
            }
        }

    def dropout_reason_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Student Dropout',
            'res_model': 'ala.dropout.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
            }
        }

    def _compute_student_html(self):
        for record in self:
            # Handle unsaved/new records
            if not record.id or not isinstance(record.id, int):
                record.student_html = """
                    <div style="padding:20px; font-family: Arial, sans-serif;">
                        <div style="color:#666; font-size:14px;">
                            Student details will appear after saving the record.
                        </div>
                    </div>
                """
                continue

            self.env.cr.execute("""
                SELECT
                    COUNT(*) AS total_days,
                    SUM(CASE WHEN present_morning = TRUE THEN 1 ELSE 0 END) AS present_days
                FROM education_attendance_line AS line
                JOIN education_academic_year AS year
                    ON year.id = line.academic_year_id
                WHERE line.student_id = %s
                  AND line.state = 'done'
                  AND year.enable = TRUE
            """, (record.id,))

            result = self.env.cr.dictfetchone() or {}
            total_days = result.get('total_days', 0) or 0
            present_days = result.get('present_days', 0) or 0
            absent_days = total_days - present_days

            current_aca_id = self.env['ala.education.academic.year'].search([('enable', '=', True)], limit=1)
            no_of_work_days = current_aca_id.total_no_of_working_days or 0

            attendance_percentage = 0
            if total_days > 0:
                attendance_percentage = round((present_days / total_days) * 100, 2)

            if attendance_percentage >= 75:
                progress_color = "#2e7d32"
            elif attendance_percentage >= 50:
                progress_color = "#f9a825"
            else:
                progress_color = "#c62828"

            total_fees = 25000
            paid_fees = 10000
            remaining_fees = total_fees - paid_fees
            overdue_amount = 5000

            main_container_style = (
                "font-family: Arial, sans-serif;"
                "max-width: 750px;"
                "margin: auto;"
                "background: #ffffff;"
                "border-radius: 12px;"
                "box-shadow: 0 4px 12px rgba(0,0,0,0.06);"
                "border: 1px solid #e0e0e0;"
            )

            section_style = "padding: 20px; box-sizing: border-box;"

            header_style = (
                "font-size: 18px;"
                "font-weight: 600;"
                "color: #333;"
                "margin-bottom: 15px;"
                "border-bottom: 2px solid #f0f0f0;"
                "padding-bottom: 10px;"
            )

            details_header_row_style = (
                "display: flex;"
                "justify-content: space-between;"
                "margin-bottom: 8px;"
                "border-bottom: 1px solid #f5f5f5;"
                "padding-bottom: 8px;"
            )

            details_value_row_style = "display: flex; justify-content: space-between;"

            details_header_item_style = (
                "flex: 1;"
                "text-align: center;"
                "font-size: 13px;"
                "font-weight: 500;"
            )

            details_value_item_style = (
                "flex: 1;"
                "text-align: center;"
                "font-size: 22px;"
                "font-weight: bold;"
            )

            progress_bar_bg_style = (
                "width: 100%;"
                "background: #f0f0f0;"
                "border-radius: 8px;"
                "height: 12px;"
                "overflow: hidden;"
                "margin-top: 15px;"
            )

            progress_bar_fill_style = (
                f"width: {attendance_percentage}%;"
                "height: 12px;"
                f"background: linear-gradient(90deg, {progress_color}, {progress_color});"
                "transition: width 0.5s ease;"
            )

            percentage_text_style = (
                "margin-top: 8px;"
                "font-size: 14px;"
                "font-weight: 600;"
                f"color: {progress_color};"
                "text-align: right;"
            )

            record.student_html = f"""
                <div style="{main_container_style}">
                    <div style="{section_style} border-bottom: 1px solid #f0f0f0;">
                        <div style="{header_style}">📊 Attendance</div>

                        <div style="{details_header_row_style}">
                            <div style="{details_header_item_style} color:#750f42;">📅 No Of Working Days</div>
                            <div style="{details_header_item_style} color:#004d40;">📅 No Of ATT Days</div>
                            <div style="{details_header_item_style} color:#1b5e20;">✅ Present</div>
                            <div style="{details_header_item_style} color:#c62828;">❌ Absent</div>
                        </div>

                        <div style="{details_value_row_style}">
                            <div style="{details_value_item_style} color:#750f42;">{no_of_work_days}</div>
                            <div style="{details_value_item_style} color:#004d40;">{total_days}</div>
                            <div style="{details_value_item_style} color:#1b5e20;">{present_days}</div>
                            <div style="{details_value_item_style} color:#c62828;">{absent_days}</div>
                        </div>

                        <div style="{progress_bar_bg_style}">
                            <div style="{progress_bar_fill_style}"></div>
                        </div>

                        <div style="{percentage_text_style}">
                            Attendance: {attendance_percentage}%
                        </div>
                    </div>

                    <div style="{section_style}">
                        <div style="{header_style}">💰 Fees</div>

                        <div style="{details_header_row_style}">
                            <div style="{details_header_item_style} color:#e65100;">Total</div>
                            <div style="{details_header_item_style} color:#1b5e20;">Paid</div>
                            <div style="{details_header_item_style} color:#f9a825;">Remaining</div>
                            <div style="{details_header_item_style} color:#c62828;">Overdue</div>
                        </div>

                        <div style="{details_value_row_style}">
                            <div style="{details_value_item_style} color:#e65100;">₹ {total_fees}</div>
                            <div style="{details_value_item_style} color:#1b5e20;">₹ {paid_fees}</div>
                            <div style="{details_value_item_style} color:#f9a825;">₹ {remaining_fees}</div>
                            <div style="{details_value_item_style} color:#c62828;">₹ {overdue_amount}</div>
                        </div>
                    </div>
                </div>
            """


    def _compute_no_of_discipline_history(self):
        for rec in self:
            discipline_id = self.env['ala.student.green.book'].search([('student_id', '=', rec.id)])
            if discipline_id:
                rec.no_of_discipline_history = len(discipline_id.green_line_ids)
            else:
                rec.no_of_discipline_history = 0

    _sql_constraints = [
        ('register_no', 'unique(register_no)',
         "Another Student already exists with this register number!"),
    ]

    @api.onchange('class_division_id')
    def _onchange_class_division_id(self):
        """Method for checking the maximum number of students in a class"""
        for rec in self:
            if rec.class_division_id.actual_strength<len(rec.class_division_id.student_ids):
                raise ValidationError("The number of students exceeds the "
                                      "maximum strength of the class division.")

    def update_password(self):
        if not self.user_id:
            raise ValidationError("User Not Found . Please Assign user")
        else:
            self.user_id.password = self.ch_password
            self.user_id.login = self.login or self.register_no
