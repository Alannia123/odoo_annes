class AlaBinanceDailySummary(models.Model):
    _name = "ala.binance.daily.summary"
    _description = "Binance Daily Summary"
    _order = "summary_date desc"

    config_id = fields.Many2one("ala.binance.strategy.config", required=True, index=True)
    summary_date = fields.Date(required=True, index=True)
    daily_pnl = fields.Float()
    cumulative_pnl = fields.Float()
    equity_balance = fields.Float()
    trade_count = fields.Integer()
    win_count = fields.Integer()
    loss_count = fields.Integer()