{
    # App Information
    'name': 'Chatter Sidebar Right',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'summary': 'Keep the backend form chatter on the right side in wide layouts with an optional user-wise preference toggle (right chatter panel, chatter sidebar right, form chatter position, backend chatter layout, side chatter, Odoo chatter alignment, form view chatter, responsive chatter, mail chatter UI, chatter panel layout).',
    'description': """
    Chatter Sidebar Right
    =====================

    Keeps the Odoo backend chatter aligned on the right side of form views by
    overriding the compiled form layout and forcing a single aside chatter
    container when the current user enables the preference. The module combines
    a focused frontend asset with a lightweight user preference for Odoo 19 and
    is designed to remain stable when browser zoom or viewport changes would
    otherwise move the chatter below the form.
    """,
    'category': 'tools',

    # Author
    'author': 'Techno Stellar',
    'maintainer': 'Techno Stellar',

    # Dependencies
    'depends': ['mail', 'web'],

    'data': [
        'views/res_users_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'chatter_sidebar_right_tspl/static/src/js/form_compiler_patch.js',
            'chatter_sidebar_right_tspl/static/src/scss/chatter_sidebar_right.scss',
        ],
    },

    'images': ['static/description/chatter_sidebar_banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,

    # Pricing
    'price': 0.0,
    'currency': 'EUR',
}
