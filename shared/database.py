"""Métricas de desempenho e sugestões de ajustes para o trader humano."""

import json
import logging
from statistics import mean


class GeradorRelatorio:
    def __init__(self, banco):
        self.banco = banco

    def gerar(self):
        sinais = self.banco.buscar_ultimos_sinais(500)
        ordens = self.banco.buscar_ordens(500)

        pnl_values = [float(item.get("pnl", 0.0)) for item in ordens if isinstance(item, dict)]
        total_ordens = len(ordens)
        wins = sum(1 for v in pnl_values if v > 0)
        losses = sum(1 for v in pnl_values if v < 0)

        if pnl_values:
            taxa_acerto = wins / total_ordens if total_ordens else 0.0
            lucro_medio = mean([v for v in pnl_values if v > 0]) if wins else 0.0
            prejuizo_medio = mean([abs(v) for v in pnl_values if v < 0]) if losses else 0.0
            drawdown = max(0.0, min(1.0, -min(0.0, sum(pnl_values)) / max(1.0, sum(abs(v) for v in pnl_values if v != 0) or 1)))
        else:
            taxa_acerto = 0.0
            lucro_medio = 0.0
            prejuizo_medio = 0.0
            drawdown = 0.0

        relatorio = {
            "total_sinais": len(sinais),
            "total_ordens": total_ordens,
            "taxa_acerto": taxa_acerto,
            "lucro_medio_por_operacao": lucro_medio,
            "prejuizo_medio": prejuizo_medio,
            "drawdown": drawdown,
            "ordens_simuladas": total_ordens,
            "sugestoes": [
                "Ajustar parâmetros técnicos para reduzir ruído em mercados laterais.",
                "Revisar prompts do LLM para evitar viés de sentimento em notícias de risco.",
                "Tighten stop-loss e reduzir alavancagem nas sessões de alta volatilidade.",
            ],
        }

        self.banco.registrar_metricas(relatorio)
        logging.info("Relatório de aprendizado: %s", json.dumps(relatorio, ensure_ascii=False))
        return relatorio

    def gerar_semanal_if_needed(self):
        return self.gerar()
