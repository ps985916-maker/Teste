"""Guardião obrigatório de risco; nenhuma ordem deve contorná-lo."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AprovacaoRisco:
    aprovado: bool
    motivos: list[str] = field(default_factory=list)
    capital_permitido: float = 0.0


class GestorRisco:
    def __init__(self, config, banco):
        self.config, self.banco = config, banco
        self.daily_loss, self.weekly_loss = 0.0, 0.0
        self.halted = False

    def validar(self, sinal, mercado, saldo):
        motivos = []
        if self.halted:
            motivos.append("operações interrompidas por limite de perda")
        if sinal.action not in {"COMPRAR", "VENDER"}:
            motivos.append("sinal não operável")
        if sinal.stop_loss_pct <= 0 or sinal.stop_loss_pct > self.config.max_stop_loss_pct:
            motivos.append("stop-loss inválido")
        if self.daily_loss >= self.config.max_daily_loss:
            self.halted = True
            motivos.append("limite diário excedido")
        if self.weekly_loss >= self.config.max_weekly_loss:
            motivos.append("limite semanal excedido")
        ticker = mercado.get("ticker", {})
        capital = float(saldo) * self.config.max_capital_per_trade
        return AprovacaoRisco(not motivos, motivos, capital)
