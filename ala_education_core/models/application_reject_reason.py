# -*- coding: utf-8 -*-

from odoo import fields, models


class ApplicationRejectReason(models.Model):
    """Used for managing reject reasons of applications"""
    _name = 'ala.application.reject.reason'
    _description = 'Reject ReasonS'

    name = fields.Char(string="Reason", required=True,
                       help="Possible Reason for rejecting the Applications")



class TcIssueWizReason(models.Model):
    """Used for managing reject reasons of applications"""
    _name = 'ala.tc.issue.wizard.reason'
    _description = 'Tc Issue ReasonS'

    name = fields.Char(string="Reason", required=True,
                       help="Possible Reason for TC issue")



class DropWizReason(models.Model):
    """Used for managing reject reasons of applications"""
    _name = 'ala.dropout.wizard.reason'
    _description = 'Drop ReasonS'

    name = fields.Char(string="Reason", required=True,
                       help="Possible Reason for TC issue")



class AlaFacultyLeftReason(models.Model):
    _name = 'ala.faculty.left.reason'
    _description = 'Faculty Left Reason'

    name = fields.Char(required=True)
