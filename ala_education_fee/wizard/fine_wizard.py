from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import get_lang


class FineAmountConfig(models.TransientModel):
    _name = "ala.fine.remove.wizard"
    _description = "invoice Generate Wizard"

    ex_fine_amount = fields.Float('Existing Fine Amount', readonly=True)
    fine_amount = fields.Float('Fine Amount', readonly=False)
    fee_line_id = fields.Many2one('ala.student.fee.line', 'Student Fee Line', readonly=True)

    def update_fine_amount(self):
        old_amount = self.fee_line_id.fine_amount

        # update fine
        self.fee_line_id.fine_amount = self.fine_amount

        # create log
        self.env['ala.student.fine.log'].create({
            'student_id': self.fee_line_id.student_id.id,
            'fee_line_id': self.fee_line_id.id,
            'academic_year_id': self.fee_line_id.academic_year_id.id,
            'old_amount': old_amount,
            'new_amount': self.fine_amount,
            'changed_by': self.env.user.id,
            'change_date': fields.Datetime.now(),
        })


