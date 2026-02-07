"""Configuración global del sistema S.C.A.H.

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

# Crear directorios si no existen
for _dir in [DATABASE_DIR, MIGRATIONS_DIR, LOGS_DIR, ASSETS_DIR, ICONS_DIR, THEMES_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ============================================================
# BASE DE DATOS
# ============================================================
DATABASE_PATH: Path = DATABASE_DIR / "scah.db"
DATABASE_BACKUP_DIR: Path = DATABASE_DIR / "backups"
DATABASE_TIMEOUT: int = 30  # segundos
DATABASE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# SEGURIDAD
# ============================================================
BCRYPT_WORK_FACTOR: int = 12
MAX_LOGIN_ATTEMPTS: int = 3
LOCKOUT_DURATION_MINUTES: int = 15
SESSION_TIMEOUT_MINUTES: int = 480  # 8 horas

# ============================================================
# CONTRASEÑA POR DEFECTO DEL ADMIN INICIAL
# ============================================================
DEFAULT_ADMIN_USERNAME: str = "admin"
DEFAULT_ADMIN_PASSWORD: str = "Admin2026!"  # Cambiar en primer inicio
DEFAULT_ADMIN_FULLNAME: str = "Administrador del Sistema"

# ============================================================
# UI - INTERFAZ DE USUARIO
# ============================================================
APP_TITLE: str = "S.C.A.H. - Sistema de Control de Alojamiento y Huéspedes"
APP_VERSION: str = "1.0.0"
APP_ORGANIZATION: str = "Departamento de Inteligencia Criminal - Policía de Tucumán"
APP_SUBTITLE: str = "Sección Hoteles"

LOGIN_WINDOW_SIZE: str = "450x550"
LOGIN_WINDOW_RESIZABLE: bool = False

DEFAULT_APPEARANCE_MODE: str = "dark"  # "dark", "light", "system"
DEFAULT_COLOR_THEME: str = "blue"  # "blue", "green", "dark-blue"

DEBOUNCE_MS: int = 300  # milisegundos para búsqueda
PAGINATION_SIZE: int = 50  # registros por página

# ============================================================
# IMPORTACIÓN DE ARCHIVOS
# ============================================================
ALLOWED_EXTENSIONS: list[str] = [".xlsx", ".xls"]
MAX_IMPORT_ROWS: int = 10000
PREVIEW_ROWS: int = 10

COLUMNAS_MAPEO: dict[str, list[str]] = {
    "nacionalidad": ["nacionalidad", "pais", "country", "nation"],
    "procedencia": ["procedencia", "origen", "ciudad_origen", "from"],
    "apellido": ["apellido", "apellidos", "last_name", "surname"],
    "nombre": ["nombre", "nombres", "first_name", "name"],
    "dni": ["dni", "documento", "doc", "nro_documento", "document"],
    "pasaporte": ["pasaporte", "passport", "nro_pasaporte"],
    "edad": ["edad", "age", "años"],
    "profesion": ["profesion", "ocupacion", "profession", "occupation"],
    "habitacion": ["habitacion", "hab", "room", "nro_habitacion", "cuarto"],
    "destino": ["destino", "destination", "hacia"],
    "vehiculo": ["vehiculo", "vehicle", "auto", "coche", "vehículo"],
    "telefono": ["telefono", "tel", "phone", "celular", "mobile", "teléfono"],
    "fecha_entrada": ["fecha_entrada", "ingreso", "check_in", "entrada", "checkin"],
    "fecha_salida": ["fecha_salida", "egreso", "check_out", "salida", "checkout"],
}

# ============================================================
# LOGGING
# ============================================================
LOG_FILE: Path = LOGS_DIR / "scah.log"
LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB
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
