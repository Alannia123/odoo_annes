# -*- coding: utf-8 -*-

from odoo import fields, models, api


class RankCard(models.TransientModel):
    _inherit = 'ala.rank.wizard'
    _description = 'Rank Card'




    def action_generate_pdf(self):
        data = {
            'class_div_id': self.class_div_id.id,
            'academic_year_id': self.academic_year_id.id,
        }
        return self.env.ref(
            'ala_exam_extend.action_generate_rank_card'
        ).report_action(self, data=data)