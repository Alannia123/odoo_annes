# -*- coding: utf-8 -*-
{
    'name': "Portal & Website Announcement Popup",
    'summary': "Time-bound image / message popups on the portal home and website home page.",
    'description': """
Announcement Popup
==================
Publish an image and/or a rich-text message as a modal popup that appears the
first time a visitor opens the website home page (``/``) or the portal home
page (``/my``, ``/my/home``).

Features
--------
* Image only / message only / image + message.
* Start date and **Show Until** date - the popup disappears on its own.
* Frequency: once, once per session, once per day, or every visit.
* Audience: everyone, public visitors only, logged-in users only, or a
  specific set of security groups (students, parents, faculty...).
* Optional call-to-action button.
* Editing a record resets the "already seen" flag so the new content shows again.
""",
    'version': '19.0.1.0.0',
    'category': 'Website',
    'license': 'LGPL-3',
    'author': "Alannia Infotechz",
    'website': "https://alanniainfotechz.online",
    'depends': ['base', 'portal', 'website'],
    'data': [
        'security/announcement_security.xml',
        'security/ir.model.access.csv',
        'views/portal_announcement_views.xml',
        'views/announcement_menus.xml',
        'templates/announcement_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ala_portal_announcement/static/src/scss/announcement_popup.scss',
            'ala_portal_announcement/static/src/js/announcement_popup.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
