from odoo import models, fields, api, _

class AttendanceDuplicateWizard(models.TransientModel):
    _name = 'attendance.duplicate.wizard'
    _description = 'Duplicate Attendance Warning'

    message = fields.Text(string="Message", readonly=True)
    existing_id = fields.Many2one('ala.education.attendance', string="Existing Attendance", readonly=True)
    division_id = fields.Many2one('ala.education.class.division', domain=[('current_year', '=', True)],
                                  string='Division', required=True,
                                  help="Class division for attendance")
    date = fields.Date(string='Date', default=fields.Date.today, required=True,
                       help="Attendance date", readonly=True)

    def action_open_existing(self):
        """Open the existing attendance record."""
        self.ensure_one()
        existing_attendance = self.sudo().search([
            ('division_id', '=', self.division_id.id),
            ('date', '=', self.date),
        ], order='id asc')

        if len(existing_attendance) > 1:
            # Keep the first (oldest)
            first_record = existing_attendance[0]

            # Delete all others
            duplicates = existing_attendance - first_record
            duplicates.sudo().unlink()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Existing Attendance'),
            'res_model': 'ala.education.attendance',
            'res_id': self.existing_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        """Simply close the wizard."""
        return {'type': 'ir.actions.act_window_close'}
