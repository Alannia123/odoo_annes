# -*- coding: utf-8 -*-
{
    'name': "Student Portal - Transfer Certificate",
    'summary': "Bridge: lets a parent download an issued T.C. from the student portal",
    'description': """
Student Portal - Transfer Certificate
=====================================
Pure bridge module. It owns no data of its own and is installed only when both
`ala_student_portal` and `ala_education_tc` are present, so neither of those
modules has to know the other exists.

* Adds a "Transfer Certificate" block to /school/student_info
* Download icon when an approved (issued) T.C. exists
* "Being processed" notice when a T.C. exists but the Principal has not
  approved it yet
* "Contact the school office" notice when there is none
""",
    'author': "Alannia Infotech",
    'website': "https://alanniainfotechz.online",
    'category': 'Education',
    'version': '19.0.1.0.0',
    'license': 'AGPL-3',
    'depends': ['ala_student_portal', 'ala_education_tc'],
    'data': [
        'views/student_info_tc_template.xml',
    ],
    'installable': True,
    'application': False,
    # Installs itself the moment both sides are present.
    'auto_install': True,
}
