"""Ponto de entrada do agente de trading em modo seguro."""

import logging
import os
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


def executar_ciclo(config, coletor, analisador, decisor, risco, executor, banco):
    """Executa um ciclo completo; falhas por ativo não derrubam o agente inteiro."""
    for simbolo in config.symbols:
        try:
            mercado = coletor.coletar_mercado(simbolo)
            analise = analisador.analisar(simbolo, mercado)
            sinal = decisor.gerar_sinal(simbolo, analise)
            banco.registrar_sinal(sinal)
            aprovacao = risco.validar(sinal, mercado, executor.saldo_disponivel())
            banco.registrar_validacao(sinal, aprovacao)
            if aprovacao.aprovado:
                resultado = executor.executar(sinal, aprovacao)
                banco.registrar_ordem(resultado)
            else:
                logging.info("Sinal %s bloqueado: %s", simbolo, aprovacao.motivos)
        except Exception:
            # Dados externos podem falhar; registrar e continuar no próximo ativo/ciclo.
            logging.exception("Falha no ciclo do ativo %s", simbolo)


def main():
    """Inicializa componentes e mantém o loop principal com intervalo configurável."""
    load_dotenv()
    config = Config.from_env()
    configurar_logging(config.log_level)
    Path("data").mkdir(exist_ok=True)
    banco = BancoDados(config.database_path)
    banco.inicializar()
    coletor = ColetorDados(config, banco)
    analisador = AnalisadorIA(config, banco)
    decisor = MotorDecisao(config)
    risco = GestorRisco(config, banco)
    executor = ExecutorOrdens(config, banco)

    logging.warning("Agente iniciado em modo %s. Mercado financeiro envolve risco de prejuízo.", config.trading_mode)
    try:
        while True:
            executar_ciclo(config, coletor, analisador, decisor, risco, executor, banco)
            GeradorRelatorio(banco).gerar_semanal_if_needed()
            time.sleep(config.poll_interval_seconds)
    except KeyboardInterrupt:
        logging.info("Agente encerrado pelo operador.")


if __name__ == "__main__":
    main()
