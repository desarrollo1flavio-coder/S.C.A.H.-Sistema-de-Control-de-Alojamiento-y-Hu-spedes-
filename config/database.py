"""Configuración y gestión de la base de datos SQLite para S.C.A.H.

Proporciona context managers para conexiones seguras,
ejecución de migraciones y operaciones de mantenimiento.
"""

import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

from config.settings import (
    DATABASE_BACKUP_DIR,
    DATABASE_PATH,
    DATABASE_TIMEOUT,
    MIGRATIONS_DIR,
)
from utils.exceptions import DatabaseConnectionError, MigrationError
from utils.logger import get_logger

logger = get_logger("database")


@contextmanager
def get_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager para obtener una conexión segura a la base de datos.

    Configura WAL mode, foreign keys y row_factory para acceso por nombre.

    Args:
        db_path: Ruta al archivo de BD. Si es None, usa la ruta por defecto.

    Yields:
        Conexión SQLite configurada.

    Raises:
        DatabaseConnectionError: Si no se puede establecer la conexión.
    """
    path = db_path or DATABASE_PATH
    conn = None
    try:
        conn = sqlite3.connect(
            str(path),
            timeout=DATABASE_TIMEOUT,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA encoding='UTF-8'")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = sqlite3.Row
        logger.debug("Conexión establecida a: %s", path)
        yield conn
    except sqlite3.Error as e:
        logger.error("Error de conexión a BD (%s): %s", path, e)
        raise DatabaseConnectionError(f"No se pudo conectar a la base de datos: {e}") from e
    finally:
        if conn:
            try:
                conn.close()
                logger.debug("Conexión cerrada correctamente")
            except sqlite3.Error as e:
                logger.warning("Error al cerrar conexión: %s", e)


@contextmanager
def get_transaction(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager para operaciones dentro de una transacción.

    Hace commit automático al salir del bloque. Rollback si hay excepción.

    Args:
        db_path: Ruta al archivo de BD.

    Yields:
        Conexión SQLite dentro de una transacción.
    """
    with get_connection(db_path) as conn:
        try:
            yield conn
            conn.commit()
            logger.debug("Transacción completada (commit)")
        except Exception as e:
            conn.rollback()
            logger.warning("Transacción revertida (rollback): %s", e)
            raise


def initialize_database() -> None:
    """Inicializa la base de datos ejecutando todas las migraciones pendientes.

    Busca archivos .sql en el directorio de migraciones y los ejecuta
    en orden numérico. Mantiene un registro de migraciones aplicadas.

    Raises:
        MigrationError: Si ocurre un error durante la migración.
    """
    logger.info("Inicializando base de datos...")
    try:
        with get_transaction() as conn:
            # Crear tabla de control de migraciones
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _migraciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    archivo TEXT UNIQUE NOT NULL,
                    fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Obtener migraciones ya aplicadas
            cursor = conn.execute("SELECT archivo FROM _migraciones")
            aplicadas = {row["archivo"] for row in cursor.fetchall()}

            # Buscar y ejecutar migraciones pendientes
            migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
            if not migration_files:
                logger.warning("No se encontraron archivos de migración en %s", MIGRATIONS_DIR)
                return

            for migration_file in migration_files:
                if migration_file.name in aplicadas:
                    logger.debug("Migración ya aplicada: %s", migration_file.name)
                    continue

                logger.info("Aplicando migración: %s", migration_file.name)
                sql_content = migration_file.read_text(encoding="utf-8")
                conn.executescript(sql_content)
                conn.execute(
                    "INSERT INTO _migraciones (archivo) VALUES (?)",
                    (migration_file.name,),
                )
                logger.info("Migración aplicada exitosamente: %s", migration_file.name)

        logger.info("Base de datos inicializada correctamente")
    except sqlite3.Error as e:
        logger.error("Error durante la migración: %s", e)
        raise MigrationError(f"Error al inicializar la base de datos: {e}") from e


def create_backup() -> Path:
    """Crea una copia de seguridad de la base de datos.

    Returns:
        Ruta al archivo de backup creado.

    Raises:
        DatabaseConnectionError: Si no se puede acceder a la BD.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"scah_backup_{timestamp}.db"
    backup_path = DATABASE_BACKUP_DIR / backup_filename

    try:
        if DATABASE_PATH.exists():
            shutil.copy2(str(DATABASE_PATH), str(backup_path))
            logger.info("Backup creado: %s", backup_path)
            return backup_path
        raise DatabaseConnectionError("No se encontró el archivo de base de datos")
    except (OSError, shutil.Error) as e:
        logger.error("Error al crear backup: %s", e)
        raise DatabaseConnectionError(f"Error al crear backup: {e}") from e


def check_database_health() -> dict[str, str | int | bool]:
    """Verifica el estado de salud de la base de datos.

    Returns:
        Diccionario con métricas: exists, size_mb, tables, integrity.
    """
    result: dict[str, str | int | bool] = {
        "exists": DATABASE_PATH.exists(),
        "size_mb": 0,
        "tables": 0,
        "integrity": "unknown",
    }
    if not DATABASE_PATH.exists():
        return result

    result["size_mb"] = round(DATABASE_PATH.stat().st_size / (1024 * 1024), 2)
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE '_%'"
            )
            result["tables"] = cursor.fetchone()["count"]
            cursor = conn.execute("PRAGMA integrity_check")
            result["integrity"] = cursor.fetchone()[0]
    except Exception as e:
        result["integrity"] = f"Error: {e}"
        logger.error("Error al verificar salud de BD: %s", e)

    return result
