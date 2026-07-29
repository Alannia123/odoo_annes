# -*- coding: utf-8 -*-
{
    'name': 'ALA Education Exam - Grade & Mark Entry',
    'version': '19.0.1.0.0',
    'category': 'School',
    'summary': 'Per-subject exam patterns, configurable grade scale and '
               'mobile-safe teacher mark entry.',
    'description': """
Foundation layer for the new grade configuration (session 2026-27).

 * Extends ala.education.class.subject with a per-cycle assessment pattern
   (Unit / Terminal), each with written + internal component caps and an
   evaluation mode (Marks vs Grade-only).
 * Adds a configurable, band-aware grade scale that replaces the hard-coded
   percentage ladder.
 * Reworks the valuation line so totals, pass/fail and grade are *computed
   and stored* (works for ORM/REST writes from the mobile app) and caps are
   enforced via constraints rather than onchange.
""",
    'author': 'Alanniainfotechz',
    'company': 'Alanniainfotechz',
    'maintainer': 'Alanniainfotechz',
    'depends': ['ala_education_exam'],
    'data': [
        'security/ir.model.access.csv',
        'data/grade_scale_data.xml',
        'views/grade_scale_views.xml',
        'views/education_class_subject_views.xml',
        'views/exam_valuation_views.xml',
        'views/exam_valuation_views.xml',
        'views/exam_valuation_views.xml',
        'reports/rank_card_action.xml',
        'reports/rank_card_template.xml',
        'reports/student_ir_action.xml',
        'reports/student_rank_card_temp.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}