"""Banco SQLite para armazenar dados de mercado, sinais e execuções."""

import json
import sqlite3
from pathlib import Path


class BancoDados:
    def __init__(self, caminho: str):
        self.caminho = caminho
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)

    def _conexao(self):
        return sqlite3.connect(self.caminho)

    def inicializar(self):
        with self._conexao() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    source TEXT DEFAULT 'manual',
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS risk_validations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id INTEGER,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def registrar_mercado(self, symbol: str, payload: dict, source: str = "market"):
        with self._conexao() as con:
            con.execute(
                "INSERT INTO market_data(symbol, source, payload) VALUES (?, ?, ?)",
                (symbol, source, json.dumps(payload, default=str)),
            )

    def registrar_sinal(self, sinal):
        with self._conexao() as con:
            cur = con.execute(
                "INSERT INTO signals(symbol, payload) VALUES (?, ?)",
                (sinal.symbol, json.dumps({k: getattr(sinal, k) for k in sinal.__dict__ if not k.startswith('_')}, default=str)),
            )
            sinal.database_id = cur.lastrowid

    def registrar_validacao(self, sinal, aprovacao):
        with self._conexao() as con:
            con.execute(
                "INSERT INTO risk_validations(signal_id, payload) VALUES (?, ?)",
                (getattr(sinal, 'database_id', None), json.dumps(aprovacao.__dict__, default=str)),
            )

    def registrar_ordem(self, ordem):
        with self._conexao() as con:
            con.execute(
                "INSERT INTO orders(symbol, payload) VALUES (?, ?)",
                (ordem.symbol, json.dumps(ordem.__dict__, default=str)),
            )

    def registrar_metricas(self, payload: dict):
        with self._conexao() as con:
            con.execute("INSERT INTO metrics(payload) VALUES (?)", (json.dumps(payload, default=str),))

    def buscar_ultimos_sinais(self, limite: int = 100):
        with self._conexao() as con:
            rows = con.execute("SELECT payload FROM signals ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
            return [json.loads(row[0]) for row in rows]

    def buscar_ordens(self, limite: int = 100):
        with self._conexao() as con:
            rows = con.execute("SELECT payload FROM orders ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
            return [json.loads(row[0]) for row in rows]
