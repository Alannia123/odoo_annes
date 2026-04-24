# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError



class TcIssue(models.TransientModel):
    """This model for providing a rejection explanation while
            rejecting an application."""
    _name = 'ala.tc.issue.reason'
    _description = 'TC Issue Reason'

    tc_issue_reason_id = fields.Many2one( 'ala.tc.issue.wizard.reason', string="TC Issue Reason", help="Give tc issue reason", required=True)

    def action_tc_issue_reason_apply(self):
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise UserError(_("No students selected."))
        students = self.env['ala.education.student'].browse(active_ids)
        students.write({
            'tc_issued': True,
            'tc_issue_reason_id': self.tc_issue_reason_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}



class Dropout(models.TransientModel):
    """This model for providing a rejection explanation while
            rejecting an application."""
    _name = 'ala.dropout.reason'
    _description = 'Dropout Reason'

    drop_out_reason_id = fields.Many2one( 'ala.dropout.wizard.reason', string="Dropout Reason", help="Give Dropout reason", required=True)

    def action_dropout_reason_apply(self):
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise UserError(_("No students selected."))
        students = self.env['ala.education.student'].browse(active_ids)
        students.write({
            'drop_out': True,
            'drop_out_reason_id': self.drop_out_reason_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}



class FacultyLeft(models.TransientModel):
    """This model for providing a rejection explanation while
            rejecting an application."""
    _name = 'ala.faculty.left'
    _description = 'Faculty Left Reason'

    faculty_left_reason_id = fields.Many2one('ala.faculty.left.reason', string="Left Reason")

    def action_faculty_left_reason_apply(self):
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise UserError(_("No Faculties selected."))
        students = self.env['ala.education.faculty'].browse(active_ids)
        students.write({
            'faculty_left': True,
            'faculty_left_reason_id': self.faculty_left_reason_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}
