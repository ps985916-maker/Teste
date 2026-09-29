"""Resumo do agente em modo terminal para monitoramento simples."""

import json
import sqlite3
from pathlib import Path


def carregar_metricas(db_path: str):
    db = sqlite3.connect(db_path)
    rows = db.execute("SELECT payload FROM metrics ORDER BY id DESC LIMIT 10").fetchall()
    db.close()
    return [json.loads(row[0]) for row in rows]


def main():
    db_path = Path("data/trading_agent.sqlite3")
    if not db_path.exists():
        print("Banco ainda não existe. Rode o agente primeiro com: python main.py")
        return

    metrics = carregar_metricas(str(db_path))
    if not metrics:
        print("Sem métricas ainda. O agente precisa executar pelo menos um ciclo.")
        return

    latest = metrics[0]
    print("=== Dashboard do Agente de Trading ===")
    print(f"Total de sinais: {latest.get('total_sinais', 0)}")
    print(f"Ordens simuladas: {latest.get('total_ordens', 0)}")
    print(f"Taxa de acerto: {latest.get('taxa_acerto', 0.0):.2%}")
    print(f"Lucro médio por operação: {latest.get('lucro_medio_por_operacao', 0.0):.2f}")
    print(f"Prejuízo médio: {latest.get('prejuizo_medio', 0.0):.2f}")
    print(f"Drawdown: {latest.get('drawdown', 0.0):.2f}")
    print("Sugestões:")
    for sugestao in latest.get("sugestoes", []):
        print(f"- {sugestao}")


if __name__ == "__main__":
    main()
