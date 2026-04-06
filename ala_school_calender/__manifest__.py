# -*- coding: utf-8 -*-

{
    'name': 'ALA School Calendar',
    'version': '19.0.1.0.1',
    'category': 'Extra Tools',
    'summary': """Calendar for Education erp""",
    'description': """Education Time Table provides a comprehensive timetable 
     management system, enhancing the functionality of  educational 
     institutions.""",
    'author': 'Alanniainfotechz',
    'company': 'Alanniainfotechz',
    'maintainer': 'Alanniainfotechz',
    'depends': ['ala_education_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/calendar_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
