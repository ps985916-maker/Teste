"""Motor de decisão com regras explícitas e fallback seguro especificado pelo projeto."""

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

    def gerar_sinal(self, symbol: str, analise) -> Sinal:
        if not analise.data_sufficient:
            return Sinal(symbol, "AGUARDAR", 0.0, ["dados insuficientes"], self.config.max_stop_loss_pct)

        if analise.volatility > self.config.max_volatility_pct:
            return Sinal(symbol, "AGUARDAR", analise.confidence, ["volatilidade extrema"], self.config.max_stop_loss_pct)

        if analise.confidence < self.config.min_confidence:
            return Sinal(symbol, "AGUARDAR", analise.confidence, ["confiança insuficiente"], self.config.max_stop_loss_pct)

        if analise.technical_score >= 0.35:
            action = "COMPRAR"
        elif analise.technical_score <= -0.35:
            action = "VENDER"
        else:
            action = "MANTER"

        rationale = analise.positive_factors + analise.negative_factors
        return Sinal(symbol, action, analise.confidence, rationale, self.config.max_stop_loss_pct)
