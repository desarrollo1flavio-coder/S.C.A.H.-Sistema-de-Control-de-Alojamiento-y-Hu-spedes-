"""Sistema de logging centralizado para S.C.A.H. v2."""

import logging
import sys
from logging.handlers import RotatingFileHandler

from config.settings import (
    LOG_BACKUP_COUNT,
    LOG_DATE_FORMAT,
    LOG_FILE,
    LOG_FORMAT,
    LOG_MAX_BYTES,
)


def setup_logger(name: str = "scah", level: int = logging.DEBUG) -> logging.Logger:
    """Configura y retorna un logger con handlers de consola y archivo."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        file_handler = RotatingFileHandler(
            filename=str(LOG_FILE),
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        logger.warning("No se pudo crear el archivo de log: %s", e)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """Obtiene un logger hijo del logger principal."""
    parent_logger = setup_logger("scah")
    return parent_logger.getChild(module_name)
