{
    "name": "ALA Binance Paper Trader",
    "version": "19.0.1.0.0",
    "summary": "Binance market monitoring and paper futures trading in Odoo 19",
    "category": "Tools",
    "author": "Alanniainfotechz",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/strategy_config_views.xml",
        "views/market_snapshot_views.xml",
        "views/paper_trade_views.xml",
        "views/trade_journal_views.xml",
    ],
    "installable": True,
    "application": True,
}