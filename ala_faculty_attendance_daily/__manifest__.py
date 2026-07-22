# -*- coding: utf-8 -*-
{
    'name': 'ALA Faculty Daily Attendance (Sheet Based)',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Sheet-based daily attendance for faculty (hr.employee) with '
               'roll numbers, absent-roll-no quick entry and auto day-close cron',
    'depends': ['hr', 'hr_attendance', 'mail', 'ala_education_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/res_company_views.xml',
        'views/faculty_attendance_views.xml',
        'views/dashboard_views.xml',
        'views/education_faculty_views.xml',
        'wizard/faculty_attendance_report_views.xml',
        'data/ir_cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ala_faculty_attendance_daily/static/src/js/attendance_dashboard.js',
            'ala_faculty_attendance_daily/static/src/xml/attendance_dashboard.xml',
            'ala_faculty_attendance_daily/static/src/scss/attendance_dashboard.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
