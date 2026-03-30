# -*- coding: utf-8 -*-

from odoo import fields, models, api


class RankCard(models.TransientModel):
    _name = 'ala.rank.wizard'
    _description = 'Rank Card'

    class_div_id = fields.Many2one(
        'ala.education.class.division',
        string='Select Class',
        required=True,
        domain="[('academic_year_id', '=', academic_year_id)]"
    )
    academic_year_id = fields.Many2one(
        'ala.education.academic.year',
        string='Academic Year',
        required=True,
        default=lambda self: self.env['ala.education.academic.year'].search(
            [('enable', '=', True)],
            limit=1
        )
    )

    @api.onchange('academic_year_id')
    def _onchange_academic_year(self):
        self.class_div_id = False


    def action_generate_pdf(self):
        data = {
            'class_div_id': self.class_div_id.id,
            'academic_year_id': self.academic_year_id.id,
        }
        return self.env.ref(
            'ala_education_exam.action_generate_rank_card'
        ).report_action(self, data=data)