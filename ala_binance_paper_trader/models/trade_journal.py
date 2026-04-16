from odoo import api, fields, models


class AlaBinanceTradeJournal(models.Model):
    _name = "ala.binance.trade.journal"
    _description = "Binance Paper Trade Journal"
    _order = "trade_date desc, id desc"

    trade_id = fields.Many2one("ala.binance.paper.trade", required=True, ondelete="cascade", index=True)
    config_id = fields.Many2one("ala.binance.strategy.config", required=True, index=True)
    symbol = fields.Char(required=True, index=True)
    side = fields.Selection([("long", "Long"), ("short", "Short")], required=True)

    trade_date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    entry_time = fields.Datetime()
    exit_time = fields.Datetime()

    entry_price = fields.Float()
    exit_price = fields.Float()
    quantity = fields.Float()
    notional = fields.Float()

    pnl_amount = fields.Float()
    pnl_percent = fields.Float()
    close_reason = fields.Char()

    btc_timeframe = fields.Char()
    alt_timeframe = fields.Char()

    @api.model
    def create_from_trade(self, trade):
        existing = self.search([("trade_id", "=", trade.id)], limit=1)
        vals = {
            "trade_id": trade.id,
            "config_id": trade.config_id.id,
            "symbol": trade.symbol,
            "side": trade.side,
            "trade_date": fields.Date.to_date(trade.exit_time or trade.entry_time or fields.Date.today()),
            "entry_time": trade.entry_time,
            "exit_time": trade.exit_time,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "quantity": trade.quantity,
            "notional": trade.notional,
            "pnl_amount": trade.pnl_amount,
            "pnl_percent": trade.pnl_percent,
            "close_reason": trade.close_reason,
            "btc_timeframe": getattr(trade.config_id, "btc_timeframe", False),
            "alt_timeframe": getattr(trade.config_id, "alt_timeframe", False),
        }
        if existing:
            existing.write(vals)
            return existing
        return self.create(vals)