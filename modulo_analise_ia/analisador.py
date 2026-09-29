"""Analisador técnico e de sentimento com suporte a LLM opcional."""

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import requests


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
    market_regime: str = "NEUTRO"


class AnalisadorIA:
    def __init__(self, config, banco):
        self.config = config
        self.banco = banco

    def analisar(self, symbol: str, mercado: dict) -> Analise:
        candles = mercado.get("candles", [])
        if len(candles) < 50:
            return Analise(
                symbol=symbol,
                sentiment=0.0,
                confidence=0.0,
                technical_score=0.0,
                positive_factors=[],
                negative_factors=["dados insuficientes"],
                volatility=0.0,
                data_sufficient=False,
                market_regime="NEUTRO",
            )

        df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close", "volume"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"]).copy()
        if df.empty:
            return Analise(symbol=symbol, sentiment=0.0, confidence=0.0, technical_score=0.0, negative_factors=["sem dados válidos"], data_sufficient=False)

        close = df["close"]
        returns = close.pct_change().fillna(0)
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi_val = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - macd_signal
        macd_val = float(macd_hist.iloc[-1])

        rolling_mean = close.rolling(20).mean()
        rolling_std = close.rolling(20).std()
        upper_bb = rolling_mean + 2 * rolling_std
        lower_bb = rolling_mean - 2 * rolling_std
        bb_pct = (close.iloc[-1] - lower_bb.iloc[-1]) / (upper_bb.iloc[-1] - lower_bb.iloc[-1]) if (upper_bb.iloc[-1] - lower_bb.iloc[-1]) else 0.5

        high_low = df["high"] - df["low"]
        atr = high_low.rolling(14).mean().iloc[-1] if len(high_low) > 0 else 0.0
        support = float(df["low"].rolling(20).min().iloc[-1])
        resistance = float(df["high"].rolling(20).max().iloc[-1])
        volatility = float(returns.rolling(20).std().iloc[-1] * np.sqrt(24)) if len(returns) > 0 else 0.0

        # Escala a pontuação tecnica em [-1, 1]
        technical_score = 0.0
        if rsi_val > 70:
            technical_score -= 0.35
        elif rsi_val < 30:
            technical_score += 0.35
        technical_score += 0.35 if macd_val > 0 else -0.35
        technical_score += 0.20 if bb_pct > 0.6 else -0.20
        technical_score += 0.15 if close.iloc[-1] > support else -0.10
        technical_score += 0.10 if close.iloc[-1] < resistance else -0.10
        technical_score = max(-1.0, min(1.0, technical_score))

        # Fatores qualitativos
        positive = []
        negative = []
        if macd_val > 0:
            positive.append("MACD positivo")
        else:
            negative.append("MACD negativo")
        if rsi_val > 70:
            negative.append("RSI sobrecomprado")
        elif rsi_val < 30:
            positive.append("RSI em sobrevenda")
        if bb_pct > 0.8:
            negative.append("preço próximo ao topo da banda")
        elif bb_pct < 0.2:
            positive.append("preço próximo ao fundo da banda")
        if atr <= 0:
            negative.append("ATR zero ou ausente")

        # Sentimento de notícias (somente insumo; não decide ordens)
        news = mercado.get("news", [])
        sentiment = 0.0
        for article in news[:10]:
            title = str(article.get("title", "")).lower()
            description = str(article.get("description", "")).lower()
            text = f"{title} {description}"
            if any(word in text for word in ["surge", "bullish", "gain", "positive", "rally"]):
                sentiment += 0.08
            if any(word in text for word in ["crash", "selloff", "decline", "risk", "drop", "recession"]):
                sentiment -= 0.08

        sentiment = max(-1.0, min(1.0, sentiment + technical_score * 0.2))
        confidence = 0.55 + min(0.3, abs(technical_score) * 0.35) + min(0.15, abs(sentiment) * 0.15)
        confidence = max(0.0, min(1.0, confidence))

        market_regime = "TENDENCIA_ALTA" if technical_score > 0.35 else "TENDENCIA_BAIXA" if technical_score < -0.35 else "NEUTRO"

        llm_info = self._consultar_llm(symbol, mercado, sentiment, technical_score)
        if llm_info:
            positive.extend(llm_info.get("positive_factors", []))
            negative.extend(llm_info.get("negative_factors", []))
            sentiment = float(np.clip(llm_info.get("sentiment", sentiment), -1.0, 1.0))
            confidence = float(np.clip(llm_info.get("confidence", confidence), 0.0, 1.0))

        return Analise(
            symbol=symbol,
            sentiment=sentiment,
            confidence=confidence,
            technical_score=technical_score,
            positive_factors=positive,
            negative_factors=negative,
            volatility=volatility,
            data_sufficient=True,
            market_regime=market_regime,
        )

    def _consultar_llm(self, symbol: str, mercado: dict, sentiment: float, technical_score: float):
        """Consulta LLM apenas para enriquecer insumo e não para autorizar operações."""
        if not self.config.llm_api_key:
            return None
        try:
            payload = {
                "model": self.config.llm_model,
                "messages": [{
                    "role": "system",
                    "content": "Você é um analista financeiro. Dê resposta em JSON com: sentiment, confidence, positive_factors, negative_factors. Use o contexto de mercado sem autorizar ordens.",
                }, {
                    "role": "user",
                    "content": f"Ativo: {symbol}. Sentimento técnico: {sentiment:.2f}. Score técnico: {technical_score:.2f}. Notícias: {len(mercado.get('news', []))} artigos. Resuma os principais riscos e oportunidades em JSON.",
                }],
                "temperature": 0.2,
            }
            headers = {"Authorization": f"Bearer {self.config.llm_api_key}", "Content-Type": "application/json"}
            resp = requests.post(f"{self.config.llm_base_url}/chat/completions", json=payload, headers=headers, timeout=25)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            # Melhor esforço para extrair JSON do conteúdo retornado pelo LLM.
            import json as json_module
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                return json_module.loads(content[start:end + 1])
        except Exception as exc:
            logging.warning("LLM indisponível para %s: %s", symbol, exc)
        return None
