"""Componente de coleta de mercado com fallback resiliente."""

import logging
from datetime import datetime, timezone

import ccxt
import requests
import yfinance as yf


class ColetorDados:
    def __init__(self, config, banco):
        self.config = config
        self.banco = banco
        try:
            self.exchange = getattr(ccxt, config.exchange_id)({"enableRateLimit": True})
        except Exception:
            self.exchange = None
            logging.warning("Exchange %s indisponível; usaremos fallback do Yahoo Finance para coleta básica.", config.exchange_id)

    def coletar_mercado(self, symbol: str):
        """Busca candles, ticker e notícias, sempre com fallback seguro."""
        try:
            candles = self._coletar_candles(symbol)
            ticker = self._coletar_ticker(symbol)
            noticias = self._coletar_noticias(symbol)
            payload = {
                "symbol": symbol,
                "candles": candles,
                "ticker": ticker,
                "news": noticias,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            self.banco.registrar_mercado(symbol, payload, source="collector")
            return payload
        except Exception as exc:
            logging.exception("Falha ao coletar dados do ativo %s", symbol)
            raise RuntimeError(f"Dados indisponíveis para {symbol}: {exc}") from exc

    def _coletar_candles(self, symbol):
        if self.exchange is not None:
            try:
                return self.exchange.fetch_ohlcv(symbol, self.config.timeframe, limit=200)
            except (ccxt.BaseError, requests.RequestException) as exc:
                logging.warning("CCXT falhou para %s: %s", symbol, exc)

        data = yf.download(symbol.replace("/USDT", "-USD"), period="7d", interval="1h", progress=False, auto_adjust=False)
        if data.empty:
            raise RuntimeError("Nenhum candle recuperado")
        candles = []
        for ts, row in data.iterrows():
            candles.append([
                int(ts.timestamp()),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                float(row["Volume"]),
            ])
        return candles

    def _coletar_ticker(self, symbol):
        if self.exchange is not None:
            try:
                return self.exchange.fetch_ticker(symbol)
            except (ccxt.BaseError, requests.RequestException):
                logging.warning("Ticker do CCXT indisponível para %s", symbol)

        ticker = yf.Ticker(symbol.replace("/USDT", "-USD")).fast_info
        if ticker is None:
            return {"symbol": symbol, "last": None}
        return {"symbol": symbol, "last": getattr(ticker, "last_price", None)}

    def _coletar_noticias(self, symbol: str):
        if not self.config.news_api_key:
            return []
        try:
            resp = requests.get(
                self.config.news_base_url,
                params={"q": symbol, "apiKey": self.config.news_api_key, "language": "en"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("articles", [])[:20]
        except requests.RequestException as exc:
            logging.warning("Falha ao buscar notícias para %s: %s", symbol, exc)
            return []
