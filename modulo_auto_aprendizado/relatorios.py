"""Métricas e sugestões para revisão humana; não altera código automaticamente."""

import json
import logging
from statistics import mean


class GeradorRelatorio:
    def __init__(self, banco):
        self.banco = banco

    def gerar(self):
        registros = [json.loads(row[0]) for row in self.banco.operacoes_recentes()]
        lucros = [float(x.get("pnl", 0)) for x in registros if "pnl" in x]
        relatorio = {"operacoes": len(registros), "taxa_acerto": None, "lucro_medio": mean(lucros) if lucros else 0.0, "sugestoes": ["Adicionar resultados reais de execução para calcular drawdown e taxa de acerto."]}
        if lucros:
            relatorio["taxa_acerto"] = sum(x > 0 for x in lucros) / len(lucros)
        logging.info("Relatório de aprendizado: %s", relatorio)
        return relatorio

    def gerar_semanal_if_needed(self):
        # Ponto de extensão para agendamento; sugestões sempre exigem revisão humana.
        return self.gerar()
