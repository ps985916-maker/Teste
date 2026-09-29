"""Gestor de risco com validação obrigatória antes de qualquer operação."""

from dataclasses import dataclass, field


@dataclass
class AprovacaoRisco:
    aprovado: bool
    motivos: list[str] = field(default_factory=list)
    capital_permitido: float = 0.0


class GestorRisco:
    def __init__(self, config, banco):
        self.config = config
        self.banco = banco
        self.daily_loss = 0.0
        self.weekly_loss = 0.0
        self.halted = False

    def validar(self, sinal, mercado: dict, saldo: float) -> AprovacaoRisco:
        motivos = []

        if self.halted:
            motivos.append("operações interrompidas por limite de perda")

        if sinal.action in {"AGUARDAR", "MANTER"}:
            motivos.append("sinal não operável")

        if sinal.action not in {"COMPRAR", "VENDER"}:
            motivos.append("ação inválida")

        if sinal.stop_loss_pct <= 0 or sinal.stop_loss_pct > self.config.max_stop_loss_pct:
            motivos.append("stop-loss fora do limite aceitável")

        if self.daily_loss >= self.config.max_daily_loss:
            self.halted = True
            motivos.append("limite diário de perda excedido")

        if self.weekly_loss >= self.config.max_weekly_loss:
            self.halted = True
            motivos.append("limite semanal de perda excedido")

        if mercado.get("ticker", {}).get("last") is None:
            motivos.append("preço de mercado indisponível")

        if mercado.get("candles") is None or len(mercado.get("candles", [])) < 20:
            motivos.append("quantidade insuficiente de candles")

        volatility = mercado.get("volatility", 0.0)
        if volatility and volatility > self.config.max_volatility_pct:
            motivos.append("volatilidade extrema detectada")

        capital_permitido = float(saldo) * self.config.max_capital_per_trade
        if capital_permitido <= 0:
            motivos.append("capital permitido inválido")

        aprovado = not motivos
        return AprovacaoRisco(aprovado=aprovado, motivos=motivos, capital_permitido=capital_permitido)

    def registrar_perda(self, valor_percentual: float):
        """Atualiza os limites diários/semanais de perda e ativa stop automático."""
        self.daily_loss += max(0.0, valor_percentual)
        self.weekly_loss += max(0.0, valor_percentual)
        if self.daily_loss >= self.config.max_daily_loss or self.weekly_loss >= self.config.max_weekly_loss:
            self.halted = True
