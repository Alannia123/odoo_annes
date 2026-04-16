from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AlaBinanceStrategyConfig(models.Model):
    _name = "ala.binance.strategy.config"
    _description = "Binance Paper Trading Strategy Config"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, default="Default Strategy", tracking=True)
    active = fields.Boolean(default=True)

    btc_symbol = fields.Char(default="BTCUSDT", required=True)
    altcoin_symbols = fields.Char(default="ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,ADAUSDT")

    paper_capital = fields.Float(default=100.0, required=True)
    available_capital = fields.Float(default=100.0)
    trade_size_usdt = fields.Float(default=100.0, required=True)

    tp_percent = fields.Float(default=1.0, required=True)
    sl_percent = fields.Float(default=0.5, required=True)

    btc_lookback = fields.Integer(default=5)
    alt_lookback = fields.Integer(default=5)

    use_short = fields.Boolean(default=True)
    max_open_trades = fields.Integer(default=1)

    use_rsi = fields.Boolean(default=True)
    rsi_period = fields.Integer(default=14)
    rsi_long_min = fields.Float(default=55.0)
    rsi_short_max = fields.Float(default=45.0)

    use_macd = fields.Boolean(default=True)
    macd_fast = fields.Integer(default=12)
    macd_slow = fields.Integer(default=26)
    macd_signal = fields.Integer(default=9)

    use_ema_filter = fields.Boolean(default=True)
    ema_period = fields.Integer(default=20)

    # new strong filters
    use_adx = fields.Boolean(default=True)
    adx_period = fields.Integer(default=14)
    adx_min = fields.Float(default=20.0)

    use_volume_spike = fields.Boolean(default=True)
    volume_ma_period = fields.Integer(default=20)
    volume_spike_multiplier = fields.Float(default=1.5)

    use_atr_sl = fields.Boolean(default=True)
    atr_period = fields.Integer(default=14)
    atr_sl_multiplier = fields.Float(default=1.5)

    cooldown_minutes = fields.Integer(default=30)
    max_daily_loss_percent = fields.Float(default=3.0)

    use_sr_filter = fields.Boolean(default=True)
    sr_lookback = fields.Integer(default=20)
    sr_buffer_percent = fields.Float(default=0.4)

    btc_timeframe = fields.Selection([
        ('5m', '5m'),
        ('15m', '15m'),
        ('30m', '30m'),
        ('1h', '1h'),
    ], default='15m')

    alt_timeframe = fields.Selection([
        ('1m', '1m'),
        ('3m', '3m'),
        ('5m', '5m'),
        ('15m', '15m'),
    ], default='5m')

    state = fields.Selection([
        ("draft", "Draft"),
        ("running", "Running"),
        ("stopped", "Stopped"),
    ], default="draft")
    top_coin_limit = fields.Integer(default=10)
    min_quote_volume = fields.Float(
        default=50000000.0,
        help="Minimum 24h quote volume in USDT for coin eligibility"
    )
    allowed_quote_asset = fields.Char(default="USDT")
    excluded_symbols = fields.Char(
        default="BTCUSDT,USDCUSDT,BUSDUSDT,FDUSDUSDT,TUSDUSDT,ETHBTC",
        help="Comma separated symbols to ignore"
    )
    validate_symbols_on_scan = fields.Boolean(default=True)

    daily_realized_pnl = fields.Float(compute="_compute_dashboard_metrics", store=False)
    today_win_count = fields.Integer(compute="_compute_dashboard_metrics", store=False)
    today_loss_count = fields.Integer(compute="_compute_dashboard_metrics", store=False)
    today_trade_count = fields.Integer(compute="_compute_dashboard_metrics", store=False)
    equity_balance = fields.Float(compute="_compute_dashboard_metrics", store=False)

    def _compute_dashboard_metrics(self):
        journal_model = self.env["ala.binance.trade.journal"]
        today = fields.Date.context_today(self)
        for rec in self:
            journals = journal_model.search([
                ("config_id", "=", rec.id),
                ("trade_date", "=", today),
            ])
            rec.daily_realized_pnl = sum(journals.mapped("pnl_amount"))
            rec.today_trade_count = len(journals)
            rec.today_win_count = len(journals.filtered(lambda x: x.pnl_amount > 0))
            rec.today_loss_count = len(journals.filtered(lambda x: x.pnl_amount < 0))
            rec.equity_balance = (rec.paper_capital or 0.0) + sum(
                journal_model.search([("config_id", "=", rec.id)]).mapped("pnl_amount")
            )

    def get_excluded_symbol_list(self):
        self.ensure_one()
        return [x.strip().upper() for x in (self.excluded_symbols or "").split(",") if x.strip()]

    def get_altcoin_list(self):
        self.ensure_one()
        return [x.strip().upper() for x in (self.altcoin_symbols or "").split(",") if x.strip()]

    @api.constrains('cooldown_minutes', 'max_daily_loss_percent', 'adx_period', 'atr_period')
    def _check_extra_values(self):
        for rec in self:
            if rec.cooldown_minutes < 0:
                raise ValidationError(_("Cooldown minutes cannot be negative."))
            if rec.max_daily_loss_percent < 0:
                raise ValidationError(_("Max daily loss percent cannot be negative."))
            if rec.adx_period <= 1:
                raise ValidationError(_("ADX period must be greater than 1."))
            if rec.atr_period <= 1:
                raise ValidationError(_("ATR period must be greater than 1."))

    def action_start(self):
        for rec in self:
            rec.state = 'running'
            if not rec.available_capital:
                rec.available_capital = rec.paper_capital

    def action_stop(self):
        self.write({'state': 'stopped'})