"""Coleta resiliente de candles via CCXT e notícias via API opcional."""

import logging
from datetime import datetime, timezone

import ccxt
import requests


class ColetorDados:
    def __init__(self, config, banco):
        self.config, self.banco = config, banco
        self.exchange = getattr(ccxt, config.exchange_id)({"enableRateLimit": True})

    def coletar_mercado(self, symbol):
        """Retorna candles, ticker e indicadores básicos; falha de API vira erro auditável."""
        try:
            candles = self.exchange.fetch_ohlcv(symbol, self.config.timeframe, limit=200)
            ticker = self.exchange.fetch_ticker(symbol)
            noticias = self._coletar_noticias(symbol)
            payload = {"symbol": symbol, "candles": candles, "ticker": ticker, "news": noticias, "collected_at": datetime.now(timezone.utc).isoformat()}
            self.banco.registrar_mercado(symbol, payload)
            return payload
        except (ccxt.BaseError, requests.RequestException) as exc:
            logging.exception("Falha ao coletar %s", symbol)
            raise RuntimeError(f"Dados indisponíveis para {symbol}") from exc

    def _coletar_noticias(self, symbol):
        if not self.config.news_api_key:
            return []
        response = requests.get(self.config.news_base_url, params={"q": symbol, "apiKey": self.config.news_api_key, "language": "en"}, timeout=15)
        response.raise_for_status()
        return response.json().get("articles", [])[:20]
