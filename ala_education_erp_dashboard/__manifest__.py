# -*- coding: utf-8 -*-

{
    'name': 'ALA Educational ERP Dashboard',
    'version': '19.0.2.0.0',
    'category': 'Industries, Productivity',
    'summary': 'An integrated view of the education ERP system',
    'description': """A comprehensive module designed to provide educational
                    institutions to manage and monitor various operations""",
    'author': "Alanniainfotechz",
    'company': 'Alanniainfotechz',
    'maintainer': 'Alanniainfotechz',
    'depends': ['base', 'ala_education_attendances', 'ala_education_promotion',
                'ala_education_exam', 'ala_education_time_table'],
    'data': [
        'security/education_security.xml',
        'security/ir.model.access.csv',
        'views/erp_dashboard_views.xml',
        'views/ala_announcement_views.xml'],
    'assets': {
        'web.assets_backend': [
            'ala_education_erp_dashboard/static/src/css/dashboard.css',
            'ala_education_erp_dashboard/static/src/js/dashboard.js',
            'ala_education_erp_dashboard/static/src/xml/erp_dashboard_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
