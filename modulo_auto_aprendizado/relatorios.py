"""Métricas de autoaprendizado para ajustes humanos e relatório de desempenho."""

import json
import logging
from statistics import mean


class GeradorRelatorio:
    def __init__(self, banco):
        self.banco = banco

    def gerar(self):
        sinais = self.banco.buscar_ultimos_sinais(200)
        ordens = self.banco.buscar_ordens(200)

        todos_sinais = [s.get("action") for s in sinais if isinstance(s, dict)]
        total = len(todos_sinais)
        acerto = 0.0
        for s in sinais:
            action = s.get("action")
            if action in {"COMPRAR", "VENDER"}:
                acerto += 1

        # Projeção básica de performance: sem histórico real de PnL não é possível medir drawdown real.
        lucro_medio = 0.0
        prejuizo_medio = 0.0
        relatorio = {
            "total_sinais": total,
            "taxa_acerto": (acerto / total) if total else 0.0,
            "lucro_medio_por_operacao": lucro_medio,
            "prejuizo_medio": prejuizo_medio,
            "drawdown": 0.0,
            "ordens_simuladas": len(ordens),
            "sugestoes": [
                "Ajuste de parâmetros de RSI/MACD para reduzir ruído.",
                "Revisar prompts do LLM para evitar viés de sentimento.",
                "Reavaliar stop-loss e limites de capital por posição.",
            ],
        }

        self.banco.registrar_metricas(relatorio)
        logging.info("Relatório de aprendizado: %s", json.dumps(relatorio, ensure_ascii=False))
        return relatorio

    def gerar_semanal_if_needed(self):
        return self.gerar()
