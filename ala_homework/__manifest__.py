# -*- coding: utf-8 -*-

{
    'name': 'ALA School Education Homework Announcements',
    'version': '19.0.1.0.0',
    'category': 'School',
    'summary': """Manage the MIS School Website education system""",
    'description': """This modules helps to organize the website data and helps to update the website datas""",
    'author': 'Alannia',
    'company': 'alanniainfotechz',
    'maintainer': 'Alanniainfotechz',
    'depends': ['base','ala_education_core', 'ala_website_backend', 'voice_to_text'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'data/sequence.xml',
        'views/homework_lines.xml',
        'views/home_work_view.xml',
        # 'wizard/home_entry_wizard_view.xml',
    ],
    #  'assets': {
    #     'web.assets_backend': [
    #         # 'ala_website_backend/static/src/js/multi_upload.js',
    #         'ala_website_backend/static/src/js/document_multi_upload.js',
    #         'ala_website_backend/static/src/xml/document_multi_upload.xml'],
    # },

    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
