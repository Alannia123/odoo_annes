# -*- coding: utf-8 -*-

{
    'name': ' ALA School Education Management',
    'version': '19.0.1.0.0',
    'category': 'School',
    'summary': """Manage the MIS School Website education system""",
    'description': """This modules helps to organize the website data and helps to update the website datas""",
    'author': 'Alannia',
    'company': 'alanniainfotechz',
    'maintainer': 'Alanniainfotechz',
    'depends': ['web','website','ala_website_backend', 'ala_school_calender'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/web_menu.xml',
        # 'views/ala_home_template.xml',
        'views/home_zi.xml',
        'views/prospectus_template.xml',
        'views/academics_template.xml',
        'views/school_commitee_temp.xml',
        'views/events_gallery_s3_temp.xml',
        'views/razor_pay_templates.xml',
        'views/online_application_templates.xml',
        'views/e_magazine_view.xml',
        'views/web_menu.xml',
        'views/certificate_website.xml',
        'views/app_release_temp.xml',
        'views/school_calender_template.xml',
        # 'views/privacy_policy.xml',
        'views/website_header.xml',
        'views/login_logo.xml',

    ],

    # 'assets': {
    #     'web.assets_backend': [
    #         '/ala_website/static/src/js/video_field.xml'
    #         '/ala_website/static/src/js/video_field.js'
    #     ],
    # },
    'assets': {
        'web.assets_frontend': [
            '/ala_website/static/src/css/style.css',
            '/ala_website/static/src/css/login.css',
            # '/ala_website/static/src/css/sample.css',
            '/ala_website/static/src/js/online_application.js',
            '/ala_website/static/src/js/valaidate_js.js',
        ],
        'web.assets_backend': [
            '/ala_website/static/src/xml/form_status_indicator.xml',
            '/ala_website/static/src/css/form_status_indicator.scss',
        ],
    },


    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
