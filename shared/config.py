"""Configuração central, validando defaults seguros."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    trading_mode: str
    symbols: list[str]
    timeframe: str
    poll_interval_seconds: int
    database_path: str
    log_level: str
    max_capital_per_trade: float
    max_daily_loss: float
    max_weekly_loss: float
    max_stop_loss_pct: float
    max_volatility_pct: float
    min_confidence: float
    exchange_id: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    news_api_key: str
    news_base_url: str

    @classmethod
    def from_env(cls):
        """Lê ambiente sem imprimir segredos; SIMULACAO é o default obrigatório."""
        mode = os.getenv("TRADING_MODE", "SIMULACAO").upper()
        if mode not in {"SIMULACAO", "REAL"}:
            raise ValueError("TRADING_MODE deve ser SIMULACAO ou REAL")
        return cls(
            mode, [x.strip() for x in os.getenv("SYMBOLS", "BTC/USDT").split(",") if x.strip()],
            os.getenv("TIMEFRAME", "1h"), int(os.getenv("POLL_INTERVAL_SECONDS", "300")),
            os.getenv("DATABASE_PATH", "data/trading_agent.sqlite3"), os.getenv("LOG_LEVEL", "INFO"),
            float(os.getenv("MAX_CAPITAL_PER_TRADE", "0.02")), float(os.getenv("MAX_DAILY_LOSS", "0.03")),
            float(os.getenv("MAX_WEEKLY_LOSS", "0.07")), float(os.getenv("MAX_STOP_LOSS_PCT", "0.03")),
            float(os.getenv("MAX_VOLATILITY_PCT", "0.10")), float(os.getenv("MIN_CONFIDENCE", "0.65")),
            os.getenv("EXCHANGE_ID", "binance"), os.getenv("LLM_API_KEY", ""),
            os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"), os.getenv("LLM_MODEL", "gpt-4o-mini"),
            os.getenv("NEWS_API_KEY", ""), os.getenv("NEWS_BASE_URL", "https://newsapi.org/v2/everything"),
        )
