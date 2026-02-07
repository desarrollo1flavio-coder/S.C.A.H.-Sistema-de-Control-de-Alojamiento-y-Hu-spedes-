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
    "nacionalidad": ["nacionalidad", "pais", "país", "country", "nation", "nacion", "nación"],
    "procedencia": ["procedencia", "origen", "ciudad_origen", "from", "domicilio",
                     "direccion", "dirección", "ciudad"],
    "apellido": ["apellido", "apellidos", "last_name", "surname",
                  "apellido_y_nombre", "apellido/nombre", "apellido_nombre"],
    "nombre": ["nombre", "nombres", "first_name", "name"],
    "dni": ["dni", "documento", "doc", "nro_documento", "document",
            "d.n.i", "d.n.i.", "n°_doc", "nro_doc", "n_doc",
            "n°_documento", "nº_doc", "nº_documento",
            "numero_documento", "número_documento", "numero_doc",
            "n°doc", "n°_de_doc", "nro._doc", "nro._documento",
            "dni/pasaporte", "dni_/_pasaporte", "dni_o_pasaporte", "doc."],
    "pasaporte": ["pasaporte", "passport", "nro_pasaporte",
                   "n°_pasaporte", "nº_pasaporte"],
    "edad": ["edad", "age", "años", "edades"],
    "profesion": ["profesion", "profesión", "ocupacion", "ocupación",
                  "profession", "occupation", "prof", "prof."],
    "habitacion": ["habitacion", "habitación", "hab", "hab.", "room",
                   "nro_habitacion", "nro_habitación", "cuarto",
                   "n°_hab", "n°_hab.", "nº_hab", "nro._hab",
                   "n°_habitacion", "n°_habitación"],
    "destino": ["destino", "destination", "hacia", "a_donde", "destino_a"],
    "vehiculo": ["vehiculo", "vehículo", "vehicle", "auto", "coche",
                 "vehic", "vehic.", "patente", "dominio",
                 "datos_vehiculo", "datos_vehículo"],
    "telefono": ["telefono", "teléfono", "tel", "tel.", "phone",
                 "celular", "mobile", "nro_telefono", "nro_teléfono",
                 "n°_tel", "n°_tel.", "nº_tel", "contacto"],
    "fecha_entrada": ["fecha_entrada", "ingreso", "check_in", "entrada",
                      "checkin", "fecha_ingreso", "f._entrada", "f._ingreso",
                      "fecha_de_entrada", "fecha_de_ingreso",
                      "fec._entrada", "fec._ingreso",
                      "f.entrada", "f.ingreso", "fec.entrada", "fec.ingreso"],
    "fecha_salida": ["fecha_salida", "egreso", "check_out", "salida",
                     "checkout", "fecha_egreso", "f._salida", "f._egreso",
                     "fecha_de_salida", "fecha_de_egreso",
                     "fec._salida", "fec._egreso",
                     "f.salida", "f.egreso", "fec.salida", "fec.egreso"],
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
