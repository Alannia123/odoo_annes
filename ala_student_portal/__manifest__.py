# -*- coding: utf-8 -*-

{
    'name': 'ALA Student Portal',
    'version': '19.0.1.0.0',
    'category': 'School',
    'summary': """Manage the ALA School Website Student Portal""",
    'description': """This modules helps to organize the website student portal""",
    'author': 'Alannia',
    'company': 'alanniainfotechz',
    'maintainer': 'Alanniainfotechz',
    'depends': ['web','website','portal', 'account', 'ala_education_erp_dashboard',
                'ala_homework', 'ala_school_calender', 'ala_education_fee'],
    'external_dependencies': {'python': ['razorpay']},
    'data': [
        # 'security/ir.model.access.csv',
        # 'data/web_menu.xml',
        'views/res_config_settings_views.xml',
        'views/student_account_template.xml',
        'views/announce_template.xml',
        'views/home_work_template.xml',
        'views/student_info_temp.xml',
        'views/time_table_template.xml',
        'views/class_comm.xml',
        'views/attendance_template.xml',
        'views/teacher_stu_view.xml',
        'views/payments_template.xml',
        'views/portal_breadcrumbs.xml',
        'views/result_template.xml',

    ],

    # 'assets': {
    #     'web.assets_backend': [
    #         '/ala_website/static/src/js/video_field.xml'
    #         '/ala_website/static/src/js/video_field.js'
    #     ],
    # },
    'assets': {
        'web.assets_frontend': [
                'https://cdn.jsdelivr.net/npm/chart.js',
            # '/ala_student_portal/static/src/js/portal_tts.js',
            # '/ala_student_portal/static/src/css/dashboard.css',
            # '/ala_website/static/src/css/sample.css',
        ],
    },


    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
