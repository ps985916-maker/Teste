"""Execução de ordens em simulação com controle de posição usando preço de mercado."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ResultadoOrdem:
    symbol: str
    status: str
    action: str
    amount: float
    price: float | None
    stop_loss_pct: float
    pnl: float = 0.0
    entry_price: float | None = None
    exit_price: float | None = None
    error: str | None = None
    timestamp: str | None = None


class ExecutorOrdens:
    """Mantém portfólio simulado e registra todas as ordens para auditoria."""

    def __init__(self, config, banco):
        self.config = config
        self.banco = banco
        self._simulated_cash = 10_000.0
        self.positions = {}
        self.trade_history = []
        if config.trading_mode == "REAL":
            raise RuntimeError("Modo REAL bloqueado por segurança. Ative somente após validação e aprovação formal do trader.")

    def saldo_disponivel(self) -> float:
        return self._simulated_cash

    def executar(self, sinal, aprovacao, market_price: float | None = None) -> ResultadoOrdem:
        if not aprovacao.aprovado:
            raise PermissionError("Ordem bloqueada: não passou validação do módulo de risco")
        if market_price is None or market_price <= 0:
            raise ValueError("Preço de mercado obrigatório para execução em simulação")

        trade_value = self._simulated_cash * aprovacao.capital_permitido
        quantity = trade_value / market_price
        self._simulated_cash = max(0.0, self._simulated_cash - trade_value)

        position = {
            "symbol": sinal.symbol,
            "action": sinal.action,
            "quantity": quantity,
            "entry_price": market_price,
            "stop_loss_pct": sinal.stop_loss_pct,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.positions[sinal.symbol] = position

        order = ResultadoOrdem(
            symbol=sinal.symbol,
            status="SIMULADO",
            action=sinal.action,
            amount=trade_value,
            price=market_price,
            stop_loss_pct=sinal.stop_loss_pct,
            entry_price=market_price,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self.banco.registrar_ordem(order)
        self.trade_history.append(order.__dict__)
        logging.info("Ordem simulada: %s %s | valor=%s | preço=%s", sinal.action, sinal.symbol, trade_value, market_price)
        return order
