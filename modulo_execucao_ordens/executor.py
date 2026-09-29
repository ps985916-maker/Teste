"""Ponto de entrada principal do agente em modo simulação."""

import logging
import time
from pathlib import Path

from dotenv import load_dotenv

from modulo_analise_ia.analisador import AnalisadorIA
from modulo_auto_aprendizado.relatorios import GeradorRelatorio
from modulo_coleta_dados.coletor import ColetorDados
from modulo_execucao_ordens.executor import ExecutorOrdens
from modulo_gestao_risco.risco import GestorRisco
from modulo_motor_decisao.motor import MotorDecisao
from shared.config import Config
from shared.database import BancoDados
from shared.logging_config import configurar_logging


def executar_ciclo(config, coletor, analisador, decisor, gestor_risco, executor, banco):
    """Executa um ciclo completo para todos os ativos e salva o resultado em SQLite."""
    for simbolo in config.symbols:
        try:
            mercado = coletor.coletar_mercado(simbolo)
            analise = analisador.analisar(simbolo, mercado)
            sinal = decisor.gerar_sinal(simbolo, analise)
            banco.registrar_sinal(sinal)

            market_price = mercado.get("ticker", {}).get("last")
            aprovacao = gestor_risco.validar(sinal, mercado, executor.saldo_disponivel())
            banco.registrar_validacao(sinal, aprovacao)

            if aprovacao.aprovado and market_price is not None:
                # Execução em simulação: o valor real do mercado é usado apenas para cálculo e registro.
                ordem = executor.executar(sinal, aprovacao, market_price)
                logging.info("Ordem aprovada para %s: %s | valor=%s | preço=%s", simbolo, ordem.action, ordem.amount, ordem.price)
            else:
                logging.warning("Ordem rejeitada para %s: %s", simbolo, aprovacao.motivos)
        except Exception:
            logging.exception("Erro no ciclo do ativo %s", simbolo)


def main():
    """Inicializa e mantém o loop principal do agente em modo simulação."""
    load_dotenv()
    config = Config.from_env()
    configurar_logging(config.log_level)
    Path("data").mkdir(parents=True, exist_ok=True)

    banco = BancoDados(config.database_path)
    banco.inicializar()

    coletor = ColetorDados(config, banco)
    analisador = AnalisadorIA(config, banco)
    decisor = MotorDecisao(config)
    gestor_risco = GestorRisco(config, banco)
    executor = ExecutorOrdens(config, banco)

    logging.warning("Agente iniciado em modo %s. Atenção: todos os mercados envolvem risco de prejuízo.", config.trading_mode)

    try:
        while True:
            executar_ciclo(config, coletor, analisador, decisor, gestor_risco, executor, banco)
            GeradorRelatorio(banco).gerar_semanal_if_needed()
            time.sleep(config.poll_interval_seconds)
    except KeyboardInterrupt:
        logging.info("Agente encerrado pelo operador.")


if __name__ == "__main__":
    main()
