from datetime import datetime, time
from odoo import api, fields, models


class AlaBinancePaperTrade(models.Model):
    _name = "ala.binance.paper.trade"
    _description = "Binance Paper Trade"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "entry_time desc"

    name = fields.Char(default="New", readonly=True, copy=False)
    config_id = fields.Many2one("ala.binance.strategy.config", required=True, ondelete="cascade")
    symbol = fields.Char(required=True, index=True)
    side = fields.Selection([("long", "Long"), ("short", "Short")], required=True)

    entry_price = fields.Float(required=True)
    current_price = fields.Float()
    exit_price = fields.Float()

    quantity = fields.Float(required=True)
    notional = fields.Float(required=True)

    tp_price = fields.Float(required=True)
    sl_price = fields.Float(required=True)
    atr_value = fields.Float()

    entry_time = fields.Datetime(default=fields.Datetime.now, required=True)
    exit_time = fields.Datetime()

    state = fields.Selection([
        ("open", "Open"),
        ("tp_hit", "TP Hit"),
        ("sl_hit", "SL Hit"),
        ("closed", "Closed"),
    ], default="open")

    pnl_amount = fields.Float()
    pnl_percent = fields.Float()
    close_reason = fields.Char()

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("ala.binance.paper.trade") or "New"
        return super().create(vals)

    @api.model
    def _is_symbol_in_cooldown(self, config, symbol):
        last_trade = self.search([
            ("config_id", "=", config.id),
            ("symbol", "=", symbol),
            ("state", "!=", "open"),
        ], order="exit_time desc, entry_time desc", limit=1)

        if not last_trade or not last_trade.exit_time:
            return False

        delta = fields.Datetime.now() - last_trade.exit_time
        minutes = delta.total_seconds() / 60.0
        return minutes < config.cooldown_minutes

    @api.model
    def _get_today_loss_amount(self, config):
        now = fields.Datetime.now()
        day_start = datetime.combine(now.date(), time.min)
        day_start = fields.Datetime.to_string(day_start)

        trades = self.search([
            ("config_id", "=", config.id),
            ("state", "in", ["sl_hit", "closed"]),
            ("exit_time", ">=", day_start),
        ])

        total_loss = 0.0
        for trade in trades:
            if trade.pnl_amount < 0:
                total_loss += abs(trade.pnl_amount)
        return total_loss

    @api.model
    def _daily_loss_limit_hit(self, config):
        base = config.paper_capital or 0.0
        if base <= 0:
            return False
        today_loss = self._get_today_loss_amount(config)
        limit_amount = base * (config.max_daily_loss_percent / 100.0)
        return today_loss >= limit_amount

    def _compute_pnl(self):
        for rec in self:
            if not rec.current_price:
                continue
            if rec.side == "long":
                pnl = (rec.current_price - rec.entry_price) * rec.quantity
            else:
                pnl = (rec.entry_price - rec.current_price) * rec.quantity
            rec.pnl_amount = pnl
            rec.pnl_percent = (pnl / rec.notional) * 100 if rec.notional else 0.0

    def _close_trade(self, state, price, reason=None):
        journal_model = self.env["ala.binance.trade.journal"]
        for rec in self:
            rec.current_price = price
            rec.exit_price = price
            rec.exit_time = fields.Datetime.now()
            rec.state = state
            rec.close_reason = reason or state
            rec._compute_pnl()
            journal_model.create_from_trade(rec)

    @api.model
    def _open_trade(self, config, symbol, side, entry_price, atr_value=None):
        qty = config.trade_size_usdt / entry_price

        if config.use_atr_sl and atr_value:
            if side == "long":
                sl_price = entry_price - (atr_value * config.atr_sl_multiplier)
            else:
                sl_price = entry_price + (atr_value * config.atr_sl_multiplier)
        else:
            if side == "long":
                sl_price = entry_price * (1 - (config.sl_percent / 100.0))
            else:
                sl_price = entry_price * (1 + (config.sl_percent / 100.0))

        if side == "long":
            tp_price = entry_price * (1 + (config.tp_percent / 100.0))
        else:
            tp_price = entry_price * (1 - (config.tp_percent / 100.0))

        return self.create({
            "config_id": config.id,
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "current_price": entry_price,
            "quantity": qty,
            "notional": config.trade_size_usdt,
            "tp_price": tp_price,
            "sl_price": sl_price,
            "atr_value": atr_value or 0.0,
        })

    @api.model
    def cron_scan_and_open_trades(self):
        snapshot_model = self.env["ala.binance.market.snapshot"]
        configs = self.env["ala.binance.strategy.config"].search([
            ("state", "=", "running"),
            ("active", "=", True),
        ])

        for config in configs:
            if self._daily_loss_limit_hit(config):
                continue

            open_count = self.search_count([
                ("config_id", "=", config.id),
                ("state", "=", "open"),
            ])
            if open_count >= config.max_open_trades:
                continue

            btc_long_ok, btc_long_data = snapshot_model._bullish_ok(
                config.btc_symbol, config.btc_timeframe, config
            )
            btc_short_ok, btc_short_data = snapshot_model._bearish_ok(
                config.btc_symbol, config.btc_timeframe, config
            )

            symbols_to_scan = []
            if config.validate_symbols_on_scan:
                symbols_to_scan = snapshot_model._get_top_altcoins_by_volume(config)
            else:
                symbols_to_scan = config.get_altcoin_list()

            for symbol in symbols_to_scan:
                if self._is_symbol_in_cooldown(config, symbol):
                    continue

                existing = self.search([
                    ("config_id", "=", config.id),
                    ("symbol", "=", symbol),
                    ("state", "=", "open"),
                ], limit=1)
                if existing:
                    continue

                long_ok, long_data = snapshot_model._bullish_ok(
                    symbol, config.alt_timeframe, config
                )
                short_ok, short_data = snapshot_model._bearish_ok(
                    symbol, config.alt_timeframe, config
                )

                price = long_data.get("last_close") or short_data.get("last_close")
                if not price:
                    continue

                if btc_long_ok and long_ok:
                    self._open_trade(
                        config=config,
                        symbol=symbol,
                        side="long",
                        entry_price=price,
                        atr_value=long_data.get("atr"),
                    )
                    break

                if config.use_short and btc_short_ok and short_ok:
                    self._open_trade(
                        config=config,
                        symbol=symbol,
                        side="short",
                        entry_price=price,
                        atr_value=short_data.get("atr"),
                    )
                    break

    @api.model
    def cron_manage_open_trades(self):
        snapshot_model = self.env["ala.binance.market.snapshot"]
        trades = self.search([("state", "=", "open")])

        for trade in trades:
            try:
                price = snapshot_model._get_futures_ticker_price(trade.symbol)
            except Exception:
                continue

            trade.current_price = price
            trade._compute_pnl()

            if trade.side == "long":
                if price >= trade.tp_price:
                    trade._close_trade("tp_hit", price, reason="Take Profit Hit")
                elif price <= trade.sl_price:
                    trade._close_trade("sl_hit", price, reason="Stop Loss Hit")
            else:
                if price <= trade.tp_price:
                    trade._close_trade("tp_hit", price, reason="Take Profit Hit")
                elif price >= trade.sl_price:
                    trade._close_trade("sl_hit", price, reason="Stop Loss Hit")