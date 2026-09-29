"""Persistência SQLite local para auditoria, sinais, ordens e resultados."""

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path


class BancoDados:
    def __init__(self, caminho):
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self.caminho = caminho

    def _conexao(self):
        return sqlite3.connect(self.caminho)

    def inicializar(self):
        with self._conexao() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS market_data (id INTEGER PRIMARY KEY, symbol TEXT, payload TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS signals (id INTEGER PRIMARY KEY, symbol TEXT, payload TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS risk_validations (id INTEGER PRIMARY KEY, signal_id INTEGER, payload TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, symbol TEXT, payload TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            """)

    def registrar_mercado(self, symbol, payload):
        with self._conexao() as con:
            con.execute("INSERT INTO market_data(symbol,payload) VALUES (?,?)", (symbol, json.dumps(payload, default=str)))

    def registrar_sinal(self, sinal):
        with self._conexao() as con:
            cur = con.execute("INSERT INTO signals(symbol,payload) VALUES (?,?)", (sinal.symbol, json.dumps(asdict(sinal), default=str)))
            sinal.database_id = cur.lastrowid

    def registrar_validacao(self, sinal, aprovacao):
        with self._conexao() as con:
            con.execute("INSERT INTO risk_validations(signal_id,payload) VALUES (?,?)", (getattr(sinal, "database_id", None), json.dumps(asdict(aprovacao), default=str)))

    def registrar_ordem(self, ordem):
        with self._conexao() as con:
            con.execute("INSERT INTO orders(symbol,payload) VALUES (?,?)", (ordem.symbol, json.dumps(asdict(ordem), default=str)))

    def operacoes_recentes(self, dias=90):
        with self._conexao() as con:
            return con.execute("SELECT payload FROM orders WHERE created_at >= datetime('now', ?)", (f"-{dias} days",)).fetchall()
