import requests
from odoo import api, fields, models


class AlaBinanceMarketSnapshot(models.Model):
    _name = "ala.binance.market.snapshot"
    _description = "Binance Market Snapshot"
    _order = "snapshot_time desc"

    symbol = fields.Char(required=True, index=True)
    price = fields.Float(required=True)
    mark_price = fields.Float()
    snapshot_time = fields.Datetime(default=fields.Datetime.now, required=True)

    @api.model
    def _get_exchange_info(self):
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()

    @api.model
    def _get_valid_futures_symbols(self):
        info = self._get_exchange_info()
        valid = {}
        for sym in info.get("symbols", []):
            if sym.get("status") != "TRADING":
                continue
            valid[sym["symbol"]] = {
                "baseAsset": sym.get("baseAsset"),
                "quoteAsset": sym.get("quoteAsset"),
                "pair": sym.get("pair"),
                "contractType": sym.get("contractType"),
            }
        return valid

    @api.model
    def _is_valid_futures_symbol(self, symbol, quote_asset="USDT"):
        valid = self._get_valid_futures_symbols()
        meta = valid.get(symbol.upper())
        if not meta:
            return False
        if quote_asset and meta.get("quoteAsset") != quote_asset:
            return False
        return True

    @api.model
    def _get_24h_tickers(self):
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()

    @api.model
    def cron_collect_market_data(self):
        configs = self.env["ala.binance.strategy.config"].search([
            ("state", "=", "running"),
            ("active", "=", True),
        ])

        symbols = set()
        for config in configs:
            if config.btc_symbol:
                symbols.add(config.btc_symbol.upper())
            for sym in config.get_altcoin_list():
                symbols.add(sym.upper())

        for symbol in symbols:
            try:
                self._record_snapshot(symbol)
            except Exception:
                continue

    @api.model
    def _get_top_altcoins_by_volume(self, config):
        valid_map = self._get_valid_futures_symbols()
        excluded = set(config.get_excluded_symbol_list())
        quote_asset = (config.allowed_quote_asset or "USDT").upper()
        min_quote_volume = config.min_quote_volume or 0.0
        limit = config.top_coin_limit or 10

        rows = []
        for row in self._get_24h_tickers():
            symbol = row.get("symbol", "").upper()
            if symbol in excluded:
                continue
            meta = valid_map.get(symbol)
            if not meta:
                continue
            if meta.get("quoteAsset") != quote_asset:
                continue
            if symbol == config.btc_symbol:
                continue

            try:
                quote_volume = float(row.get("quoteVolume", 0.0))
                last_price = float(row.get("lastPrice", 0.0))
                price_change_percent = float(row.get("priceChangePercent", 0.0))
            except Exception:
                continue

            if quote_volume < min_quote_volume:
                continue
            if last_price <= 0:
                continue

            rows.append({
                "symbol": symbol,
                "quote_volume": quote_volume,
                "price_change_percent": price_change_percent,
            })

        rows.sort(key=lambda x: x["quote_volume"], reverse=True)
        return [x["symbol"] for x in rows[:limit]]

    @api.model
    def _get_futures_ticker_price(self, symbol):
        url = "https://fapi.binance.com/fapi/v1/ticker/price"
        resp = requests.get(url, params={"symbol": symbol}, timeout=10)
        resp.raise_for_status()
        return float(resp.json()["price"])

    @api.model
    def _get_futures_klines(self, symbol, interval="5m", limit=200):
        url = "https://fapi.binance.com/fapi/v1/klines"
        resp = requests.get(url, params={
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }, timeout=15)
        resp.raise_for_status()
        rows = resp.json()
        return [{
            "open": float(r[1]),
            "high": float(r[2]),
            "low": float(r[3]),
            "close": float(r[4]),
            "volume": float(r[5]),
        } for r in rows]

    @api.model
    def _ema_series(self, values, period):
        if len(values) < period:
            return []
        multiplier = 2 / (period + 1)
        sma = sum(values[:period]) / period
        out = [sma]
        for val in values[period:]:
            out.append(((val - out[-1]) * multiplier) + out[-1])
        return out

    @api.model
    def _rsi(self, closes, period=14):
        if len(closes) < period + 1:
            return None
        gains, losses = [], []
        for i in range(1, period + 1):
            diff = closes[i] - closes[i - 1]
            gains.append(max(diff, 0.0))
            losses.append(abs(min(diff, 0.0)))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        for i in range(period + 1, len(closes)):
            diff = closes[i] - closes[i - 1]
            gain = max(diff, 0.0)
            loss = abs(min(diff, 0.0))
            avg_gain = ((avg_gain * (period - 1)) + gain) / period
            avg_loss = ((avg_loss * (period - 1)) + loss) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @api.model
    def _macd(self, closes, fast=12, slow=26, signal=9):
        if len(closes) < slow + signal:
            return None
        ema_fast = self._ema_series(closes, fast)
        ema_slow = self._ema_series(closes, slow)
        if not ema_fast or not ema_slow:
            return None

        offset = slow - fast
        fast_aligned = ema_fast[offset:]
        min_len = min(len(fast_aligned), len(ema_slow))
        fast_aligned = fast_aligned[-min_len:]
        slow_aligned = ema_slow[-min_len:]

        macd_line = [f - s for f, s in zip(fast_aligned, slow_aligned)]
        signal_line = self._ema_series(macd_line, signal)
        if not signal_line:
            return None

        signal_tail = signal_line[-1]
        macd_tail = macd_line[-1]
        return {
            "macd": macd_tail,
            "signal": signal_tail,
            "histogram": macd_tail - signal_tail,
        }

    @api.model
    def _true_ranges(self, candles):
        trs = []
        for i, candle in enumerate(candles):
            high = candle["high"]
            low = candle["low"]
            if i == 0:
                trs.append(high - low)
                continue
            prev_close = candles[i - 1]["close"]
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
            trs.append(tr)
        return trs

    @api.model
    def _atr(self, candles, period=14):
        if len(candles) < period + 1:
            return None
        trs = self._true_ranges(candles)
        atr = sum(trs[:period]) / period
        for tr in trs[period:]:
            atr = ((atr * (period - 1)) + tr) / period
        return atr

    @api.model
    def _adx(self, candles, period=14):
        if len(candles) < period * 2:
            return None

        plus_dm = []
        minus_dm = []
        tr_list = []

        for i in range(1, len(candles)):
            curr = candles[i]
            prev = candles[i - 1]

            up_move = curr["high"] - prev["high"]
            down_move = prev["low"] - curr["low"]

            plus = up_move if up_move > down_move and up_move > 0 else 0.0
            minus = down_move if down_move > up_move and down_move > 0 else 0.0
            plus_dm.append(plus)
            minus_dm.append(minus)

            tr = max(
                curr["high"] - curr["low"],
                abs(curr["high"] - prev["close"]),
                abs(curr["low"] - prev["close"]),
            )
            tr_list.append(tr)

        tr14 = sum(tr_list[:period])
        plus14 = sum(plus_dm[:period])
        minus14 = sum(minus_dm[:period])

        dxs = []
        for i in range(period, len(tr_list)):
            if i > period:
                tr14 = tr14 - (tr14 / period) + tr_list[i]
                plus14 = plus14 - (plus14 / period) + plus_dm[i]
                minus14 = minus14 - (minus14 / period) + minus_dm[i]

            if tr14 == 0:
                continue

            plus_di = 100 * (plus14 / tr14)
            minus_di = 100 * (minus14 / tr14)
            di_sum = plus_di + minus_di
            dx = 0.0 if di_sum == 0 else 100 * abs(plus_di - minus_di) / di_sum
            dxs.append(dx)

        if len(dxs) < period:
            return None

        adx = sum(dxs[:period]) / period
        for dx in dxs[period:]:
            adx = ((adx * (period - 1)) + dx) / period
        return adx

    @api.model
    def _volume_spike_ok(self, candles, ma_period=20, multiplier=1.5):
        if len(candles) < ma_period + 1:
            return False
        volumes = [c["volume"] for c in candles]
        avg_vol = sum(volumes[-(ma_period + 1):-1]) / ma_period
        current_vol = volumes[-1]
        return current_vol >= (avg_vol * multiplier)

    @api.model
    def _sr_levels(self, candles, lookback=20):
        if len(candles) < lookback:
            return None
        recent = candles[-lookback:]
        resistance = max(c["high"] for c in recent)
        support = min(c["low"] for c in recent)
        return {"support": support, "resistance": resistance}

    @api.model
    def _near_resistance(self, price, resistance, buffer_percent):
        if not resistance:
            return False
        return price >= resistance * (1 - buffer_percent / 100.0)

    @api.model
    def _near_support(self, price, support, buffer_percent):
        if not support:
            return False
        return price <= support * (1 + buffer_percent / 100.0)

    @api.model
    def _indicator_bundle(self, symbol, interval, config):
        candles = self._get_futures_klines(symbol, interval=interval, limit=220)
        closes = [c["close"] for c in candles]
        last_close = closes[-1] if closes else None
        ema = self._ema_series(closes, config.ema_period)
        macd = self._macd(closes, config.macd_fast, config.macd_slow, config.macd_signal)
        sr = self._sr_levels(candles, config.sr_lookback)

        return {
            "candles": candles,
            "last_close": last_close,
            "rsi": self._rsi(closes, config.rsi_period) if config.use_rsi else None,
            "ema": ema[-1] if ema else None,
            "macd": macd,
            "adx": self._adx(candles, config.adx_period) if config.use_adx else None,
            "atr": self._atr(candles, config.atr_period) if config.use_atr_sl else None,
            "volume_spike_ok": self._volume_spike_ok(
                candles, config.volume_ma_period, config.volume_spike_multiplier
            ) if config.use_volume_spike else True,
            "sr": sr,
        }

    @api.model
    def _bullish_ok(self, symbol, timeframe, config):
        data = self._indicator_bundle(symbol, timeframe, config)
        if not data.get("last_close"):
            return False, data

        if config.use_rsi and (data["rsi"] is None or data["rsi"] < config.rsi_long_min):
            return False, data

        if config.use_macd:
            m = data["macd"]
            if not m or m["macd"] <= m["signal"]:
                return False, data

        if config.use_ema_filter and (data["ema"] is None or data["last_close"] <= data["ema"]):
            return False, data

        if config.use_adx and (data["adx"] is None or data["adx"] < config.adx_min):
            return False, data

        if config.use_volume_spike and not data["volume_spike_ok"]:
            return False, data

        if config.use_sr_filter and data["sr"]:
            if self._near_resistance(data["last_close"], data["sr"]["resistance"], config.sr_buffer_percent):
                return False, data

        return True, data

    @api.model
    def _bearish_ok(self, symbol, timeframe, config):
        data = self._indicator_bundle(symbol, timeframe, config)
        if not data.get("last_close"):
            return False, data

        if config.use_rsi and (data["rsi"] is None or data["rsi"] > config.rsi_short_max):
            return False, data

        if config.use_macd:
            m = data["macd"]
            if not m or m["macd"] >= m["signal"]:
                return False, data

        if config.use_ema_filter and (data["ema"] is None or data["last_close"] >= data["ema"]):
            return False, data

        if config.use_adx and (data["adx"] is None or data["adx"] < config.adx_min):
            return False, data

        if config.use_volume_spike and not data["volume_spike_ok"]:
            return False, data

        if config.use_sr_filter and data["sr"]:
            if self._near_support(data["last_close"], data["sr"]["support"], config.sr_buffer_percent):
                return False, data

        return True, data