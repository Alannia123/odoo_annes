# Copyright 2018, 2021 Heliconia Solutions Pvt Ltd (https://heliconia.io)

{
    "name": "Menu Category",
    "summary": """

        Odoo 17.0 community backend Category wise Menu Dashboard

    """,
    "author": "Heliconia Solutions Pvt. Ltd.",
    "website": "https://heliconia.io",
    "category": "Tools",
    "version": "19.0.1.0.0",
    "depends": ["web_responsive", 'ala_education_core'],
    "license": "OPL-1",
    "price": 5.00,
    "currency": "EUR",
    "data": [
        "security/ir.model.access.csv",
        "views/ir_ui_menu.xml",
        "views/ir_ui_menu_category.xml",
    ],
    "assets": {
    "web.assets_backend": [
        "hspl_menu_category/static/src/less/hspl_menu_category.scss",
        "hspl_menu_category/static/src/js/hspl_web_navbar.esm.js",
        "hspl_menu_category/static/src/js/hspl_apps_menu.esm.js",
        "hspl_menu_category/static/src/xml/apps_category.xml",
        # 'your_module/static/src/js/mobile_menu_fix.js',
    ],
},
    "images": ["static/description/heliconia_menu_category.gif"],
    "installable": True,
    "auto_install": False,
    "application": True,
}
