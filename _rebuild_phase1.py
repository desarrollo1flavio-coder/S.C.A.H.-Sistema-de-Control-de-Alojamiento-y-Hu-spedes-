"""Script de reconstrucción S.C.A.H. v2.

Ejecutar UNA VEZ para reescribir todos los archivos del proyecto.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

FILES = {}

# ============================================================
# config/settings.py
# ============================================================
FILES["config/settings.py"] = '''\
"""Configuración global del sistema S.C.A.H. v2.

Define constantes, rutas y parámetros de configuración utilizados
en toda la aplicación.
"""

from pathlib import Path

# ============================================================
# RUTAS DEL PROYECTO
# ============================================================
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATABASE_DIR: Path = BASE_DIR / "database"
MIGRATIONS_DIR: Path = DATABASE_DIR / "migrations"
LOGS_DIR: Path = BASE_DIR / "logs"
ASSETS_DIR: Path = BASE_DIR / "assets"
ICONS_DIR: Path = ASSETS_DIR / "icons"
THEMES_DIR: Path = ASSETS_DIR / "themes"

for _dir in [DATABASE_DIR, MIGRATIONS_DIR, LOGS_DIR, ASSETS_DIR, ICONS_DIR, THEMES_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ============================================================
# BASE DE DATOS
# ============================================================
DATABASE_PATH: Path = DATABASE_DIR / "scah.db"
DATABASE_BACKUP_DIR: Path = DATABASE_DIR / "backups"
DATABASE_TIMEOUT: int = 30
DATABASE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# SEGURIDAD
# ============================================================
BCRYPT_WORK_FACTOR: int = 12
MAX_LOGIN_ATTEMPTS: int = 3
LOCKOUT_DURATION_MINUTES: int = 15
SESSION_TIMEOUT_MINUTES: int = 480

DEFAULT_ADMIN_USERNAME: str = "admin"
DEFAULT_ADMIN_PASSWORD: str = "Admin2026!"
DEFAULT_ADMIN_FULLNAME: str = "Administrador del Sistema"

# ============================================================
# UI
# ============================================================
APP_TITLE: str = "S.C.A.H. - Sistema de Control de Alojamiento y Huéspedes"
APP_VERSION: str = "2.0.0"
APP_ORGANIZATION: str = "Departamento de Inteligencia Criminal - Policía de Tucumán"
APP_SUBTITLE: str = "Sección Hoteles"

LOGIN_WINDOW_SIZE: str = "450x550"
LOGIN_WINDOW_RESIZABLE: bool = False
DEFAULT_APPEARANCE_MODE: str = "dark"
DEFAULT_COLOR_THEME: str = "blue"
DEBOUNCE_MS: int = 300
PAGINATION_SIZE: int = 50

# ============================================================
# BACKUP AUTOMÁTICO
# ============================================================
BACKUP_ENABLED: bool = True
BACKUP_INTERVAL_HOURS: int = 24
BACKUP_MAX_FILES: int = 10

# ============================================================
# IMPORTACIÓN EXCEL
# ============================================================
ALLOWED_EXTENSIONS: list[str] = [".xlsx", ".xls"]
MAX_IMPORT_ROWS: int = 10000
PREVIEW_ROWS: int = 10

COLUMNAS_IGNORAR: list[str] = [
    "n°", "nro", "nº", "n", "#", "numero", "número",
    "item", "orden", "nro.", "n°.",
]

COLUMNAS_MAPEO: dict[str, list[str]] = {
    "nacionalidad": [
        "nacionalidad", "pais", "país", "country", "nation", "nacion", "nación",
    ],
    "procedencia": [
        "procedencia", "origen", "ciudad_origen", "from", "domicilio",
        "direccion", "dirección", "ciudad",
    ],
    "apellido_nombre": [
        "apellido_y_nombre", "apellido/nombre", "apellido_nombre",
        "apellido_y_nombres", "apellidos_y_nombre",
        "apellidos_y_nombres", "nombre_y_apellido",
        "nombre_apellido", "nombres_y_apellido",
    ],
    "apellido": ["apellido", "apellidos", "last_name", "surname"],
    "nombre": ["nombre", "nombres", "first_name", "name"],
    "dni": [
        "dni", "documento", "nro_documento", "document",
        "d.n.i", "d.n.i.", "n°_doc", "nro_doc", "n_doc",
        "n°_documento", "nº_doc", "nº_documento",
        "numero_documento", "número_documento", "numero_doc",
        "n°doc", "n°_de_doc", "nro._doc", "nro._documento",
        "dni/pasaporte", "dni_/_pasaporte", "dni_o_pasaporte",
        "d.n.i._/_pas.", "d.n.i._/_pas", "dni_/_pas.", "dni_/_pas",
        "dni/pas", "d.n.i./pas.", "d.n.i./pas", "d.n.i./pasaporte",
        "dni/pas.", "d.n.i_/_pas", "dni_pas",
    ],
    "pasaporte": [
        "pasaporte", "passport", "nro_pasaporte",
        "n°_pasaporte", "nº_pasaporte",
    ],
    "edad": ["edad", "age", "años", "edades"],
    "fecha_nacimiento": [
        "fecha_nacimiento", "fecha_de_nacimiento", "nacimiento",
        "fecha_de_nac.", "fecha_de_nac", "fecha_nac", "fecha_nac.",
        "f._nac.", "f._nac", "fec._nac.", "fec._nac",
        "fec._nacimiento", "f.nac", "f.nac.", "fec.nac",
        "fec.nac.", "birth_date", "date_of_birth",
        "fch_nac", "fch._nac", "fch._nac.",
    ],
    "profesion": [
        "profesion", "profesión", "ocupacion", "ocupación",
        "profession", "occupation", "prof", "prof.",
    ],
    "establecimiento": [
        "hotel", "establecimiento", "alojamiento",
        "hostal", "pension", "pensión", "hospedaje",
        "hosteria", "hostería", "apart", "apart_hotel",
        "motel", "residencial", "posada",
    ],
    "habitacion": [
        "habitacion", "habitación", "room",
        "nro_habitacion", "nro_habitación", "cuarto",
        "n°_hab", "n°_hab.", "nº_hab", "nro._hab",
        "n°_habitacion", "n°_habitación",
    ],
    "destino": ["destino", "destination", "hacia", "a_donde", "destino_a"],
    "vehiculo": [
        "vehiculo", "vehículo", "vehicle", "auto", "coche",
        "vehic", "vehic.", "patente", "dominio",
        "datos_vehiculo", "datos_vehículo",
    ],
    "telefono": [
        "telefono", "teléfono", "phone",
        "celular", "mobile", "nro_telefono", "nro_teléfono",
        "n°_tel", "n°_tel.", "nº_tel", "contacto",
    ],
    "fecha_entrada": [
        "fecha_entrada", "ingreso", "check_in", "entrada",
        "checkin", "fecha_ingreso", "f._entrada", "f._ingreso",
        "fecha_de_entrada", "fecha_de_ingreso",
        "fec._entrada", "fec._ingreso",
        "f.entrada", "f.ingreso", "fec.entrada", "fec.ingreso",
    ],
    "fecha_salida": [
        "fecha_salida", "egreso", "check_out", "salida",
        "checkout", "fecha_egreso", "f._salida", "f._egreso",
        "fecha_de_salida", "fecha_de_egreso",
        "fec._salida", "fec._egreso",
        "f.salida", "f.egreso", "fec.salida", "fec.egreso",
    ],
}

# ============================================================
# LOGGING
# ============================================================
LOG_FILE: Path = LOGS_DIR / "scah.log"
LOG_MAX_BYTES: int = 5 * 1024 * 1024
LOG_BACKUP_COUNT: int = 5
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# ============================================================
# LISTAS PREDEFINIDAS
# ============================================================
NACIONALIDADES: list[str] = [
    "Argentina", "Bolivia", "Brasil", "Chile", "Colombia", "Ecuador",
    "Paraguay", "Perú", "Uruguay", "Venezuela", "México", "Cuba",
    "Estados Unidos", "Canadá", "España", "Italia", "Francia",
    "Alemania", "Reino Unido", "China", "Japón", "Corea del Sur",
    "India", "Australia", "Otra",
]

PROVINCIAS_ARGENTINA: list[str] = [
    "Buenos Aires", "CABA", "Catamarca", "Chaco", "Chubut",
    "Córdoba", "Corrientes", "Entre Ríos", "Formosa", "Jujuy",
    "La Pampa", "La Rioja", "Mendoza", "Misiones", "Neuquén",
    "Río Negro", "Salta", "San Juan", "San Luis", "Santa Cruz",
    "Santa Fe", "Santiago del Estero", "Tierra del Fuego", "Tucumán",
]

ROLES_USUARIO: list[str] = ["admin", "supervisor", "operador"]
TIPOS_HABITACION: list[str] = ["standard", "doble", "triple", "suite", "familiar", "otro"]
ESTADOS_HABITACION: list[str] = ["disponible", "ocupada", "mantenimiento", "reservada"]
'''

# ============================================================
# config/database.py
# ============================================================
FILES["config/database.py"] = '''\
"""Configuración y gestión de la base de datos SQLite para S.C.A.H. v2.

Proporciona context managers para conexiones seguras,
ejecución de migraciones y operaciones de mantenimiento.
"""

import shutil
import sqlite3
import re
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

from config.settings import (
    DATABASE_BACKUP_DIR,
    DATABASE_PATH,
    DATABASE_TIMEOUT,
    MIGRATIONS_DIR,
    BACKUP_MAX_FILES,
)
from utils.exceptions import DatabaseConnectionError, MigrationError
from utils.logger import get_logger

logger = get_logger("database")


@contextmanager
def get_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager para obtener una conexión segura a la base de datos."""
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
        conn.execute("PRAGMA encoding=\'UTF-8\'")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error("Error de conexión a BD (%s): %s", path, e)
        raise DatabaseConnectionError(f"No se pudo conectar a la base de datos: {e}") from e
    finally:
        if conn:
            try:
                conn.close()
            except sqlite3.Error as e:
                logger.warning("Error al cerrar conexión: %s", e)


@contextmanager
def get_transaction(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager para operaciones dentro de una transacción."""
    with get_connection(db_path) as conn:
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.warning("Transacción revertida (rollback): %s", e)
            raise


def _is_skippable_migration_error(
    conn: sqlite3.Connection,
    sql_content: str,
    error: sqlite3.Error,
) -> bool:
    """Determina si un error de migración es seguro de omitir."""
    error_text = str(error).lower()

    # Tabla o columna duplicada
    if "already exists" in error_text or "duplicate column" in error_text:
        return True

    # Columna duplicada con nombre específico
    marker = "duplicate column name:"
    if marker in error_text:
        return True

    return False


def initialize_database() -> None:
    """Inicializa la base de datos ejecutando todas las migraciones pendientes."""
    logger.info("Inicializando base de datos...")
    try:
        with get_transaction() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _migraciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    archivo TEXT UNIQUE NOT NULL,
                    fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor = conn.execute("SELECT archivo FROM _migraciones")
            aplicadas = {row["archivo"] for row in cursor.fetchall()}

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
                try:
                    conn.executescript(sql_content)
                except sqlite3.Error as e:
                    if _is_skippable_migration_error(conn, sql_content, e):
                        logger.warning(
                            "Migración %s: esquema ya contiene el cambio (%s)",
                            migration_file.name, e,
                        )
                    else:
                        raise

                # Re-registrar si no fue rollbackeado
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO _migraciones (archivo) VALUES (?)",
                        (migration_file.name,),
                    )
                except sqlite3.Error:
                    pass
                logger.info("Migración aplicada: %s", migration_file.name)

        logger.info("Base de datos inicializada correctamente")
    except sqlite3.Error as e:
        logger.error("Error durante la migración: %s", e)
        raise MigrationError(f"Error al inicializar la base de datos: {e}") from e


def create_backup() -> Path:
    """Crea una copia de seguridad de la base de datos."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"scah_backup_{timestamp}.db"
    backup_path = DATABASE_BACKUP_DIR / backup_filename

    try:
        if DATABASE_PATH.exists():
            shutil.copy2(str(DATABASE_PATH), str(backup_path))
            logger.info("Backup creado: %s", backup_path)
            _cleanup_old_backups()
            return backup_path
        raise DatabaseConnectionError("No se encontró el archivo de base de datos")
    except (OSError, shutil.Error) as e:
        logger.error("Error al crear backup: %s", e)
        raise DatabaseConnectionError(f"Error al crear backup: {e}") from e


def _cleanup_old_backups() -> None:
    """Elimina backups antiguos manteniendo solo los más recientes."""
    try:
        backups = sorted(
            DATABASE_BACKUP_DIR.glob("scah_backup_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old_backup in backups[BACKUP_MAX_FILES:]:
            old_backup.unlink()
            logger.info("Backup antiguo eliminado: %s", old_backup.name)
    except Exception as e:
        logger.warning("Error al limpiar backups: %s", e)


def check_database_health() -> dict[str, str | int | bool]:
    """Verifica el estado de salud de la base de datos."""
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
                "WHERE type=\'table\' AND name NOT LIKE \'_%\'"
            )
            result["tables"] = cursor.fetchone()["count"]
            cursor = conn.execute("PRAGMA integrity_check")
            result["integrity"] = cursor.fetchone()[0]
    except Exception as e:
        result["integrity"] = f"Error: {e}"
        logger.error("Error al verificar salud de BD: %s", e)

    return result
'''

# ============================================================
# config/__init__.py
# ============================================================
FILES["config/__init__.py"] = '''\
"""Módulo de configuración de S.C.A.H. v2."""
'''

# ============================================================
# utils/exceptions.py
# ============================================================
FILES["utils/exceptions.py"] = '''\
"""Excepciones personalizadas del sistema S.C.A.H. v2."""


class SCAHBaseError(Exception):
    """Excepción base para todas las excepciones del sistema."""

    def __init__(self, message: str = "Error interno del sistema", code: str = "SCAH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# -- Errores de Base de Datos --
class DatabaseError(SCAHBaseError):
    def __init__(self, message: str = "Error en la base de datos"):
        super().__init__(message, "DB_ERROR")


class DatabaseConnectionError(DatabaseError):
    def __init__(self, message: str = "No se pudo conectar a la base de datos"):
        super().__init__(message)
        self.code = "DB_CONNECTION_ERROR"


class MigrationError(DatabaseError):
    def __init__(self, message: str = "Error al ejecutar migración"):
        super().__init__(message)
        self.code = "DB_MIGRATION_ERROR"


# -- Errores de Autenticación --
class AuthenticationError(SCAHBaseError):
    def __init__(self, message: str = "Error de autenticación"):
        super().__init__(message, "AUTH_ERROR")


class InvalidCredentialsError(AuthenticationError):
    def __init__(self, message: str = "Usuario o contraseña incorrectos"):
        super().__init__(message)
        self.code = "AUTH_INVALID_CREDENTIALS"


class AccountLockedError(AuthenticationError):
    def __init__(self, message: str = "Cuenta bloqueada temporalmente", minutes_remaining: int = 0):
        self.minutes_remaining = minutes_remaining
        if minutes_remaining > 0:
            message = f"Cuenta bloqueada. Intente nuevamente en {minutes_remaining} minutos"
        super().__init__(message)
        self.code = "AUTH_ACCOUNT_LOCKED"


class AccountDisabledError(AuthenticationError):
    def __init__(self, message: str = "Cuenta deshabilitada. Contacte al administrador"):
        super().__init__(message)
        self.code = "AUTH_ACCOUNT_DISABLED"


class UserNotFoundError(AuthenticationError):
    def __init__(self, message: str = "Usuario no encontrado"):
        super().__init__(message)
        self.code = "AUTH_USER_NOT_FOUND"


# -- Errores de Validación --
class ValidationError(SCAHBaseError):
    def __init__(self, message: str = "Datos inválidos", field: str = ""):
        self.field = field
        if field:
            message = f"Campo \'{field}\': {message}"
        super().__init__(message, "VALIDATION_ERROR")


class DuplicateRecordError(ValidationError):
    def __init__(self, message: str = "El registro ya existe", field: str = ""):
        super().__init__(message, field)
        self.code = "VALIDATION_DUPLICATE"


# -- Errores de Importación --
class ImportFileError(SCAHBaseError):
    def __init__(self, message: str = "Error durante la importación"):
        super().__init__(message, "IMPORT_ERROR")


class InvalidFileFormatError(ImportFileError):
    def __init__(self, message: str = "Formato de archivo no válido"):
        super().__init__(message)
        self.code = "IMPORT_INVALID_FORMAT"


class MissingColumnsError(ImportFileError):
    def __init__(self, message: str = "Faltan columnas requeridas", missing: list[str] | None = None):
        self.missing_columns = missing or []
        if missing:
            cols = ", ".join(missing)
            message = f"Columnas faltantes: {cols}"
        super().__init__(message)
        self.code = "IMPORT_MISSING_COLUMNS"


# -- Errores de Permisos --
class PermissionDeniedError(SCAHBaseError):
    def __init__(self, message: str = "No tiene permisos para realizar esta acción"):
        super().__init__(message, "PERMISSION_DENIED")


# -- Errores de Establecimiento / Habitación --
class EstablecimientoError(SCAHBaseError):
    def __init__(self, message: str = "Error de establecimiento"):
        super().__init__(message, "ESTABLECIMIENTO_ERROR")


class HabitacionError(SCAHBaseError):
    def __init__(self, message: str = "Error de habitación"):
        super().__init__(message, "HABITACION_ERROR")
'''

# ============================================================
# utils/logger.py  (sin cambios significativos)
# ============================================================
FILES["utils/logger.py"] = '''\
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
'''

# ============================================================
# utils/encryption.py  (sin cambios)
# ============================================================
FILES["utils/encryption.py"] = '''\
"""Funciones de seguridad y encriptación para S.C.A.H. v2."""

import bcrypt

from config.settings import BCRYPT_WORK_FACTOR
from utils.logger import get_logger

logger = get_logger("encryption")


def hash_password(password: str) -> str:
    """Genera un hash bcrypt seguro para una contraseña."""
    if not password:
        raise ValueError("La contraseña no puede estar vacía")
    try:
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=BCRYPT_WORK_FACTOR)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")
    except Exception as e:
        logger.error("Error al hashear contraseña: %s", e)
        raise RuntimeError("Error al procesar la contraseña") from e


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica si una contraseña coincide con su hash bcrypt."""
    if not password or not password_hash:
        raise ValueError("La contraseña y el hash no pueden estar vacíos")
    try:
        password_bytes = password.encode("utf-8")
        hash_bytes = password_hash.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except (ValueError, TypeError):
        return False
    except Exception as e:
        logger.error("Error inesperado al verificar contraseña: %s", e)
        return False


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Valida que una contraseña cumpla los requisitos mínimos de seguridad."""
    errors: list[str] = []
    if len(password) < 8:
        errors.append("Debe tener al menos 8 caracteres")
    if not any(c.isupper() for c in password):
        errors.append("Debe contener al menos una letra mayúscula")
    if not any(c.islower() for c in password):
        errors.append("Debe contener al menos una letra minúscula")
    if not any(c.isdigit() for c in password):
        errors.append("Debe contener al menos un número")
    special_chars = "!@#$%^&*.,_-"
    if not any(c in special_chars for c in password):
        errors.append(f"Debe contener al menos un carácter especial ({special_chars})")
    return len(errors) == 0, errors
'''

# ============================================================
# utils/validators.py
# ============================================================
FILES["utils/validators.py"] = '''\
"""Validaciones de datos para el sistema S.C.A.H. v2."""

import re
from datetime import date, datetime

from utils.logger import get_logger

logger = get_logger("validators")

DNI_PATTERN: re.Pattern[str] = re.compile(r"^\\d{7,8}$")
PASAPORTE_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9]{5,15}$")
TELEFONO_PATTERN: re.Pattern[str] = re.compile(r"^[\\+\\-\\d\\s\\(\\)]{6,20}$")
NOMBRE_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-záéíóúñÁÉÍÓÚÑüÜ\\s\\'\\-\\.]{2,100}$")


def validar_dni(dni: str) -> tuple[bool, str]:
    """Valida el formato de un número de DNI argentino (7-8 dígitos)."""
    if not dni or not dni.strip():
        return True, ""
    dni_limpio = dni.strip().replace(".", "").replace("-", "").replace(" ", "")
    if dni_limpio.endswith(".0"):
        dni_limpio = dni_limpio[:-2]
    if DNI_PATTERN.match(dni_limpio):
        return True, ""
    return False, "El DNI debe tener 7 u 8 dígitos numéricos"


def limpiar_dni(dni: str) -> str:
    """Limpia un DNI removiendo puntos, guiones y espacios."""
    if not dni:
        return ""
    limpio = dni.strip().replace(".", "").replace("-", "").replace(" ", "")
    if limpio.endswith(".0"):
        limpio = limpio[:-2]
    return limpio


def validar_pasaporte(pasaporte: str) -> tuple[bool, str]:
    """Valida el formato de un número de pasaporte (5-15 alfanumérico)."""
    if not pasaporte or not pasaporte.strip():
        return True, ""
    pasaporte_limpio = pasaporte.strip()
    if PASAPORTE_PATTERN.match(pasaporte_limpio):
        return True, ""
    return False, "El pasaporte debe tener entre 5 y 15 caracteres alfanuméricos"


def validar_dni_o_pasaporte(dni: str, pasaporte: str) -> tuple[bool, str]:
    """Valida que al menos uno de los dos documentos esté presente y sea válido."""
    tiene_dni = bool(dni and dni.strip())
    tiene_pasaporte = bool(pasaporte and pasaporte.strip())

    if not tiene_dni and not tiene_pasaporte:
        return False, "Debe ingresar al menos DNI o Pasaporte"

    errors: list[str] = []
    if tiene_dni:
        valido, msg = validar_dni(dni)
        if not valido:
            errors.append(msg)
    if tiene_pasaporte:
        valido, msg = validar_pasaporte(pasaporte)
        if not valido:
            errors.append(msg)

    if errors:
        return False, "; ".join(errors)
    return True, ""


def validar_telefono(telefono: str) -> tuple[bool, str]:
    """Valida el formato de un número de teléfono."""
    if not telefono or not telefono.strip():
        return True, ""
    if TELEFONO_PATTERN.match(telefono.strip()):
        return True, ""
    return False, "Formato de teléfono inválido"


def validar_nombre(valor: str, campo: str = "Nombre") -> tuple[bool, str]:
    """Valida un nombre o apellido."""
    if not valor or not valor.strip():
        return False, f"{campo} es obligatorio"
    valor_limpio = valor.strip()
    if len(valor_limpio) < 2:
        return False, f"{campo} debe tener al menos 2 caracteres"
    if NOMBRE_PATTERN.match(valor_limpio):
        return True, ""
    return False, f"{campo} contiene caracteres no válidos"


def validar_edad(edad) -> tuple[bool, str]:
    """Valida que la edad sea un número válido entre 0 y 150."""
    if edad is None or (isinstance(edad, str) and not edad.strip()):
        return True, ""
    try:
        edad_int = int(float(str(edad)))
    except (ValueError, TypeError):
        return False, "La edad debe ser un número entero"
    if edad_int < 0 or edad_int > 150:
        return False, "La edad debe estar entre 0 y 150 años"
    return True, ""


def validar_fecha_entrada(fecha) -> tuple[bool, str]:
    """Valida la fecha de entrada."""
    if not fecha:
        return False, "La fecha de entrada es obligatoria"
    try:
        if isinstance(fecha, str):
            fecha_obj = datetime.strptime(fecha.strip(), "%Y-%m-%d").date()
        else:
            fecha_obj = fecha
        return True, ""
    except ValueError:
        return False, "Formato de fecha inválido. Use AAAA-MM-DD"


def validar_fecha_salida(fecha_salida, fecha_entrada) -> tuple[bool, str]:
    """Valida la fecha de salida en relación a la fecha de entrada."""
    if not fecha_salida:
        return True, ""
    try:
        if isinstance(fecha_salida, str):
            salida = datetime.strptime(fecha_salida.strip(), "%Y-%m-%d").date()
        else:
            salida = fecha_salida
        if isinstance(fecha_entrada, str):
            entrada = datetime.strptime(fecha_entrada.strip(), "%Y-%m-%d").date()
        else:
            entrada = fecha_entrada
        if salida < entrada:
            return False, "La fecha de salida no puede ser anterior a la de entrada"
        return True, ""
    except ValueError:
        return False, "Formato de fecha inválido. Use AAAA-MM-DD"


def sanitizar_texto(texto: str) -> str:
    """Sanitiza un texto eliminando caracteres peligrosos y espacios extra."""
    if not texto:
        return ""
    limpio = " ".join(texto.strip().split())
    limpio = re.sub(r"[\\x00-\\x1f\\x7f-\\x9f]", "", limpio)
    return limpio
'''

# ============================================================
# utils/__init__.py
# ============================================================
FILES["utils/__init__.py"] = '''\
"""Módulo de utilidades de S.C.A.H. v2."""
'''

# ============================================================
# models/__init__.py
# ============================================================
FILES["models/__init__.py"] = '''\
"""Modelos de datos de S.C.A.H. v2."""
'''

# ============================================================
# models/persona.py
# ============================================================
FILES["models/persona.py"] = '''\
"""Modelo y DAO de Persona para S.C.A.H. v2.

Almacena datos fijos de una persona (separado de sus estadías).
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from config.database import get_connection, get_transaction
from config.settings import PAGINATION_SIZE
from utils.logger import get_logger
from utils.validators import sanitizar_texto, limpiar_dni

logger = get_logger("models.persona")


class PersonaSchema(BaseModel):
    """Esquema de validación para datos de persona."""

    nacionalidad: str = Field(..., min_length=2, max_length=100)
    procedencia: str = Field(..., min_length=2, max_length=200)
    apellido: str = Field(..., min_length=1, max_length=100)
    nombre: str = Field(..., min_length=1, max_length=100)
    dni: Optional[str] = Field(default=None, max_length=8)
    pasaporte: Optional[str] = Field(default=None, max_length=15)
    fecha_nacimiento: Optional[date] = None
    profesion: Optional[str] = Field(default=None, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=30)

    @model_validator(mode="after")
    def validar_documento(self) -> "PersonaSchema":
        if not self.dni and not self.pasaporte:
            raise ValueError("Debe ingresar al menos DNI o Pasaporte")
        return self

    @field_validator("apellido", "nombre", "nacionalidad", "procedencia")
    @classmethod
    def sanitizar(cls, v: str) -> str:
        return sanitizar_texto(v)

    @field_validator("dni")
    @classmethod
    def validar_formato_dni(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = limpiar_dni(v)
        if not v.isdigit() or len(v) < 7 or len(v) > 8:
            raise ValueError("El DNI debe tener 7 u 8 dígitos numéricos")
        return v

    @field_validator("pasaporte")
    @classmethod
    def validar_formato_pasaporte(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip().upper()
        if not v.isalnum() or len(v) < 5 or len(v) > 15:
            raise ValueError("El pasaporte debe tener entre 5 y 15 caracteres alfanuméricos")
        return v


class PersonaDAO:
    """Operaciones de base de datos para la tabla \'personas\'."""

    @staticmethod
    def crear(datos: dict) -> int:
        """Crea un nuevo registro de persona."""
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO personas "
                "(nacionalidad, procedencia, apellido, nombre, dni, pasaporte, "
                "fecha_nacimiento, profesion, telefono) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datos["nacionalidad"],
                    datos["procedencia"],
                    datos["apellido"],
                    datos["nombre"],
                    datos.get("dni"),
                    datos.get("pasaporte"),
                    str(datos["fecha_nacimiento"]) if datos.get("fecha_nacimiento") else None,
                    datos.get("profesion"),
                    datos.get("telefono"),
                ),
            )
            persona_id = cursor.lastrowid
            logger.info("Persona creada ID %d: %s %s", persona_id, datos["apellido"], datos["nombre"])
            return persona_id

    @staticmethod
    def obtener_por_id(persona_id: int) -> Optional[dict]:
        """Obtiene una persona por su ID."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM personas WHERE id = ? AND activo = 1",
                (persona_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def buscar_por_documento(dni: str | None = None, pasaporte: str | None = None) -> Optional[dict]:
        """Busca una persona por DNI o pasaporte. Retorna la primera coincidencia."""
        with get_connection() as conn:
            if dni:
                cursor = conn.execute(
                    "SELECT * FROM personas WHERE dni = ? AND activo = 1", (dni.strip(),)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
            if pasaporte:
                cursor = conn.execute(
                    "SELECT * FROM personas WHERE pasaporte = ? AND activo = 1",
                    (pasaporte.strip(),),
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
        return None

    @staticmethod
    def actualizar(persona_id: int, datos: dict) -> bool:
        """Actualiza los datos de una persona."""
        campos_permitidos = [
            "nacionalidad", "procedencia", "apellido", "nombre", "dni", "pasaporte",
            "fecha_nacimiento", "profesion", "telefono",
        ]
        campos: list[str] = []
        valores: list = []

        for campo in campos_permitidos:
            if campo in datos:
                valor = datos[campo]
                if campo == "fecha_nacimiento" and valor is not None:
                    valor = str(valor)
                campos.append(f"{campo} = ?")
                valores.append(valor)

        if not campos:
            return False

        valores.append(persona_id)
        query = f"UPDATE personas SET {\\', \\'.join(campos)} WHERE id = ? AND activo = 1"

        with get_transaction() as conn:
            cursor = conn.execute(query, valores)
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(persona_id: int) -> bool:
        """Elimina lógicamente una persona (soft-delete)."""
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE personas SET activo = 0 WHERE id = ? AND activo = 1",
                (persona_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def buscar_rapida(
        termino: str,
        campo: Optional[str] = None,
        limite: int = PAGINATION_SIZE,
    ) -> list[dict]:
        """Búsqueda rápida en uno o varios campos."""
        if not termino or not termino.strip():
            return []

        termino_like = f"%{termino.strip()}%"
        with get_connection() as conn:
            if campo and campo in ("dni", "pasaporte", "apellido", "nombre", "nacionalidad"):
                query = f"SELECT * FROM personas WHERE activo = 1 AND {campo} LIKE ? ORDER BY apellido LIMIT ?"
                cursor = conn.execute(query, (termino_like, limite))
            else:
                cursor = conn.execute(
                    "SELECT * FROM personas WHERE activo = 1 AND ("
                    "dni LIKE ? OR pasaporte LIKE ? OR apellido LIKE ? OR nombre LIKE ?"
                    ") ORDER BY apellido LIMIT ?",
                    (termino_like, termino_like, termino_like, termino_like, limite),
                )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def contar_total(solo_activos: bool = True) -> int:
        """Cuenta el total de personas."""
        with get_connection() as conn:
            query = "SELECT COUNT(*) as total FROM personas"
            if solo_activos:
                query += " WHERE activo = 1"
            cursor = conn.execute(query)
            return cursor.fetchone()["total"]

    @staticmethod
    def listar(pagina: int = 1, por_pagina: int = PAGINATION_SIZE) -> tuple[list[dict], int]:
        """Lista personas con paginación."""
        with get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as total FROM personas WHERE activo = 1")
            total = cursor.fetchone()["total"]
            offset = (pagina - 1) * por_pagina
            cursor = conn.execute(
                "SELECT * FROM personas WHERE activo = 1 ORDER BY apellido, nombre LIMIT ? OFFSET ?",
                (por_pagina, offset),
            )
            return [dict(row) for row in cursor.fetchall()], total
'''

# ============================================================
# models/estadia.py
# ============================================================
FILES["models/estadia.py"] = '''\
"""Modelo y DAO de Estadía para S.C.A.H. v2.

Cada estadía representa una visita/check-in de una persona en un establecimiento.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from config.database import get_connection, get_transaction
from config.settings import PAGINATION_SIZE
from utils.logger import get_logger

logger = get_logger("models.estadia")


class EstadiaSchema(BaseModel):
    """Esquema de validación para datos de estadía."""

    persona_id: int
    establecimiento: Optional[str] = Field(default=None, max_length=150)
    habitacion: Optional[str] = Field(default="S/N", max_length=20)
    edad: Optional[int] = Field(default=None, gt=0, lt=150)
    fecha_entrada: date
    fecha_salida: Optional[date] = None
    destino: Optional[str] = Field(default=None, max_length=200)
    vehiculo_tiene: bool = Field(default=False)
    vehiculo_datos: Optional[str] = Field(default=None, max_length=200)
    usuario_carga: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validar_fechas(self) -> "EstadiaSchema":
        if self.fecha_salida and self.fecha_salida < self.fecha_entrada:
            raise ValueError("La fecha de salida no puede ser anterior a la de entrada")
        return self


class EstadiaDAO:
    """Operaciones de base de datos para la tabla \'estadias\'."""

    @staticmethod
    def crear(datos: dict) -> int:
        """Crea un nuevo registro de estadía."""
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO estadias "
                "(persona_id, establecimiento, habitacion, edad, fecha_entrada, "
                "fecha_salida, destino, vehiculo_tiene, vehiculo_datos, usuario_carga) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datos["persona_id"],
                    datos.get("establecimiento"),
                    datos.get("habitacion", "S/N"),
                    datos.get("edad"),
                    str(datos["fecha_entrada"]),
                    str(datos["fecha_salida"]) if datos.get("fecha_salida") else None,
                    datos.get("destino"),
                    1 if datos.get("vehiculo_tiene") else 0,
                    datos.get("vehiculo_datos"),
                    datos["usuario_carga"],
                ),
            )
            estadia_id = cursor.lastrowid
            logger.info("Estadía creada ID %d para persona %d", estadia_id, datos["persona_id"])
            return estadia_id

    @staticmethod
    def obtener_por_id(estadia_id: int) -> Optional[dict]:
        """Obtiene una estadía por su ID."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT e.*, p.apellido, p.nombre, p.dni, p.pasaporte, p.nacionalidad, "
                "p.procedencia, p.fecha_nacimiento, p.profesion, p.telefono "
                "FROM estadias e "
                "JOIN personas p ON e.persona_id = p.id "
                "WHERE e.id = ? AND e.activo = 1",
                (estadia_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def obtener_por_persona(persona_id: int) -> list[dict]:
        """Obtiene todas las estadías de una persona (historial)."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM estadias WHERE persona_id = ? AND activo = 1 "
                "ORDER BY fecha_entrada DESC",
                (persona_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def actualizar(estadia_id: int, datos: dict) -> bool:
        """Actualiza una estadía existente."""
        campos_permitidos = [
            "establecimiento", "habitacion", "edad", "fecha_entrada",
            "fecha_salida", "destino", "vehiculo_tiene", "vehiculo_datos",
        ]
        campos: list[str] = []
        valores: list = []

        for campo in campos_permitidos:
            if campo in datos:
                valor = datos[campo]
                if campo == "vehiculo_tiene":
                    valor = 1 if valor else 0
                elif campo in ("fecha_entrada", "fecha_salida") and valor is not None:
                    valor = str(valor)
                campos.append(f"{campo} = ?")
                valores.append(valor)

        if not campos:
            return False

        valores.append(estadia_id)
        query = f"UPDATE estadias SET {\\', \\'.join(campos)} WHERE id = ? AND activo = 1"

        with get_transaction() as conn:
            cursor = conn.execute(query, valores)
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(estadia_id: int) -> bool:
        """Elimina lógicamente una estadía (soft-delete)."""
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE estadias SET activo = 0 WHERE id = ? AND activo = 1",
                (estadia_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def buscar_completa(
        termino: str = "",
        campo: str | None = None,
        filtros: dict | None = None,
        operador: str = "AND",
        pagina: int = 1,
        por_pagina: int = PAGINATION_SIZE,
    ) -> tuple[list[dict], int]:
        """Búsqueda completa uniendo personas y estadías."""
        base = (
            "FROM estadias e "
            "JOIN personas p ON e.persona_id = p.id "
            "WHERE e.activo = 1 AND p.activo = 1"
        )
        conditions: list[str] = []
        params: list = []

        # Búsqueda rápida por término
        if termino and termino.strip():
            t = f"%{termino.strip()}%"
            if campo and campo in ("dni", "pasaporte", "apellido", "nombre", "nacionalidad", "establecimiento"):
                if campo in ("dni", "pasaporte", "apellido", "nombre", "nacionalidad"):
                    conditions.append(f"p.{campo} LIKE ?")
                else:
                    conditions.append(f"e.{campo} LIKE ?")
                params.append(t)
            else:
                conditions.append(
                    "(p.dni LIKE ? OR p.pasaporte LIKE ? OR p.apellido LIKE ? OR p.nombre LIKE ? OR e.establecimiento LIKE ?)"
                )
                params.extend([t, t, t, t, t])

        # Filtros avanzados
        if filtros:
            if filtros.get("fecha_desde"):
                conditions.append("e.fecha_entrada >= ?")
                params.append(str(filtros["fecha_desde"]))
            if filtros.get("fecha_hasta"):
                conditions.append("e.fecha_entrada <= ?")
                params.append(str(filtros["fecha_hasta"]))
            if filtros.get("nacionalidad"):
                conditions.append("p.nacionalidad = ?")
                params.append(filtros["nacionalidad"])
            if filtros.get("procedencia"):
                conditions.append("p.procedencia LIKE ?")
                params.append(f"%{filtros[\'procedencia\']}%")
            if filtros.get("establecimiento"):
                conditions.append("e.establecimiento LIKE ?")
                params.append(f"%{filtros[\'establecimiento\']}%")
            if filtros.get("apellido"):
                conditions.append("p.apellido LIKE ?")
                params.append(f"%{filtros[\'apellido\']}%")
            if filtros.get("nombre"):
                conditions.append("p.nombre LIKE ?")
                params.append(f"%{filtros[\'nombre\']}%")
            if filtros.get("edad_min"):
                conditions.append("e.edad >= ?")
                params.append(int(filtros["edad_min"]))
            if filtros.get("edad_max"):
                conditions.append("e.edad <= ?")
                params.append(int(filtros["edad_max"]))

        if conditions:
            joiner = f" {operador} "
            base += f" AND ({joiner.join(conditions)})"

        with get_connection() as conn:
            count_query = f"SELECT COUNT(*) as total {base}"
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()["total"]

            offset = (pagina - 1) * por_pagina
            data_query = (
                f"SELECT e.*, p.apellido, p.nombre, p.dni, p.pasaporte, "
                f"p.nacionalidad, p.procedencia, p.fecha_nacimiento, p.profesion, p.telefono "
                f"{base} ORDER BY e.fecha_entrada DESC LIMIT ? OFFSET ?"
            )
            cursor = conn.execute(data_query, params + [por_pagina, offset])
            return [dict(row) for row in cursor.fetchall()], total

    @staticmethod
    def contar_total(solo_activos: bool = True) -> int:
        """Cuenta el total de estadías."""
        with get_connection() as conn:
            query = "SELECT COUNT(*) as total FROM estadias"
            if solo_activos:
                query += " WHERE activo = 1"
            cursor = conn.execute(query)
            return cursor.fetchone()["total"]

    @staticmethod
    def contar_activas_hoy() -> int:
        """Cuenta huéspedes hospedados hoy (con check-in y sin check-out)."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as total FROM estadias "
                "WHERE activo = 1 AND fecha_entrada <= date(\'now\') "
                "AND (fecha_salida IS NULL OR fecha_salida >= date(\'now\'))"
            )
            return cursor.fetchone()["total"]

    @staticmethod
    def estadisticas_nacionalidades(limite: int = 10) -> list[dict]:
        """Top nacionalidades de huéspedes."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT p.nacionalidad, COUNT(*) as cantidad "
                "FROM estadias e JOIN personas p ON e.persona_id = p.id "
                "WHERE e.activo = 1 "
                "GROUP BY p.nacionalidad ORDER BY cantidad DESC LIMIT ?",
                (limite,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def estadisticas_establecimientos(limite: int = 10) -> list[dict]:
        """Top establecimientos por cantidad de estadías."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT establecimiento, COUNT(*) as cantidad "
                "FROM estadias WHERE activo = 1 AND establecimiento IS NOT NULL "
                "GROUP BY establecimiento ORDER BY cantidad DESC LIMIT ?",
                (limite,),
            )
            return [dict(row) for row in cursor.fetchall()]
'''

# ============================================================
# models/establecimiento.py
# ============================================================
FILES["models/establecimiento.py"] = '''\
"""Modelo y DAO de Establecimiento para S.C.A.H. v2."""

from typing import Optional
from pydantic import BaseModel, Field

from config.database import get_connection, get_transaction
from utils.logger import get_logger

logger = get_logger("models.establecimiento")


class EstablecimientoSchema(BaseModel):
    """Esquema de validación para datos de establecimiento."""
    nombre: str = Field(..., min_length=2, max_length=150)
    direccion: Optional[str] = Field(default=None, max_length=300)
    telefono: Optional[str] = Field(default=None, max_length=30)


class EstablecimientoDAO:
    """Operaciones de base de datos para la tabla \'establecimientos\'."""

    @staticmethod
    def crear(datos: dict) -> int:
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO establecimientos (nombre, direccion, telefono) VALUES (?, ?, ?)",
                (datos["nombre"], datos.get("direccion"), datos.get("telefono")),
            )
            est_id = cursor.lastrowid
            logger.info("Establecimiento creado ID %d: %s", est_id, datos["nombre"])
            return est_id

    @staticmethod
    def obtener_por_id(est_id: int) -> Optional[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM establecimientos WHERE id = ? AND activo = 1", (est_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def obtener_por_nombre(nombre: str) -> Optional[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM establecimientos WHERE nombre = ? COLLATE NOCASE AND activo = 1",
                (nombre.strip(),),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def obtener_o_crear(nombre: str) -> int:
        """Obtiene el ID de un establecimiento por nombre, o lo crea si no existe."""
        existente = EstablecimientoDAO.obtener_por_nombre(nombre)
        if existente:
            return existente["id"]
        return EstablecimientoDAO.crear({"nombre": nombre.strip()})

    @staticmethod
    def listar(incluir_inactivos: bool = False) -> list[dict]:
        with get_connection() as conn:
            query = "SELECT * FROM establecimientos"
            if not incluir_inactivos:
                query += " WHERE activo = 1"
            query += " ORDER BY nombre"
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def actualizar(est_id: int, datos: dict) -> bool:
        campos: list[str] = []
        valores: list = []
        for campo in ("nombre", "direccion", "telefono"):
            if campo in datos:
                campos.append(f"{campo} = ?")
                valores.append(datos[campo])
        if not campos:
            return False
        valores.append(est_id)
        with get_transaction() as conn:
            cursor = conn.execute(
                f"UPDATE establecimientos SET {\\', \\'.join(campos)} WHERE id = ? AND activo = 1",
                valores,
            )
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(est_id: int) -> bool:
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE establecimientos SET activo = 0 WHERE id = ? AND activo = 1",
                (est_id,),
            )
            return cursor.rowcount > 0
'''

# ============================================================
# models/habitacion.py
# ============================================================
FILES["models/habitacion.py"] = '''\
"""Modelo y DAO de Habitación para S.C.A.H. v2."""

from typing import Optional
from pydantic import BaseModel, Field

from config.database import get_connection, get_transaction
from utils.logger import get_logger

logger = get_logger("models.habitacion")


class HabitacionSchema(BaseModel):
    """Esquema de validación para datos de habitación."""
    establecimiento_id: int
    numero: str = Field(..., min_length=1, max_length=20)
    tipo: str = Field(default="standard", max_length=50)
    capacidad: int = Field(default=2, gt=0, le=20)
    estado: str = Field(default="disponible")


class HabitacionDAO:
    """Operaciones de base de datos para la tabla \'habitaciones\'."""

    @staticmethod
    def crear(datos: dict) -> int:
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO habitaciones "
                "(establecimiento_id, numero, tipo, capacidad, estado) "
                "VALUES (?, ?, ?, ?, ?)",
                (datos["establecimiento_id"], datos["numero"],
                 datos.get("tipo", "standard"), datos.get("capacidad", 2),
                 datos.get("estado", "disponible")),
            )
            hab_id = cursor.lastrowid
            logger.info("Habitación creada ID %d: %s", hab_id, datos["numero"])
            return hab_id

    @staticmethod
    def obtener_por_id(hab_id: int) -> Optional[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT h.*, e.nombre as establecimiento_nombre "
                "FROM habitaciones h JOIN establecimientos e ON h.establecimiento_id = e.id "
                "WHERE h.id = ? AND h.activo = 1",
                (hab_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def listar_por_establecimiento(est_id: int) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM habitaciones "
                "WHERE establecimiento_id = ? AND activo = 1 ORDER BY numero",
                (est_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def actualizar_estado(hab_id: int, estado: str) -> bool:
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE habitaciones SET estado = ? WHERE id = ? AND activo = 1",
                (estado, hab_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def actualizar(hab_id: int, datos: dict) -> bool:
        campos: list[str] = []
        valores: list = []
        for campo in ("numero", "tipo", "capacidad", "estado"):
            if campo in datos:
                campos.append(f"{campo} = ?")
                valores.append(datos[campo])
        if not campos:
            return False
        valores.append(hab_id)
        with get_transaction() as conn:
            cursor = conn.execute(
                f"UPDATE habitaciones SET {\\', \\'.join(campos)} WHERE id = ? AND activo = 1",
                valores,
            )
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(hab_id: int) -> bool:
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE habitaciones SET activo = 0 WHERE id = ? AND activo = 1",
                (hab_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def contar_por_estado(est_id: int) -> dict[str, int]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT estado, COUNT(*) as cantidad FROM habitaciones "
                "WHERE establecimiento_id = ? AND activo = 1 GROUP BY estado",
                (est_id,),
            )
            return {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
'''

# ============================================================
# models/usuario.py
# ============================================================
FILES["models/usuario.py"] = '''\
"""Modelo y DAO de Usuario para S.C.A.H. v2."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from config.database import get_connection, get_transaction
from config.settings import ROLES_USUARIO
from utils.logger import get_logger

logger = get_logger("models.usuario")


class UsuarioSchema(BaseModel):
    """Esquema de validación para datos de usuario."""
    username: str = Field(..., min_length=3, max_length=50)
    password_hash: str = Field(..., min_length=1)
    nombre_completo: str = Field(..., min_length=2, max_length=200)
    rol: str = Field(default="operador")
    activo: bool = Field(default=True)

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, v: str) -> str:
        if v not in ROLES_USUARIO:
            raise ValueError(f"Rol inválido. Permitidos: {\\', \\'.join(ROLES_USUARIO)}")
        return v

    @field_validator("username")
    @classmethod
    def validar_username(cls, v: str) -> str:
        return v.strip().lower()


class UsuarioDAO:
    """Operaciones de base de datos para la tabla \'usuarios\'."""

    @staticmethod
    def crear(username: str, password_hash: str, nombre_completo: str, rol: str = "operador") -> int:
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (username, password_hash, nombre_completo, rol) "
                "VALUES (?, ?, ?, ?)",
                (username.strip().lower(), password_hash, nombre_completo.strip(), rol),
            )
            user_id = cursor.lastrowid
            logger.info("Usuario creado: %s (ID: %s, Rol: %s)", username, user_id, rol)
            return user_id

    @staticmethod
    def obtener_por_username(username: str) -> Optional[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM usuarios WHERE username = ?",
                (username.strip().lower(),),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def obtener_por_id(user_id: int) -> Optional[dict]:
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def actualizar_ultimo_acceso(username: str) -> None:
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE username = ?",
                (username.strip().lower(),),
            )

    @staticmethod
    def incrementar_intentos_fallidos(username: str) -> int:
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET intentos_fallidos = intentos_fallidos + 1 WHERE username = ?",
                (username.strip().lower(),),
            )
            cursor = conn.execute(
                "SELECT intentos_fallidos FROM usuarios WHERE username = ?",
                (username.strip().lower(),),
            )
            row = cursor.fetchone()
            return row["intentos_fallidos"] if row else 0

    @staticmethod
    def bloquear_cuenta(username: str, hasta: datetime) -> None:
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET bloqueado_hasta = ? WHERE username = ?",
                (hasta.strftime("%Y-%m-%d %H:%M:%S"), username.strip().lower()),
            )

    @staticmethod
    def resetear_intentos(username: str) -> None:
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE username = ?",
                (username.strip().lower(),),
            )

    @staticmethod
    def listar_todos(incluir_inactivos: bool = False) -> list[dict]:
        with get_connection() as conn:
            query = (
                "SELECT id, username, nombre_completo, rol, activo, "
                "ultimo_acceso, fecha_creacion FROM usuarios"
            )
            if not incluir_inactivos:
                query += " WHERE activo = 1"
            query += " ORDER BY nombre_completo"
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def existe_username(username: str) -> bool:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM usuarios WHERE username = ?",
                (username.strip().lower(),),
            )
            return cursor.fetchone()["count"] > 0

    @staticmethod
    def actualizar(
        user_id: int,
        nombre_completo: str | None = None,
        rol: str | None = None,
        activo: bool | None = None,
        password_hash: str | None = None,
    ) -> bool:
        campos: list[str] = []
        valores: list = []
        if nombre_completo is not None:
            campos.append("nombre_completo = ?")
            valores.append(nombre_completo.strip())
        if rol is not None:
            campos.append("rol = ?")
            valores.append(rol)
        if activo is not None:
            campos.append("activo = ?")
            valores.append(1 if activo else 0)
        if password_hash is not None:
            campos.append("password_hash = ?")
            valores.append(password_hash)
        if not campos:
            return False
        valores.append(user_id)
        with get_transaction() as conn:
            cursor = conn.execute(
                f"UPDATE usuarios SET {\\', \\'.join(campos)} WHERE id = ?", valores
            )
            return cursor.rowcount > 0
'''

# ============================================================
# models/auditoria.py
# ============================================================
FILES["models/auditoria.py"] = '''\
"""Modelo y DAO de Auditoría para S.C.A.H. v2."""

import json
from typing import Optional

from config.database import get_connection, get_transaction
from utils.logger import get_logger

logger = get_logger("models.auditoria")


class AuditoriaDAO:
    """Operaciones de base de datos para la tabla \'auditoria\'."""

    @staticmethod
    def registrar(
        usuario: str,
        accion: str,
        tabla_afectada: Optional[str] = None,
        registro_id: Optional[int] = None,
        datos_anteriores: Optional[dict] = None,
        datos_nuevos: Optional[dict] = None,
        detalles: Optional[str] = None,
    ) -> int:
        datos_ant_json = (
            json.dumps(datos_anteriores, ensure_ascii=False, default=str)
            if datos_anteriores else None
        )
        datos_new_json = (
            json.dumps(datos_nuevos, ensure_ascii=False, default=str)
            if datos_nuevos else None
        )
        try:
            with get_transaction() as conn:
                cursor = conn.execute(
                    "INSERT INTO auditoria "
                    "(usuario, accion, tabla_afectada, registro_id, "
                    "datos_anteriores, datos_nuevos, detalles) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (usuario, accion, tabla_afectada, registro_id,
                     datos_ant_json, datos_new_json, detalles),
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error("Error al registrar auditoría: %s", e)
            return -1

    @staticmethod
    def buscar(
        usuario: Optional[str] = None,
        accion: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        limite: int = 100,
    ) -> list[dict]:
        query = "SELECT * FROM auditoria WHERE 1=1"
        params: list = []
        if usuario:
            query += " AND usuario = ?"
            params.append(usuario)
        if accion:
            query += " AND accion = ?"
            params.append(accion)
        if fecha_desde:
            query += " AND fecha >= ?"
            params.append(fecha_desde)
        if fecha_hasta:
            query += " AND fecha <= ?"
            params.append(fecha_hasta + " 23:59:59")
        query += " ORDER BY fecha DESC LIMIT ?"
        params.append(limite)
        with get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
'''

# ============================================================
# models/huesped.py  (mantener como wrapper de compatibilidad)
# ============================================================
FILES["models/huesped.py"] = '''\
"""Modelo de compatibilidad: wrapper sobre persona + estadia para S.C.A.H. v2.

Mantiene la interfaz HuespedDAO para código que aún la use,
pero delega a PersonaDAO + EstadiaDAO internamente.
"""

from typing import Optional

from config.database import get_connection
from config.settings import PAGINATION_SIZE
from utils.logger import get_logger

logger = get_logger("models.huesped")


class HuespedDAO:
    """Wrapper de compatibilidad para consultas que unan personas + estadias."""

    @staticmethod
    def buscar_rapida(
        termino: str,
        campo: Optional[str] = None,
        limite: int = PAGINATION_SIZE,
    ) -> list[dict]:
        """Búsqueda rápida uniendo personas y estadías."""
        if not termino or not termino.strip():
            return []
        termino_like = f"%{termino.strip()}%"
        with get_connection() as conn:
            if campo and campo in ("dni", "pasaporte", "apellido", "nombre", "nacionalidad"):
                query = (
                    f"SELECT e.*, p.apellido, p.nombre, p.dni, p.pasaporte, "
                    f"p.nacionalidad, p.procedencia, p.fecha_nacimiento, p.profesion, p.telefono "
                    f"FROM estadias e JOIN personas p ON e.persona_id = p.id "
                    f"WHERE e.activo = 1 AND p.activo = 1 AND p.{campo} LIKE ? "
                    f"ORDER BY e.fecha_entrada DESC LIMIT ?"
                )
                cursor = conn.execute(query, (termino_like, limite))
            else:
                cursor = conn.execute(
                    "SELECT e.*, p.apellido, p.nombre, p.dni, p.pasaporte, "
                    "p.nacionalidad, p.procedencia, p.fecha_nacimiento, p.profesion, p.telefono "
                    "FROM estadias e JOIN personas p ON e.persona_id = p.id "
                    "WHERE e.activo = 1 AND p.activo = 1 AND ("
                    "p.dni LIKE ? OR p.pasaporte LIKE ? OR p.apellido LIKE ? OR p.nombre LIKE ?"
                    ") ORDER BY e.fecha_entrada DESC LIMIT ?",
                    (termino_like, termino_like, termino_like, termino_like, limite),
                )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def contar_total(solo_activos: bool = True) -> int:
        with get_connection() as conn:
            query = "SELECT COUNT(*) as total FROM estadias"
            if solo_activos:
                query += " WHERE activo = 1"
            cursor = conn.execute(query)
            return cursor.fetchone()["total"]
'''

# ============================================================
# WRITE ALL FILES
# ============================================================
def write_all():
    written = 0
    for rel_path, content in FILES.items():
        full_path = os.path.join(BASE, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        written += 1
        print(f"  [OK] {rel_path}")
    print(f"\n  Total: {written} archivos escritos")


if __name__ == "__main__":
    print("=" * 60)
    print("S.C.A.H. v2 - Reconstrucción: Fase 1-3")
    print("Config + Utils + Models")
    print("=" * 60)
    write_all()
    print("\nFase 1-3 completada.")
