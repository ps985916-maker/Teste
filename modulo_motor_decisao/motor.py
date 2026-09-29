"""Regras explícitas; AGUARDAR é o fallback seguro."""

from dataclasses import dataclass, field


@dataclass
class Sinal:
    symbol: str
    action: str
    confidence: float
    rationale: list[str] = field(default_factory=list)
    stop_loss_pct: float = 0.03
    database_id: int | None = None


class MotorDecisao:
    def __init__(self, config):
        self.config = config

    def gerar_sinal(self, symbol, analise):
        if not analise.data_sufficient or analise.confidence < self.config.min_confidence or analise.volatility > self.config.max_volatility_pct:
            return Sinal(symbol, "AGUARDAR", analise.confidence, ["dados insuficientes ou incerteza alta"], self.config.max_stop_loss_pct)
        action = "COMPRAR" if analise.technical_score >= 0.45 else "VENDER" if analise.technical_score <= -0.45 else "MANTER"
        return Sinal(symbol, action, analise.confidence, analise.positive_factors + analise.negative_factors, self.config.max_stop_loss_pct)
