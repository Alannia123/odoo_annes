# -*- coding: utf-8 -*-
import logging
import re
from datetime import datetime, time

import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

DEFAULT_TZ = 'Asia/Kolkata'


class FacultyAttendanceSheet(models.Model):
    """Daily attendance sheet for faculty / staff (hr.employee based)."""
    _name = 'ala.faculty.attendance.sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Faculty Daily Attendance Sheet'
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Name', compute='_compute_name', store=True,
                       help='Name of the attendance sheet')
    date = fields.Date(string='Date', required=True, tracking=True,
                       default=fields.Date.context_today,
                       help='Attendance date')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company, help='Current company')
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done')], default='draft',
        string='State', tracking=True, help='Stage of the attendance sheet')
    line_ids = fields.One2many(
        'ala.faculty.attendance.sheet.line', 'sheet_id',
        string='Attendance Lines', help='Faculty attendance lines')
    absent_roll_nos = fields.Char(
        string='Leave Roll Nos', copy=False,
        help="Enter ONLY roll numbers of staff on leave, comma / space "
             "separated. Ranges supported, e.g. '3, 7, 10-12'. Everyone "
             "else stays Present. Adjust On Duty / Med Leave on the lines.")
    total_count = fields.Integer(compute='_compute_counts', string='Total')
    present_count = fields.Integer(compute='_compute_counts', string='Present',
                                   help='Present + On Duty')
    leave_count = fields.Integer(compute='_compute_counts', string='On Leave',
                                 help='Leave + Med Leave')
    auto_closed = fields.Boolean(string='Auto Closed', readonly=True, copy=False,
                                 help='Set when the end-of-day cron validated this sheet')

    _sql_constraints = [
        ('date_company_uniq', 'unique(date, company_id)',
         'A faculty attendance sheet already exists for this date.'),
    ]

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('date')
    def _compute_name(self):
        for rec in self:
            rec.name = _('Faculty Attendance - %s') % (
                rec.date.strftime('%d/%m/%Y') if rec.date else _('New'))

    @api.depends('line_ids.status')
    def _compute_counts(self):
        for rec in self:
            rec.total_count = len(rec.line_ids)
            rec.present_count = len(rec.line_ids.filtered(
                lambda l: l.status in ('present', 'on_duty')))
            rec.leave_count = len(rec.line_ids.filtered(
                lambda l: l.status in ('leave', 'med_leave')))

    # ------------------------------------------------------------------
    # Line generation
    # ------------------------------------------------------------------
    def _get_faculty_employees(self):
        self.ensure_one()
        employees = self.env['hr.employee'].search([
            ('faculty_attendance_active', '=', True),
            ('faculty_roll_no', '>', 0),
            ('company_id', '=', self.company_id.id),
        ])
        return employees.sorted(key=lambda e: e.faculty_roll_no)

    def _create_lines(self, raise_if_empty=True):
        Line = self.env['ala.faculty.attendance.sheet.line']
        for rec in self:
            if rec.line_ids:
                continue
            employees = rec._get_faculty_employees()
            if not employees:
                if raise_if_empty:
                    raise UserError(_(
                        'No employees found with "Include in Faculty '
                        'Attendance" enabled and a Faculty Roll No set.'))
                _logger.warning(
                    'Faculty attendance %s: no eligible employees found.',
                    rec.display_name)
                continue
            values = [{
                'sheet_id': rec.id,
                'employee_id': emp.id,
                'roll_no': emp.faculty_roll_no,
            } for emp in employees]
            Line.create(values)  # single batch create

    def action_create_lines(self):
        self._create_lines(raise_if_empty=True)

    # ------------------------------------------------------------------
    # Absent roll no quick entry
    # ------------------------------------------------------------------
    @api.model
    def _parse_roll_tokens(self, text):
        """'3, 7 10-12' -> {3, 7, 10, 11, 12}. Raises on garbage input."""
        rolls = set()
        for token in re.split(r'[,\s]+', (text or '').strip()):
            if not token:
                continue
            m = re.fullmatch(r'(\d+)\s*-\s*(\d+)', token)
            if m:
                start, end = int(m.group(1)), int(m.group(2))
                if start > end:
                    start, end = end, start
                rolls.update(range(start, end + 1))
            elif token.isdigit():
                rolls.add(int(token))
            else:
                raise ValidationError(_(
                    "Invalid roll number token: '%s'. Use numbers, commas, "
                    "spaces or ranges like 10-12.") % token)
        return rolls

    def action_apply_absent_rolls(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Sheet is already validated.'))
            if not rec.line_ids:
                rec._create_lines()
            absent_rolls = rec._parse_roll_tokens(rec.absent_roll_nos)
            line_rolls = set(rec.line_ids.mapped('roll_no'))
            unknown = absent_rolls - line_rolls
            if unknown:
                raise ValidationError(_(
                    'Roll no(s) %s do not exist in this sheet.')
                    % ', '.join(map(str, sorted(unknown))))
            for line in rec.line_ids:
                line.status = 'leave' if line.roll_no in absent_rolls \
                    else 'present'

    def action_mark_all_present(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Sheet is already validated.'))
            if not rec.line_ids:
                rec._create_lines()
            rec.line_ids.write({'status': 'present'})
            rec.absent_roll_nos = False

    # ------------------------------------------------------------------
    # hr.attendance generation
    # ------------------------------------------------------------------
    def _company_tz(self):
        self.ensure_one()
        tz_name = (self.company_id.resource_calendar_id.tz
                   or self.env.user.tz or DEFAULT_TZ)
        try:
            return pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            return pytz.timezone(DEFAULT_TZ)

    @api.model
    def _float_to_utc(self, day, float_hour, tz):
        """Local school time (float, e.g. 9.5) on `day` -> naive UTC datetime
        as stored by hr.attendance."""
        hours = int(float_hour)
        minutes = int(round((float_hour - hours) * 60))
        local_dt = tz.localize(datetime.combine(day, time(hours, minutes)))
        return local_dt.astimezone(pytz.utc).replace(tzinfo=None)

    def _generate_hr_attendances(self):
        """Create one hr.attendance per Present / On Duty line.
        Idempotent (skips lines already linked) and skips employees who
        already have an overlapping attendance (e.g. biometric punch)."""
        Attendance = self.env['hr.attendance'].sudo()
        for rec in self:
            tz = rec._company_tz()
            company = rec.company_id
            check_in = self._float_to_utc(
                rec.date, company.faculty_check_in_time or 9.0, tz)
            out_full = self._float_to_utc(
                rec.date, company.faculty_check_out_time or 16.0, tz)
            if out_full <= check_in:
                raise UserError(_(
                    'Faculty check-out time must be after check-in time. '
                    'Fix the times on company "%s".') % company.name)

            todo, vals_list, skipped = [], [], []
            for line in rec.line_ids:
                if line.attendance_id or line.status not in (
                        'present', 'on_duty'):
                    continue
                check_out = out_full
                overlap = Attendance.search_count([
                    ('employee_id', '=', line.employee_id.id),
                    ('check_in', '<', check_out),
                    '|', ('check_out', '=', False),
                    ('check_out', '>', check_in),
                ])
                if overlap:
                    skipped.append(line.employee_id.name)
                    continue
                todo.append(line)
                vals_list.append({
                    'employee_id': line.employee_id.id,
                    'check_in': check_in,
                    'check_out': check_out,
                })
            if vals_list:
                attendances = Attendance.create(vals_list)
                for line, attendance in zip(todo, attendances):
                    line.attendance_id = attendance.id
            if skipped:
                rec.message_post(body=_(
                    'HR Attendance NOT generated for %s: an overlapping '
                    'attendance record already exists (biometric/manual '
                    'punch).') % ', '.join(skipped))

    def _remove_hr_attendances(self):
        self.line_ids.attendance_id.sudo().unlink()

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def _validate_sheet(self, auto=False):
        for rec in self:
            if rec.state != 'draft':
                continue
            if not rec.line_ids:
                raise UserError(_('Create attendance lines before validating.'))
            if rec.absent_roll_nos:
                rec.action_apply_absent_rolls()
            rec._generate_hr_attendances()
            rec.write({'state': 'done', 'auto_closed': auto})

    def action_done(self):
        self._validate_sheet(auto=False)

    def action_reset_draft(self):
        self._remove_hr_attendances()
        self.write({'state': 'draft', 'auto_closed': False})

    def unlink(self):
        if any(rec.state == 'done' for rec in self):
            raise UserError(_('Validated attendance sheets cannot be deleted. '
                              'Reset to draft first.'))
        return super().unlink()

    # ------------------------------------------------------------------
    # Crons
    # ------------------------------------------------------------------
    @api.model
    def _company_local_date(self, company):
        tz_name = (company.resource_calendar_id.tz
                   or self.env.user.tz or DEFAULT_TZ)
        try:
            tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            tz = pytz.timezone(DEFAULT_TZ)
        return datetime.now(pytz.utc).astimezone(tz).date()

    @api.model
    def _cron_auto_create(self):
        """Morning cron: create today's sheet with lines (idempotent).
        Skips Sundays. Adjust the weekday filter for the school's calendar."""
        for company in self.env['res.company'].search([]):
            today = self._company_local_date(company)
            if today.weekday() == 6:  # Sunday
                continue
            exists = self.search_count([
                ('date', '=', today), ('company_id', '=', company.id)])
            if exists:
                continue
            sheet = self.with_company(company).create({
                'date': today, 'company_id': company.id})
            sheet._create_lines(raise_if_empty=False)
            _logger.info('Auto-created faculty attendance sheet %s',
                         sheet.display_name)

    @api.model
    def _cron_auto_close(self):
        """End-of-day cron: apply pending absent roll nos, mark the rest
        present, and validate every draft sheet whose date has passed."""
        for company in self.env['res.company'].search([]):
            today = self._company_local_date(company)
            sheets = self.search([
                ('state', '=', 'draft'),
                ('company_id', '=', company.id),
                ('date', '<=', today),
            ])
            for sheet in sheets:
                try:
                    if not sheet.line_ids:
                        sheet._create_lines(raise_if_empty=False)
                    if not sheet.line_ids:
                        continue  # nothing to close, leave in draft
                    sheet._validate_sheet(auto=True)
                    sheet.message_post(body=_(
                        'Sheet auto-validated by end-of-day scheduler. '
                        'Present/On Duty: %(p)s / %(t)s, On Leave: %(a)s',
                        p=sheet.present_count, t=sheet.total_count,
                        a=sheet.leave_count))
                except Exception:
                    _logger.exception(
                        'Auto-close failed for faculty attendance sheet %s',
                        sheet.display_name)
                    self.env.cr.rollback()


class FacultyAttendanceSheetLine(models.Model):
    _name = 'ala.faculty.attendance.sheet.line'
    _description = 'Faculty Daily Attendance Line'
    _order = 'roll_no, id'
    _rec_name = 'employee_id'

    sheet_id = fields.Many2one(
        'ala.faculty.attendance.sheet', string='Attendance Sheet',
        required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Faculty', required=True, index=True)
    roll_no = fields.Integer(string='Roll No', required=True,
                             help='Roll no snapshot at sheet creation time')
    date = fields.Date(related='sheet_id.date', store=True)
    company_id = fields.Many2one(related='sheet_id.company_id', store=True)
    state = fields.Selection(related='sheet_id.state', store=True)
    status = fields.Selection([
        ('present', 'Present'),
        ('leave', 'Leave'),
        ('on_duty', 'On Duty'),
        ('med_leave', 'Med Leave'),
    ], string='Status', default='present', required=True)
    remarks = fields.Char(string='Remarks')
    attendance_id = fields.Many2one(
        'hr.attendance', string='HR Attendance', readonly=True, copy=False,
        ondelete='set null', index=True,
        help='hr.attendance record generated when the sheet was validated')

    _sql_constraints = [
        ('sheet_employee_uniq', 'unique(sheet_id, employee_id)',
         'Employee already exists in this attendance sheet.'),
    ]
