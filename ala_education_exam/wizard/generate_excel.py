from odoo import models

class ExamMarksheetReport(models.AbstractModel):
    _name = 'report.ala_education_exam.exam_marksheet_template'
    _description = 'Exam Marksheet PDF Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['ala.education.exam.type'].browse(docids)
        print('wwwwwwwwwwwwwwwwwww',self)
        print('wwwwwwwwwwwwwwwwwwwdocids',docids)
        print('wwwwwwwwwwwwwwwwwwwdocs',docs)
        print('wwwwwwwwwwwwwwwwwwwdata',data)
        dfdfdf# adjust model
        return {
            'doc_ids': docs.ids,
            'doc_model': 'ala.education.exam.type',
            'docs': docs,
            'data': data,
        }
