# -*- coding: utf-8 -*-
{
    'name': 'Educational Time Table ALA',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Timetable management for education ERP',
    'description': 'Education Time Table provides a comprehensive timetable management system for educational institutions.',
    'author': 'Alanniainfotechz',
    'company': 'Alanniainfotechz',
    'maintainer': 'Alanniainfotechz',
    'depends': ['mail', 'ala_education_core'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/education_timetable_views.xml',
        'views/faculty_timetable_view.xml',
        'views/education_timetable_schedule_views.xml',
        'views/education_class_division_views.xml',
        'views/education_faculty_views.xml',
        'views/timetable_period_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'ala_education_time_table/static/src/css/style.css',
        ],
    },

    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
