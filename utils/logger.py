"""Sistema de logging centralizado para S.C.A.H.

Configura un logger con salida a consola y archivo rotativo.
Todos los módulos deben usar este sistema para sus logs.
"""

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
    """Configura y retorna un logger con handlers de consola y archivo.

    Args:
        name: Nombre del logger. Usar nombres jerárquicos (ej: 'scah.auth').
        level: Nivel mínimo de logging.

    Returns:
        Logger configurado y listo para usar.
    """
    logger = logging.getLogger(name)

    # Evitar agregar handlers duplicados
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler de archivo rotativo
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
    """Obtiene un logger hijo del logger principal.

    Args:
        module_name: Nombre del módulo que solicita el logger.

    Returns:
        Logger configurado como hijo del logger principal 'scah'.
    """
    parent_logger = setup_logger("scah")
    return parent_logger.getChild(module_name)
