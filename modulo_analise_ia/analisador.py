"""Indicadores técnicos determinísticos e contrato de análise."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Analise:
    symbol: str
    sentiment: float
    confidence: float
    technical_score: float
    positive_factors: list[str] = field(default_factory=list)
    negative_factors: list[str] = field(default_factory=list)
    volatility: float = 0.0
    data_sufficient: bool = False


class AnalisadorIA:
    def __init__(self, config, banco):
        self.config, self.banco = config, banco

    def analisar(self, symbol, mercado):
        candles = mercado.get("candles", [])
        if len(candles) < 50:
            return Analise(symbol, 0.0, 0.0, 0.0, negative_factors=["histórico insuficiente"])
        df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close", "volume"])
        delta = df.close.diff()
        gain, loss = delta.clip(lower=0).rolling(14).mean(), -delta.clip(upper=0).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss.replace(0, 1e-9))).iloc[-1]
        ema12, ema26 = df.close.ewm(span=12).mean(), df.close.ewm(span=26).mean()
        macd = (ema12 - ema26).iloc[-1]
        volatility = float(df.close.pct_change().rolling(20).std().iloc[-1] * 3)
        score = max(-1.0, min(1.0, (50 - rsi) / 50 + (1 if macd > 0 else -1) * 0.2))
        positive = (["MACD positivo"] if macd > 0 else [])
        negative = (["RSI sobrecomprado"] if rsi > 70 else [])
        # O LLM poderia enriquecer fatores aqui; ele nunca decide ou autoriza ordens.
        return Analise(symbol, float(score), 0.70, float(score), positive, negative, volatility, True)
