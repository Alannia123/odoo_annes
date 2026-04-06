# -*- coding: utf-8 -*-
{
    'name': 'ALA Accounting Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Accounting ',
    'summary': 'Odoo Accounting Dashboard, Accounting Dashboard V19, Account Dashboard, Dashboard, Odoo19 Accounting, Odoo19 Dashboard',
    'description': """Accounting, Odoo Accounting Dashboard, Accounting Dashboard V19, Account Dashboard, Dashboard, Invoice Dashboard, Invoice Graph View, Odoo19""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://cybrosys.com',
    'depends': ['base_accounting_kit','ala_education_fee'],
    'data': [
        'data/account_move_data.xml',
        'reports/today_payment_summary.xml',
    ],
    'assets':{
        'web.assets_backend':[
            'ala_accounting_dashboard/static/src/js/lib/chart/chart.min.js',
            'ala_accounting_dashboard/static/src/xml/accounting_dashboard.xml',
            'ala_accounting_dashboard/static/src/js/accounting_dashboard.js',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
