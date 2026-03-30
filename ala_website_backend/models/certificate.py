from odoo import models, fields, api

class CertificateMaster(models.Model):
    _name = "ala.certificate"
    _description = "Certificate Configuration"


    name = fields.Char("Certificate Name", required=True)
    academic_year_id = fields.Many2one("ala.education.academic.year", required=True)
    certificate_type = fields.Selection([
        ('participation', "Participation"),
        ('winner', "Winners"),
        ('custom', "Custom"),
        ('photo', "Photo"),
    ], required=True)

    template_background = fields.Binary("Certificate Background (Image)")
    student_line_ids = fields.One2many("ala.certificate.line", "certificate_id", string="Students")

    # School details
    school_name = fields.Char("School Name")
    school_subtitle = fields.Char("School Subtitle")
    certificate_title_line1 = fields.Char("Certificate Title Line 1", default="CERTIFICATE")
    certificate_title_line2 = fields.Char("Certificate Title Line 2", default="OF EXCELLENCE")
    presented_text = fields.Char("Presented Text", default="This certificate is presented to")
    description_text = fields.Text(
        "Description Text",
        default="In recognition of outstanding performance, creativity, and active participation in the Science Expo 2025 conducted by Mary Immaculate English Medium School."
    )
    issued_date = fields.Date("Issued Date")

    # Logo / medal / QR
    school_logo = fields.Binary("School Logo")
    qr_code_image = fields.Binary("QR Code")
    medal_type = fields.Selection([
        ('none', "None"),
        ('gold', "Gold"),
        ('silver', "Silver"),
        ('bronze', "Bronze"),
    ], string="Medal Type", default='none')

    # Optional custom medal images
    medal_gold_image = fields.Binary("Gold Medal Image")
    medal_silver_image = fields.Binary("Silver Medal Image")
    medal_bronze_image = fields.Binary("Bronze Medal Image")

    # Signatures
    left_sign_name = fields.Char("Left Signatory Name")
    left_sign_role = fields.Char("Left Signatory Role")
    left_sign_image = fields.Binary("Left Signature Image")

    right_sign_name = fields.Char("Right Signatory Name")
    right_sign_role = fields.Char("Right Signatory Role")
    right_sign_image = fields.Binary("Right Signature Image")

    # Fonts
    font_family = fields.Selection([
        ('Arial, sans-serif', 'Arial'),
        ('"Times New Roman", serif', 'Times New Roman'),
        ('Georgia, serif', 'Georgia'),
        ('"Trebuchet MS", sans-serif', 'Trebuchet MS'),
        ('Verdana, sans-serif', 'Verdana'),
        ('"Courier New", monospace', 'Courier New'),
    ], string="Font Family", default='Arial, sans-serif')

    # Colors
    primary_color = fields.Char("Primary Color", default="#1d2b5f")
    secondary_color = fields.Char("Secondary Color", default="#69b8b2")
    wave_color = fields.Char("Wave Color", default="#7cc8c3")
    background_opacity = fields.Float("Background Opacity", default=0.12)

    def get_selected_medal_image(self):
        self.ensure_one()
        if self.medal_type == 'gold':
            return self.medal_gold_image
        elif self.medal_type == 'silver':
            return self.medal_silver_image
        elif self.medal_type == 'bronze':
            return self.medal_bronze_image
        return False


class CertificateLine(models.Model):
    _name = "ala.certificate.line"
    _description = "Certificate Students"

    certificate_id = fields.Many2one("ala.certificate", ondelete="cascade")
    student_id = fields.Many2one("ala.education.student", required=True)
    position = fields.Selection([
        ('first', "First Place"),
        ('second', "Second Place"),
        ('third', "Third Place"),
        ('none', "Participation"),
    ], default="none")

    certificate_url = fields.Char("Download URL", compute="_compute_url")

    def _compute_url(self):
        for rec in self:
            rec.certificate_url = f"/my/certificate/{rec.id}"

