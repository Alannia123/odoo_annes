# -*- coding: utf-8 -*-
{
    'name': 'ALA Fee Collection Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Student fee payment tracker and principal collection overview',
    'description': """
Fee Collection Dashboard
========================
* **Fee Payment Tracker** - one row per student, every fee visible as a
  colour-coded chip across an April-March grid.
* **Fee Collection Overview** - principal's view of money actually
  received: day-wise summary by payment mode, or receipt-level detail.
* Filters: student / register no, roll no, division, academic year,
  payment date range, status, mode.
* Export either view to XLSX or PDF; exports re-run the same server-side
  query as the screen, so they can never disagree.
    """,
    'author': 'Alannia',
    'company': 'alanniainfotechz',
    'maintainer': 'Alanniainfotechz',
    'license': 'LGPL-3',
    'depends': ['web', 'account', 'ala_education_fee', 'ala_education_core'],
    'data': [
        'report/fee_dashboard_report.xml',
        'report/fee_dashboard_template.xml',
        'report/principal_fee_overview_template.xml',
        'views/dashboard_action.xml',
        'views/principal_fee_overview_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ala_fee_dashboard/static/src/scss/fee_dashboard.scss',
            'ala_fee_dashboard/static/src/scss/principal_fee_overview.scss',
            'ala_fee_dashboard/static/src/js/fee_dashboard.js',
            'ala_fee_dashboard/static/src/js/principal_fee_overview.js',
            'ala_fee_dashboard/static/src/xml/fee_dashboard.xml',
            'ala_fee_dashboard/static/src/xml/principal_fee_overview.xml',
        ],
    },
    'external_dependencies': {'python': ['xlsxwriter']},
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}
