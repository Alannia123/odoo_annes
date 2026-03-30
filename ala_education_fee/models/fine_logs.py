from odoo import models, fields, api
from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class StudentFineLog(models.Model):
    _name = "ala.student.fine.log"
    _description = "Student Fine Change Log"
    _order = "create_date desc"

    student_id = fields.Many2one('res.partner', string="Student")
    fee_line_id = fields.Many2one('ala.student.fee.line', string="Fee Line")
    academic_year_id = fields.Many2one('ala.education.academic.year', string="Academic Year")

    old_amount = fields.Float("Old Fine Amount")
    new_amount = fields.Float("New Fine Amount")

    changed_by = fields.Many2one('res.users', string="Changed By")
    change_date = fields.Datetime("Changed On", default=fields.Datetime.now)