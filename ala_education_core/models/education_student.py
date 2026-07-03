# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from html.parser import HTMLParser
import qrcode
import base64
from io import BytesIO

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
    _order = 'division_sequence, roll_no_int, roll_no, name'
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
    class_division_id = fields.Many2one('ala.education.class.division', domain=[('current_year', '=', True)],
                                        string="Division",
                                        help="Class of the student", )
    admission_class_id = fields.Many2one('ala.education.class',
                                         string="Class",
                                         help="Admission taken class")
    ad_no = fields.Char(string="Admission Number", help="Admission number of student")
    admission_no = fields.Char(string="Admission Number", help="Admission number of student")

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
    student_html = fields.Html('Attendance & Fees',  compute="_compute_student_html", sanitize=False)
    # student_html = fields.Html('Attendance & Fees',  sanitize=False)
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
    qr_code = fields.Binary("QR Code", readonly=True, attachment=True)
    qr_token = fields.Char("QR Token", readonly=True, copy=False, index=True)
    qr_url = fields.Char("QR Url", readonly=True, copy=False, index=True)
    division_sequence = fields.Integer(
        related='class_division_id.sequence',
        store=True,
        index=True,
    )
    roll_no_int = fields.Integer(
        string="Roll No Sort",
        compute="_compute_roll_no_int",
        store=True,
        index=True,
    )

    @api.depends('roll_no')
    def _compute_roll_no_int(self):
        for rec in self:
            val = (rec.roll_no or '').strip()
            if val.isdigit():
                rec.roll_no_int = int(val)
            else:
                rec.roll_no_int = 999999

    def _build_qr_verify_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/student/verify/{self.id}/{self.qr_token}"

    def action_generate_qr_code(self):
        for rec in self:
            if not rec.qr_token:
                rec.qr_token = (self.env['ir.sequence'].next_by_code('mis.education.student.qr.token') or str(rec.id)).replace('/', '')

            qr_data = rec._build_qr_verify_url()
            rec.qr_url = qr_data

            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=2,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")

            rec.qr_code = base64.b64encode(buffer.getvalue()).decode('utf-8')

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
            if not record.id or not isinstance(record.id, int):
                record.student_html = ""
                continue

            current_aca_id = self.env['ala.education.academic.year'].search([
                ('enable', '=', True)
            ], limit=1)

            self.env.cr.execute("""
                SELECT
                    COUNT(*) AS total_days,
                    SUM(CASE WHEN present = TRUE THEN 1 ELSE 0 END) AS present_days
                FROM ala_education_attendance_line AS line
                JOIN ala_education_academic_year AS year
                    ON year.id = line.academic_year_id
                WHERE line.student_id = %s
                  AND line.state = 'done'
                  AND year.enable = TRUE
            """, (record.id,))

            result = self.env.cr.dictfetchone() or {}
            total_days = result.get('total_days', 0) or 0
            present_days = result.get('present_days', 0) or 0
            absent_days = total_days - present_days

            no_of_work_days = current_aca_id.total_no_of_working_days if current_aca_id else 0

            academic_fee_id = self.env['ala.student.fees'].search([
                ('student_id', '=', record.id),
                ('academic_year_id', '=', current_aca_id.id)
            ], limit=1)

            total_fees = academic_fee_id.final_amount_total if academic_fee_id else 0
            paid_fees = academic_fee_id.amount_paid if academic_fee_id else 0
            remaining_fees = academic_fee_id.amount_unpaid if academic_fee_id else 0
            overdue_amount = academic_fee_id.amount_due if academic_fee_id else 0

            attendance_percentage = 0
            if total_days > 0:
                attendance_percentage = round((present_days / total_days) * 100, 2)

            # Dynamic color
            if attendance_percentage >= 75:
                progress_color = "#2e7d32"
            elif attendance_percentage >= 50:
                progress_color = "#f9a825"
            else:
                progress_color = "#c62828"

            # =========================
            # FEES (Replace With Real Calculation If Needed)
            # =========================
            academic_fee_id = self.env['ala.student.fees'].search(
                [('student_id', '=', record.id), ('academic_year_id', '=', current_aca_id.id)], limit=1)
            total_fees = academic_fee_id.final_amount_total
            paid_fees = academic_fee_id.amount_paid
            remaining_fees = academic_fee_id.amount_unpaid
            overdue_amount = academic_fee_id.amount_due

            # =========================
            # STYLES
            # =========================
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
                f"margin-top: 8px;"
                "font-size: 14px;"
                "font-weight: 600;"
                f"color: {progress_color};"
                "text-align: right;"
            )

            # =========================
            # FINAL HTML
            # =========================
            student_html = f"""
                    <div style="{main_container_style}">

                        <!-- Attendance Section -->
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

                        <!-- Fees Section -->
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

            record.student_html = student_html

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

    # @api.onchange('class_division_id')
    # def _onchange_class_division_id(self):
    #     """Method for checking the maximum number of students in a class"""
    #     for rec in self:
    #         if rec.class_division_id.actual_strength<len(rec.class_division_id.student_ids):
    #             raise ValidationError("The number of students exceeds the "
    #                                   "maximum strength of the class division.")

    def update_password(self):
        portal_group = self.env.ref('base.group_portal')

        for student in self:
            if student.drop_out or student.tc_issued:
                continue

            if not student.register_no:
                raise ValidationError("Register No not found for student %s" % student.name)

            if not student.date_of_birth:
                raise ValidationError("Date of Birth not found for student %s" % student.name)

            login = student.register_no
            password = student.date_of_birth.strftime('%d%m')  # Example: 05 Jan = 0501

            vals = {
                'name': student.name,
                'login': login,
                'password': password,
                'group_ids': [(6, 0, [portal_group.id])],
            }

            if student.partner_id:
                vals['partner_id'] = student.partner_id.id

            if student.user_id:
                student.user_id.sudo().write(vals)
                user = student.user_id
            else:
                existing_user = self.env['res.users'].sudo().search([
                    ('login', '=', login)
                ], limit=1)

                if existing_user:
                    raise ValidationError(
                        "Login '%s' already exists for user '%s'. "
                        "Please change the Register No."
                        % (login, existing_user.name)
                    )

                user = self.env['res.users'].sudo().create(vals)
                student.user_id = user.id

            student.login = login
            student.ch_password = password
