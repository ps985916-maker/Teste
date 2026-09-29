"""Execução em simulação segura. O modo REAL é bloqueado por padrão."""

import logging
from dataclasses import dataclass


@dataclass
class ResultadoOrdem:
    symbol: str
    status: str
    action: str
    amount: float
    price: float | None
    stop_loss_pct: float
    error: str | None = None


class ExecutorOrdens:
    def __init__(self, config, banco):
        self.config = config
        self.banco = banco
        self._simulated_cash = 10_000.0
        if config.trading_mode == "REAL":
            raise RuntimeError("Modo REAL bloqueado neste esqueleto; ative somente após aprovação de segurança e validação completa.")

    def saldo_disponivel(self) -> float:
        return self._simulated_cash

    def executar(self, sinal, aprovacao) -> ResultadoOrdem:
        if not aprovacao.aprovado:
            raise PermissionError("Ordem bloqueada: não passou validação do módulo de risco")

        # Simulação: apenas registra as ordens sem enviar ordens reais à corretora.
        order = ResultadoOrdem(
            symbol=sinal.symbol,
            status="SIMULADO",
            action=sinal.action,
            amount=aprovacao.capital_permitido,
            price=None,
            stop_loss_pct=sinal.stop_loss_pct,
        )
        self.banco.registrar_ordem(order)
        logging.info("Ordem simulada: %s %s valor=%s", sinal.action, sinal.symbol, aprovacao.capital_permitido)
        return order
