"""Execução somente em paper trading; REAL permanece bloqueado deliberadamente."""

from dataclasses import dataclass
import logging


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
        self.config, self.banco = config, banco
        if config.trading_mode == "REAL":
            raise RuntimeError("Modo REAL está bloqueado neste esqueleto; implemente revisão/aprovação explícita antes de habilitar.")

    def saldo_disponivel(self):
        return 10_000.0

    def executar(self, sinal, aprovacao):
        if not aprovacao.aprovado:
            raise PermissionError("Ordem sem aprovação do módulo de risco")
        # Simulação não envia rede nem ordem à corretora; preço é preenchido pelo adaptador real futuramente.
        logging.info("PAPER ORDER %s %s capital=%s", sinal.action, sinal.symbol, aprovacao.capital_permitido)
        return ResultadoOrdem(sinal.symbol, "SIMULADO", sinal.action, aprovacao.capital_permitido, None, sinal.stop_loss_pct)
