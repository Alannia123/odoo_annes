{
    'name': 'Sales Terms Voice Input',
    'version': '19.0.1.0.0',
    'summary': 'Fill sales text fields using voice input.',
    'author': 'OpenAI',
    'category': 'Sales/Sales',
    'depends': ['web', 'sale'],
    'data': [
        'views/sale_order_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'voice_to_text/static/src/scss/voice_to_text.scss',
            'voice_to_text/static/src/js/voice_to_text_widget.js',
            'voice_to_text/static/src/xml/voice_button.xml',
            'voice_to_text/static/src/xml/voice_widget.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
