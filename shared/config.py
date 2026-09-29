"""Configuração central do agente financeiro."""

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
    exchange_id: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    news_api_key: str
    news_base_url: str
    max_capital_per_trade: float
    max_daily_loss: float
    max_weekly_loss: float
    max_stop_loss_pct: float
    max_volatility_pct: float
    min_confidence: float

    @classmethod
    def from_env(cls):
        """Lê as variáveis de ambiente com defaults seguros para paper trading."""
        mode = os.getenv("TRADING_MODE", "SIMULACAO").upper()
        if mode not in {"SIMULACAO", "REAL"}:
            raise ValueError("TRADING_MODE deve ser SIMULACAO ou REAL")

        symbols = os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT")
        return cls(
            trading_mode=mode,
            symbols=[s.strip() for s in symbols.split(",") if s.strip()],
            timeframe=os.getenv("TIMEFRAME", "1h"),
            poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "300")),
            database_path=os.getenv("DATABASE_PATH", "data/trading_agent.sqlite3"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            exchange_id=os.getenv("EXCHANGE_ID", "binance"),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            news_api_key=os.getenv("NEWS_API_KEY", ""),
            news_base_url=os.getenv("NEWS_BASE_URL", "https://newsapi.org/v2/everything"),
            max_capital_per_trade=float(os.getenv("MAX_CAPITAL_PER_TRADE", "0.02")),
            max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "0.03")),
            max_weekly_loss=float(os.getenv("MAX_WEEKLY_LOSS", "0.07")),
            max_stop_loss_pct=float(os.getenv("MAX_STOP_LOSS_PCT", "0.03")),
            max_volatility_pct=float(os.getenv("MAX_VOLATILITY_PCT", "0.10")),
            min_confidence=float(os.getenv("MIN_CONFIDENCE", "0.65")),
        )
