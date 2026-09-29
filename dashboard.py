"""Métricas de desempenho e sugestões de ajustes para o trader humano."""

import json
import logging


class GeradorRelatorio:
    def __init__(self, banco):
        self.banco = banco

    def _mean(self, values):
        return sum(values) / len(values) if values else 0.0

    def gerar(self):
        sinais = self.banco.buscar_ultimos_sinais(500)
        ordens = self.banco.buscar_ordens(500)

        pnl_values = []
        for item in ordens:
            if isinstance(item, dict):
                pnl = float(item.get("pnl", 0.0))
                pnl_values.append(pnl)

        total_ordens = len(ordens)
        wins = sum(1 for v in pnl_values if v > 0)
        losses = sum(1 for v in pnl_values if v < 0)
        win_pnl = [v for v in pnl_values if v > 0]
        loss_pnl = [abs(v) for v in pnl_values if v < 0]

        taxa_acerto = (wins / total_ordens) if total_ordens else 0.0
        lucro_medio = self._mean(win_pnl)
        prejuizo_medio = self._mean(loss_pnl)

        cumulative = 0.0
        running_max = 0.0
        drawdown = 0.0
        for value in pnl_values:
            cumulative += value
            if cumulative > running_max:
                running_max = cumulative
            drawdown = max(drawdown, running_max - cumulative)

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
