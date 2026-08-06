# -*- coding: utf-8 -*-
{
    'name': "Education - Transfer Certificate (TC)",
    'summary': "Manual-entry Transfer Certificate with an exact QWeb replica of the printed school TC form",
    'description': """
Transfer Certificate
====================
* Manual data entry form (no dependency on the student master - optional link possible)
* Auto TC numbering via ir.sequence
* Gender aware pronouns (He/She, his/her)
* Date of birth auto-converted to words (e.g. FOURTH JUNE TWO THOUSAND TWELVE)
* Pixel-faithful A4 QWeb/PDF replica of the pre-printed TC stationery
* Separate "Blank Form" report for pre-printing empty stationery
* Principal-only approval workflow (Draft -> Waiting Approval -> Issued)
* Sequence-based verification QR printed bottom-right, with a public
  /tc/verify/<id>/<token> landing page
""",
    'author': "Alannia Infotech",
    'website': "https://alanniainfotechz.online",
    'category': 'Education',
    'version': '19.0.1.1.0',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'ala_education_core', 'ala_website_backend'],
    'data': [
        'security/tc_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/report_paperformat.xml',
        'report/tc_template.xml',
        'report/tc_report.xml',
        'views/tc_verify_template.xml',
        'views/res_company_views.xml',
        'views/transfer_certificate_views.xml',
        'views/tc_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
