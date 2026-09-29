"""Logging consistente para produção e testes."""

import logging
from pathlib import Path


def configurar_logging(level: str = "INFO"):
    """Configura logging para console e arquivo."""
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/agent.log", encoding="utf-8"),
        ],
    )
