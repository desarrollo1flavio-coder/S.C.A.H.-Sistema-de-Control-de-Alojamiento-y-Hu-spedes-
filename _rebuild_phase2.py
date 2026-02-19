"""Script de reconstrucción S.C.A.H. v2 - Fase 2.

Excel Parser + Controllers
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = {}

# ============================================================
# utils/excel_parser.py  — REESCRITURA COMPLETA
# ============================================================
FILES["utils/excel_parser.py"] = '''"""Parser de archivos Excel para S.C.A.H. v2.

Lee archivos .xlsx/.xls, detecta columnas automáticamente mediante
fuzzy matching contra COLUMNAS_MAPEO, y retorna datos normalizados
listos para inserción en persona + estadia.
"""

import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from config.settings import (
    ALLOWED_EXTENSIONS,
    COLUMNAS_IGNORAR,
    COLUMNAS_MAPEO,
    MAX_IMPORT_ROWS,
    PREVIEW_ROWS,
)
from utils.logger import get_logger
from utils.validators import limpiar_dni, sanitizar_texto

logger = get_logger("excel_parser")


# ============================================================
# Normalización de texto para matching de columnas
# ============================================================
def _normalize(text: str) -> str:
    """Normaliza texto: quita acentos, convierte a minúsculas, reemplaza
    caracteres especiales por underscore."""
    if not text:
        return ""
    # Descomponer caracteres Unicode y eliminar marcas diacríticas
    nfkd = unicodedata.normalize("NFKD", str(text))
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    # Limpio: minúsculas, reemplazar no-alfanuméricos por _
    clean = re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")
    return clean


def _is_ignorable(col_normalized: str) -> bool:
    """Retorna True si la columna normalizada es un campo ignorable (N°, Nro, #, etc)."""
    for patron in COLUMNAS_IGNORAR:
        if _normalize(patron) == col_normalized:
            return True
    # Si es solo dígitos o vacío, ignorar
    if not col_normalized or col_normalized.isdigit():
        return True
    return False


def _map_column(col_name: str) -> Optional[str]:
    """Intenta mapear un nombre de columna del Excel a un campo interno.

    Retorna el nombre del campo interno (ej: 'nacionalidad', 'fecha_entrada')
    o None si no se encontró coincidencia.
    """
    normalized = _normalize(col_name)
    if not normalized or _is_ignorable(normalized):
        return None

    # Buscar coincidencia exacta primero
    for field, aliases in COLUMNAS_MAPEO.items():
        for alias in aliases:
            if _normalize(alias) == normalized:
                return field

    # Buscar coincidencia parcial (el nombre del Excel contiene el alias o viceversa)
    for field, aliases in COLUMNAS_MAPEO.items():
        for alias in aliases:
            alias_norm = _normalize(alias)
            if alias_norm in normalized or normalized in alias_norm:
                return field

    logger.warning("Columna no mapeada: '%s' (normalizada: '%s')", col_name, normalized)
    return None


# ============================================================
# Lectura del archivo Excel
# ============================================================
def leer_archivo(filepath: str | Path) -> pd.DataFrame:
    """Lee un archivo Excel y retorna un DataFrame limpio."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

    suffix = filepath.suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extensión no soportada: {suffix}. Use {ALLOWED_EXTENSIONS}")

    try:
        if suffix == ".xlsx":
            df = pd.read_excel(filepath, engine="openpyxl")
        else:
            df = pd.read_excel(filepath, engine="xlrd")
    except Exception as e:
        logger.error("Error al leer archivo Excel: %s", e)
        raise ValueError(f"No se pudo leer el archivo Excel: {e}") from e

    if df.empty:
        raise ValueError("El archivo Excel está vacío")

    if len(df) > MAX_IMPORT_ROWS:
        raise ValueError(f"El archivo excede el máximo de {MAX_IMPORT_ROWS} filas")

    # Eliminar filas completamente vacías
    df = df.dropna(how="all").reset_index(drop=True)
    # Eliminar columnas sin nombre (Unnamed)
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]

    return df


# ============================================================
# Mapeo automático de columnas
# ============================================================
def detectar_mapeo(df: pd.DataFrame) -> dict[str, str]:
    """Detecta el mapeo entre columnas del Excel y campos internos.

    Retorna dict {nombre_columna_excel: campo_interno}.
    """
    mapeo: dict[str, str] = {}
    campos_usados: set[str] = set()

    for col in df.columns:
        col_str = str(col).strip()
        campo = _map_column(col_str)
        if campo and campo not in campos_usados:
            mapeo[col_str] = campo
            campos_usados.add(campo)
            logger.debug("Columna mapeada: '%s' -> '%s'", col_str, campo)

    logger.info("Mapeo detectado: %d columnas de %d", len(mapeo), len(df.columns))
    return mapeo


def obtener_columnas_faltantes(mapeo: dict[str, str]) -> list[str]:
    """Retorna campos obligatorios que no fueron mapeados."""
    campos_obligatorios = {"apellido_nombre", "dni", "fecha_entrada"}
    # Si hay apellido_nombre, no necesitamos apellido y nombre separados
    # Si hay apellido Y nombre separados, no necesitamos apellido_nombre
    campos_mapeados = set(mapeo.values())

    tiene_nombre_completo = "apellido_nombre" in campos_mapeados
    tiene_nombre_separado = "apellido" in campos_mapeados and "nombre" in campos_mapeados

    faltantes: list[str] = []
    if not tiene_nombre_completo and not tiene_nombre_separado:
        faltantes.append("apellido_nombre (o apellido + nombre separados)")
    if "dni" not in campos_mapeados and "pasaporte" not in campos_mapeados:
        faltantes.append("dni o pasaporte")
    if "fecha_entrada" not in campos_mapeados:
        faltantes.append("fecha_entrada (entrada)")

    return faltantes


# ============================================================
# Parseo de valores individuales
# ============================================================
def _parse_date(valor: Any) -> Optional[date]:
    """Intenta parsear un valor a fecha. Soporta múltiples formatos."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if isinstance(valor, (datetime, date)):
        return valor if isinstance(valor, date) else valor.date()
    if isinstance(valor, pd.Timestamp):
        return valor.date()

    texto = str(valor).strip()
    if not texto or texto.lower() in ("nat", "nan", "none", ""):
        return None

    # Formatos comunes en Argentina
    formatos = [
        "%d/%m/%Y",       # 25/12/2024
        "%d-%m-%Y",       # 25-12-2024
        "%Y-%m-%d",       # 2024-12-25
        "%d/%m/%y",       # 25/12/24
        "%d-%m-%y",       # 25-12-24
        "%d.%m.%Y",       # 25.12.2024
        "%d.%m.%y",       # 25.12.24
        "%Y/%m/%d",       # 2024/12/25
        "%m/%d/%Y",       # 12/25/2024 (formato USA)
    ]
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue

    logger.warning("No se pudo parsear fecha: '%s'", texto)
    return None


def _parse_edad(valor: Any) -> Optional[int]:
    """Parsea un valor a edad (entero)."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    try:
        edad = int(float(str(valor)))
        return edad if 0 < edad < 150 else None
    except (ValueError, TypeError):
        return None


def _parse_documento(valor: Any) -> tuple[Optional[str], Optional[str]]:
    """Parsea un valor de documento y determina si es DNI o Pasaporte.

    Retorna (dni, pasaporte). Uno de los dos será None.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None, None

    texto = str(valor).strip()
    if not texto or texto.lower() in ("nan", "none", ""):
        return None, None

    # Limpiar el texto
    limpio = texto.replace(".", "").replace("-", "").replace(" ", "")

    # Si termina en .0 (vino de float), removerlo
    if limpio.endswith(".0"):
        limpio = limpio[:-2]

    # Si es solo dígitos y tiene 7-8 caracteres -> DNI
    if limpio.isdigit() and 7 <= len(limpio) <= 8:
        return limpio, None

    # Si es alfanumérico y tiene 5-15 caracteres -> Pasaporte
    if limpio.isalnum() and 5 <= len(limpio) <= 15:
        return None, limpio.upper()

    # Si es solo dígitos pero no tiene longitud de DNI
    if limpio.isdigit():
        if len(limpio) < 7:
            return None, None
        return limpio[:8], None  # Truncar a 8 dígitos

    return None, limpio.upper() if limpio else (None, None)


def _split_apellido_nombre(valor: Any) -> tuple[str, str]:
    """Separa 'APELLIDO Y NOMBRE' en (apellido, nombre).

    Estrategia: si hay coma, separa por coma (Apellido, Nombre).
    Si no hay coma, la ÚLTIMA palabra es el nombre y el resto es apellido.
    Esto maneja mejor apellidos compuestos como 'DE LA CRUZ JUAN'.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "", ""

    texto = sanitizar_texto(str(valor))
    if not texto:
        return "", ""

    # Si tiene coma: "APELLIDO, NOMBRE" o "APELLIDO,NOMBRE"
    if "," in texto:
        partes = texto.split(",", 1)
        apellido = partes[0].strip()
        nombre = partes[1].strip() if len(partes) > 1 else ""
        return apellido, nombre

    # Sin coma: última palabra = nombre, resto = apellido
    # Ej: "DE LA CRUZ JUAN" -> ("DE LA CRUZ", "JUAN")
    # Ej: "GONZALEZ MARIA" -> ("GONZALEZ", "MARIA")
    palabras = texto.split()
    if len(palabras) == 1:
        return palabras[0], ""
    if len(palabras) == 2:
        return palabras[0], palabras[1]

    # 3+ palabras: última es nombre, resto es apellido
    nombre = palabras[-1]
    apellido = " ".join(palabras[:-1])
    return apellido, nombre


# ============================================================
# Procesamiento completo del DataFrame
# ============================================================
def procesar_dataframe(
    df: pd.DataFrame,
    mapeo: dict[str, str],
) -> tuple[list[dict], list[dict]]:
    """Procesa un DataFrame mapeado y retorna datos normalizados.

    Retorna:
        (registros_validos, registros_con_error)
        Cada registro válido es un dict con claves para PersonaSchema + EstadiaSchema.
        Cada registro con error es un dict con 'fila', 'datos', 'errores'.
    """
    registros: list[dict] = []
    errores: list[dict] = []

    # Invertir mapeo: campo_interno -> nombre_columna_excel
    campo_a_col = {campo: col_excel for col_excel, campo in mapeo.items()}

    for idx, row in df.iterrows():
        fila_num = idx + 2  # +2 porque fila 1 es header y idx es 0-based
        try:
            registro = _procesar_fila(row, campo_a_col, fila_num)
            if registro:
                registros.append(registro)
        except Exception as e:
            errores.append({
                "fila": fila_num,
                "datos": {col: str(row.get(col, "")) for col in mapeo.keys()},
                "errores": [str(e)],
            })

    logger.info(
        "Procesamiento: %d válidos, %d errores de %d filas",
        len(registros), len(errores), len(df),
    )
    return registros, errores


def _procesar_fila(row: pd.Series, campo_a_col: dict[str, str], fila_num: int) -> Optional[dict]:
    """Procesa una fila individual del DataFrame."""
    def get_val(campo: str) -> Any:
        col = campo_a_col.get(campo)
        if col is None:
            return None
        val = row.get(col)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return val

    # --- Nombre y Apellido ---
    apellido = ""
    nombre = ""

    if "apellido_nombre" in campo_a_col:
        apellido, nombre = _split_apellido_nombre(get_val("apellido_nombre"))
    if "apellido" in campo_a_col:
        val = get_val("apellido")
        if val:
            apellido = sanitizar_texto(str(val))
    if "nombre" in campo_a_col:
        val = get_val("nombre")
        if val:
            nombre = sanitizar_texto(str(val))

    if not apellido and not nombre:
        return None  # Fila vacía

    # --- Documento ---
    dni = None
    pasaporte = None

    if "dni" in campo_a_col:
        dni, pasaporte = _parse_documento(get_val("dni"))
    if "pasaporte" in campo_a_col:
        val = get_val("pasaporte")
        if val:
            _, pas = _parse_documento(val)
            if pas:
                pasaporte = pas

    if not dni and not pasaporte:
        raise ValueError(f"Fila {fila_num}: sin documento válido (DNI o Pasaporte)")

    # --- Fechas ---
    fecha_entrada = _parse_date(get_val("fecha_entrada"))
    fecha_salida = _parse_date(get_val("fecha_salida"))

    if not fecha_entrada:
        raise ValueError(f"Fila {fila_num}: fecha de entrada inválida o ausente")

    # --- Otros campos ---
    nacionalidad = sanitizar_texto(str(get_val("nacionalidad") or "Argentina"))
    procedencia = sanitizar_texto(str(get_val("procedencia") or "S/D"))
    profesion = get_val("profesion")
    if profesion:
        profesion = sanitizar_texto(str(profesion))

    edad = _parse_edad(get_val("edad"))
    fecha_nacimiento = _parse_date(get_val("fecha_nacimiento"))

    # Si no hay edad pero sí fecha de nacimiento, calcular
    if edad is None and fecha_nacimiento:
        ref = fecha_entrada or date.today()
        edad = ref.year - fecha_nacimiento.year
        if (ref.month, ref.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
            edad -= 1

    establecimiento = get_val("establecimiento")
    if establecimiento:
        establecimiento = sanitizar_texto(str(establecimiento))

    habitacion = get_val("habitacion")
    if habitacion:
        habitacion = sanitizar_texto(str(habitacion))

    telefono = get_val("telefono")
    if telefono:
        telefono = sanitizar_texto(str(telefono))

    destino = get_val("destino")
    if destino:
        destino = sanitizar_texto(str(destino))

    vehiculo = get_val("vehiculo")
    vehiculo_datos = None
    vehiculo_tiene = False
    if vehiculo:
        vehiculo_datos = sanitizar_texto(str(vehiculo))
        vehiculo_tiene = True

    return {
        # Datos de Persona
        "nacionalidad": nacionalidad,
        "procedencia": procedencia,
        "apellido": apellido,
        "nombre": nombre,
        "dni": dni,
        "pasaporte": pasaporte,
        "fecha_nacimiento": str(fecha_nacimiento) if fecha_nacimiento else None,
        "profesion": profesion,
        "telefono": telefono,
        # Datos de Estadía
        "establecimiento": establecimiento,
        "habitacion": habitacion or "S/N",
        "edad": edad,
        "fecha_entrada": str(fecha_entrada),
        "fecha_salida": str(fecha_salida) if fecha_salida else None,
        "destino": destino,
        "vehiculo_tiene": vehiculo_tiene,
        "vehiculo_datos": vehiculo_datos,
    }


# ============================================================
# Función de preview
# ============================================================
def preview_archivo(filepath: str | Path, max_rows: int = PREVIEW_ROWS) -> dict:
    """Retorna un preview del archivo Excel para confirmación del usuario.

    Retorna:
        {
            "columnas_excel": [...],
            "mapeo": {col_excel: campo_interno},
            "columnas_faltantes": [...],
            "filas_preview": [...],
            "total_filas": int,
        }
    """
    df = leer_archivo(filepath)
    mapeo = detectar_mapeo(df)
    faltantes = obtener_columnas_faltantes(mapeo)

    preview_df = df.head(max_rows)
    filas = []
    for _, row in preview_df.iterrows():
        fila_dict = {}
        for col_excel, campo in mapeo.items():
            val = row.get(col_excel)
            fila_dict[campo] = "" if val is None or (isinstance(val, float) and pd.isna(val)) else str(val)
        filas.append(fila_dict)

    return {
        "columnas_excel": list(df.columns),
        "mapeo": mapeo,
        "columnas_faltantes": faltantes,
        "filas_preview": filas,
        "total_filas": len(df),
    }
'''

# ============================================================
# controllers/__init__.py
# ============================================================
FILES["controllers/__init__.py"] = '''"""Módulo de controladores de S.C.A.H. v2."""
'''

# ============================================================
# controllers/auth_controller.py
# ============================================================
FILES["controllers/auth_controller.py"] = '''"""Controlador de autenticación para S.C.A.H. v2."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from config.settings import (
    DEFAULT_ADMIN_FULLNAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    LOCKOUT_DURATION_MINUTES,
    MAX_LOGIN_ATTEMPTS,
    ROLES_USUARIO,
)
from models.usuario import UsuarioDAO
from utils.encryption import hash_password, verify_password
from utils.exceptions import (
    AccountDisabledError,
    AccountLockedError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from utils.logger import get_logger

logger = get_logger("auth_controller")


@dataclass
class SessionInfo:
    """Información de la sesión activa."""
    user_id: int
    username: str
    nombre_completo: str
    rol: str
    login_time: datetime = field(default_factory=datetime.now)

    def tiene_permiso(self, roles_requeridos: list[str]) -> bool:
        return self.rol in roles_requeridos

    @property
    def es_admin(self) -> bool:
        return self.rol == "admin"

    @property
    def es_supervisor(self) -> bool:
        return self.rol in ("admin", "supervisor")


class AuthController:
    """Gestiona autenticación y sesiones."""

    def __init__(self):
        self._session: Optional[SessionInfo] = None

    @property
    def session(self) -> Optional[SessionInfo]:
        return self._session

    @property
    def is_authenticated(self) -> bool:
        return self._session is not None

    @property
    def current_user(self) -> str:
        return self._session.username if self._session else "sistema"

    def ensure_admin_exists(self) -> None:
        """Crea el usuario admin por defecto si no existe."""
        if not UsuarioDAO.existe_username(DEFAULT_ADMIN_USERNAME):
            hashed = hash_password(DEFAULT_ADMIN_PASSWORD)
            UsuarioDAO.crear(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hashed,
                nombre_completo=DEFAULT_ADMIN_FULLNAME,
                rol="admin",
            )
            logger.info("Usuario admin por defecto creado")

    def login(self, username: str, password: str) -> SessionInfo:
        """Autentica un usuario y crea una sesión."""
        usuario = UsuarioDAO.obtener_por_username(username)
        if not usuario:
            raise UserNotFoundError()

        # Verificar si la cuenta está activa
        if not usuario.get("activo", True):
            raise AccountDisabledError()

        # Verificar bloqueo temporal
        bloqueado_hasta = usuario.get("bloqueado_hasta")
        if bloqueado_hasta:
            if isinstance(bloqueado_hasta, str):
                bloqueado_hasta = datetime.strptime(bloqueado_hasta, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < bloqueado_hasta:
                remaining = int((bloqueado_hasta - datetime.now()).total_seconds() / 60) + 1
                raise AccountLockedError(minutes_remaining=remaining)
            else:
                UsuarioDAO.resetear_intentos(username)

        # Verificar contraseña
        if not verify_password(password, usuario["password_hash"]):
            intentos = UsuarioDAO.incrementar_intentos_fallidos(username)
            if intentos >= MAX_LOGIN_ATTEMPTS:
                hasta = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                UsuarioDAO.bloquear_cuenta(username, hasta)
                raise AccountLockedError(minutes_remaining=LOCKOUT_DURATION_MINUTES)
            raise InvalidCredentialsError(
                f"Credenciales inválidas. Intentos restantes: {MAX_LOGIN_ATTEMPTS - intentos}"
            )

        # Login exitoso
        UsuarioDAO.resetear_intentos(username)
        UsuarioDAO.actualizar_ultimo_acceso(username)

        self._session = SessionInfo(
            user_id=usuario["id"],
            username=usuario["username"],
            nombre_completo=usuario["nombre_completo"],
            rol=usuario["rol"],
        )
        logger.info("Login exitoso: %s (rol: %s)", username, usuario["rol"])
        return self._session

    def logout(self) -> None:
        """Cierra la sesión actual."""
        if self._session:
            logger.info("Logout: %s", self._session.username)
            self._session = None

    def require_role(self, *roles: str) -> bool:
        """Verifica que el usuario tenga uno de los roles especificados."""
        if not self._session:
            return False
        return self._session.tiene_permiso(list(roles))
'''

# ============================================================
# controllers/persona_controller.py
# ============================================================
FILES["controllers/persona_controller.py"] = '''"""Controlador de Persona para S.C.A.H. v2."""

from pydantic import ValidationError

from models.auditoria import AuditoriaDAO
from models.persona import PersonaDAO, PersonaSchema
from utils.exceptions import DuplicateRecordError, ValidationError as AppValidationError
from utils.logger import get_logger

logger = get_logger("persona_controller")


class PersonaController:
    """Gestiona operaciones CRUD de personas."""

    def __init__(self, usuario: str = "sistema"):
        self.usuario = usuario

    def crear(self, datos: dict) -> int:
        """Crea una nueva persona con validación."""
        try:
            schema = PersonaSchema(**datos)
        except ValidationError as e:
            errores = "; ".join(err["msg"] for err in e.errors())
            raise AppValidationError(errores)

        # Verificar duplicado por documento
        existente = PersonaDAO.buscar_por_documento(
            dni=schema.dni, pasaporte=schema.pasaporte
        )
        if existente:
            raise DuplicateRecordError(
                f"Ya existe una persona con ese documento (ID: {existente['id']})"
            )

        persona_id = PersonaDAO.crear(schema.model_dump())
        AuditoriaDAO.registrar(
            usuario=self.usuario,
            accion="CREAR_PERSONA",
            tabla_afectada="personas",
            registro_id=persona_id,
            datos_nuevos=schema.model_dump(),
        )
        return persona_id

    def obtener_o_crear(self, datos: dict) -> int:
        """Obtiene una persona existente por documento, o la crea si no existe.
        Usado durante importación masiva."""
        dni = datos.get("dni")
        pasaporte = datos.get("pasaporte")

        existente = PersonaDAO.buscar_por_documento(dni=dni, pasaporte=pasaporte)
        if existente:
            return existente["id"]

        try:
            schema = PersonaSchema(**datos)
        except ValidationError:
            # Mínimo para crear: relajar validación
            datos_min = {
                "nacionalidad": datos.get("nacionalidad", "Argentina"),
                "procedencia": datos.get("procedencia", "S/D"),
                "apellido": datos.get("apellido", "S/D"),
                "nombre": datos.get("nombre", "S/D"),
                "dni": dni,
                "pasaporte": pasaporte,
                "fecha_nacimiento": datos.get("fecha_nacimiento"),
                "profesion": datos.get("profesion"),
                "telefono": datos.get("telefono"),
            }
            schema = PersonaSchema(**datos_min)

        return PersonaDAO.crear(schema.model_dump())

    def actualizar(self, persona_id: int, datos: dict) -> bool:
        """Actualiza los datos de una persona."""
        anterior = PersonaDAO.obtener_por_id(persona_id)
        if not anterior:
            raise AppValidationError("Persona no encontrada")

        resultado = PersonaDAO.actualizar(persona_id, datos)
        if resultado:
            AuditoriaDAO.registrar(
                usuario=self.usuario,
                accion="ACTUALIZAR_PERSONA",
                tabla_afectada="personas",
                registro_id=persona_id,
                datos_anteriores=anterior,
                datos_nuevos=datos,
            )
        return resultado

    def eliminar(self, persona_id: int) -> bool:
        """Elimina lógicamente una persona."""
        anterior = PersonaDAO.obtener_por_id(persona_id)
        if not anterior:
            raise AppValidationError("Persona no encontrada")

        resultado = PersonaDAO.eliminar(persona_id)
        if resultado:
            AuditoriaDAO.registrar(
                usuario=self.usuario,
                accion="ELIMINAR_PERSONA",
                tabla_afectada="personas",
                registro_id=persona_id,
                datos_anteriores=anterior,
            )
        return resultado

    def buscar(self, termino: str, campo: str | None = None, limite: int = 50) -> list[dict]:
        return PersonaDAO.buscar_rapida(termino, campo, limite)
'''

# ============================================================
# controllers/estadia_controller.py
# ============================================================
FILES["controllers/estadia_controller.py"] = '''"""Controlador de Estadía para S.C.A.H. v2."""

from pydantic import ValidationError

from models.auditoria import AuditoriaDAO
from models.estadia import EstadiaDAO, EstadiaSchema
from utils.exceptions import ValidationError as AppValidationError
from utils.logger import get_logger

logger = get_logger("estadia_controller")


class EstadiaController:
    """Gestiona operaciones CRUD de estadías."""

    def __init__(self, usuario: str = "sistema"):
        self.usuario = usuario

    def crear(self, datos: dict) -> int:
        """Crea una nueva estadía con validación."""
        datos.setdefault("usuario_carga", self.usuario)
        try:
            schema = EstadiaSchema(**datos)
        except ValidationError as e:
            errores = "; ".join(err["msg"] for err in e.errors())
            raise AppValidationError(errores)

        estadia_id = EstadiaDAO.crear(schema.model_dump())
        AuditoriaDAO.registrar(
            usuario=self.usuario,
            accion="CREAR_ESTADIA",
            tabla_afectada="estadias",
            registro_id=estadia_id,
            datos_nuevos=schema.model_dump(),
        )
        return estadia_id

    def actualizar(self, estadia_id: int, datos: dict) -> bool:
        """Actualiza una estadía existente."""
        anterior = EstadiaDAO.obtener_por_id(estadia_id)
        if not anterior:
            raise AppValidationError("Estadía no encontrada")

        resultado = EstadiaDAO.actualizar(estadia_id, datos)
        if resultado:
            AuditoriaDAO.registrar(
                usuario=self.usuario,
                accion="ACTUALIZAR_ESTADIA",
                tabla_afectada="estadias",
                registro_id=estadia_id,
                datos_anteriores=anterior,
                datos_nuevos=datos,
            )
        return resultado

    def eliminar(self, estadia_id: int) -> bool:
        """Elimina lógicamente una estadía."""
        anterior = EstadiaDAO.obtener_por_id(estadia_id)
        if not anterior:
            raise AppValidationError("Estadía no encontrada")

        resultado = EstadiaDAO.eliminar(estadia_id)
        if resultado:
            AuditoriaDAO.registrar(
                usuario=self.usuario,
                accion="ELIMINAR_ESTADIA",
                tabla_afectada="estadias",
                registro_id=estadia_id,
                datos_anteriores=anterior,
            )
        return resultado

    def buscar(
        self,
        termino: str = "",
        campo: str | None = None,
        filtros: dict | None = None,
        pagina: int = 1,
        por_pagina: int = 50,
    ) -> tuple[list[dict], int]:
        return EstadiaDAO.buscar_completa(termino, campo, filtros, pagina=pagina, por_pagina=por_pagina)

    def historial_persona(self, persona_id: int) -> list[dict]:
        return EstadiaDAO.obtener_por_persona(persona_id)
'''

# ============================================================
# controllers/import_controller.py  — REESCRITURA COMPLETA
# ============================================================
FILES["controllers/import_controller.py"] = '''"""Controlador de importación Excel para S.C.A.H. v2.

Orquesta: lectura del Excel -> detección de columnas -> procesamiento ->
creación de personas y estadías en la BD.
"""

from pathlib import Path
from typing import Callable, Optional

from controllers.persona_controller import PersonaController
from controllers.estadia_controller import EstadiaController
from models.auditoria import AuditoriaDAO
from utils.excel_parser import (
    leer_archivo,
    detectar_mapeo,
    obtener_columnas_faltantes,
    procesar_dataframe,
    preview_archivo,
)
from utils.exceptions import ImportFileError, MissingColumnsError
from utils.logger import get_logger

logger = get_logger("import_controller")


class ImportController:
    """Orquesta la importación de datos desde archivos Excel."""

    def __init__(self, usuario: str = "sistema"):
        self.usuario = usuario
        self.persona_ctrl = PersonaController(usuario)
        self.estadia_ctrl = EstadiaController(usuario)

    def preview(self, filepath: str) -> dict:
        """Genera un preview del archivo para confirmación."""
        return preview_archivo(filepath)

    def importar(
        self,
        filepath: str,
        mapeo_override: dict[str, str] | None = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict:
        """Importa datos desde un archivo Excel.

        Args:
            filepath: Ruta al archivo Excel
            mapeo_override: Mapeo manual (opcional, sobreescribe autodetección)
            on_progress: Callback (actual, total, mensaje) para progreso

        Returns:
            dict con estadísticas de la importación
        """
        stats = {
            "archivo": str(filepath),
            "total_filas": 0,
            "personas_creadas": 0,
            "personas_existentes": 0,
            "estadias_creadas": 0,
            "errores": [],
            "warnings": [],
        }

        try:
            # 1. Leer archivo
            if on_progress:
                on_progress(0, 100, "Leyendo archivo Excel...")
            df = leer_archivo(filepath)
            stats["total_filas"] = len(df)

            # 2. Detectar mapeo
            if on_progress:
                on_progress(5, 100, "Detectando columnas...")
            mapeo = mapeo_override or detectar_mapeo(df)
            faltantes = obtener_columnas_faltantes(mapeo)
            if faltantes:
                raise MissingColumnsError(missing=faltantes)

            # 3. Procesar filas
            if on_progress:
                on_progress(10, 100, "Procesando datos...")
            registros, errores_parse = procesar_dataframe(df, mapeo)
            stats["errores"].extend(errores_parse)

            # 4. Insertar en BD
            total = len(registros)
            for i, reg in enumerate(registros):
                try:
                    # Crear o encontrar persona
                    datos_persona = {
                        k: reg[k] for k in (
                            "nacionalidad", "procedencia", "apellido", "nombre",
                            "dni", "pasaporte", "fecha_nacimiento", "profesion", "telefono",
                        ) if reg.get(k) is not None
                    }
                    persona_id = self.persona_ctrl.obtener_o_crear(datos_persona)

                    # Verificar si es persona nueva o existente
                    from models.persona import PersonaDAO
                    # (la lógica de obtener_o_crear ya maneja esto)

                    # Crear estadía
                    datos_estadia = {
                        "persona_id": persona_id,
                        "establecimiento": reg.get("establecimiento"),
                        "habitacion": reg.get("habitacion", "S/N"),
                        "edad": reg.get("edad"),
                        "fecha_entrada": reg["fecha_entrada"],
                        "fecha_salida": reg.get("fecha_salida"),
                        "destino": reg.get("destino"),
                        "vehiculo_tiene": reg.get("vehiculo_tiene", False),
                        "vehiculo_datos": reg.get("vehiculo_datos"),
                        "usuario_carga": self.usuario,
                    }
                    self.estadia_ctrl.crear(datos_estadia)
                    stats["estadias_creadas"] += 1

                    if on_progress and i % 10 == 0:
                        pct = 10 + int(85 * (i + 1) / total)
                        on_progress(pct, 100, f"Importando registro {i+1} de {total}...")

                except Exception as e:
                    stats["errores"].append({
                        "fila": i + 2,
                        "datos": {k: str(v) for k, v in reg.items() if v is not None},
                        "errores": [str(e)],
                    })

            if on_progress:
                on_progress(100, 100, "Importación completada")

        except (ImportFileError, MissingColumnsError):
            raise
        except Exception as e:
            logger.error("Error durante importación: %s", e)
            raise ImportFileError(f"Error al importar: {e}") from e

        # Registrar en auditoría
        AuditoriaDAO.registrar(
            usuario=self.usuario,
            accion="IMPORTAR_EXCEL",
            tabla_afectada="estadias",
            detalles=(
                f"Archivo: {Path(filepath).name} | "
                f"Filas: {stats['total_filas']} | "
                f"Estadías creadas: {stats['estadias_creadas']} | "
                f"Errores: {len(stats['errores'])}"
            ),
        )

        logger.info(
            "Importación completada: %d estadías de %d filas (%d errores)",
            stats["estadias_creadas"], stats["total_filas"], len(stats["errores"]),
        )
        return stats
'''

# ============================================================
# controllers/report_controller.py
# ============================================================
FILES["controllers/report_controller.py"] = '''"""Controlador de reportes para S.C.A.H. v2."""

from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from models.estadia import EstadiaDAO
from config.settings import APP_ORGANIZATION, APP_SUBTITLE
from utils.logger import get_logger

logger = get_logger("report_controller")


class ReportController:
    """Genera exportaciones en Excel y PDF."""

    def __init__(self, usuario: str = "sistema"):
        self.usuario = usuario

    def exportar_excel(
        self,
        filepath: str,
        filtros: dict | None = None,
        termino: str = "",
    ) -> str:
        """Exporta resultados de búsqueda a Excel."""
        registros, total = EstadiaDAO.buscar_completa(
            termino=termino,
            filtros=filtros,
            pagina=1,
            por_pagina=10000,
        )
        if not registros:
            raise ValueError("No hay datos para exportar")

        df = pd.DataFrame(registros)

        # Renombrar columnas para legibilidad
        columnas_rename = {
            "establecimiento": "HOTEL",
            "nacionalidad": "NACIONALIDAD",
            "procedencia": "PROCEDENCIA",
            "apellido": "APELLIDO",
            "nombre": "NOMBRE",
            "dni": "D.N.I.",
            "pasaporte": "PASAPORTE",
            "fecha_nacimiento": "FECHA NAC.",
            "edad": "EDAD",
            "profesion": "PROFESIÓN",
            "fecha_entrada": "ENTRADA",
            "fecha_salida": "SALIDA",
            "habitacion": "HABITACIÓN",
        }
        cols_presentes = {k: v for k, v in columnas_rename.items() if k in df.columns}
        df = df[list(cols_presentes.keys())].rename(columns=cols_presentes)

        df.to_excel(filepath, index=False, engine="openpyxl")
        logger.info("Exportación Excel: %s (%d registros)", filepath, len(df))
        return filepath

    def exportar_pdf(
        self,
        filepath: str,
        filtros: dict | None = None,
        termino: str = "",
    ) -> str:
        """Exporta resultados a PDF con formato institucional."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except ImportError:
            raise ImportError("ReportLab no está instalado. Ejecute: pip install reportlab")

        registros, total = EstadiaDAO.buscar_completa(
            termino=termino,
            filtros=filtros,
            pagina=1,
            por_pagina=10000,
        )
        if not registros:
            raise ValueError("No hay datos para exportar")

        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(A4),
            rightMargin=10*mm, leftMargin=10*mm,
            topMargin=15*mm, bottomMargin=15*mm,
        )
        styles = getSampleStyleSheet()
        elements = []

        # Header institucional
        elements.append(Paragraph(APP_ORGANIZATION, styles["Title"]))
        elements.append(Paragraph(APP_SUBTITLE, styles["Heading2"]))
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph(
            f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Total: {len(registros)} registros",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 5*mm))

        # Tabla de datos
        headers = ["HOTEL", "APELLIDO", "NOMBRE", "DNI", "NACIONALIDAD", "ENTRADA", "SALIDA"]
        table_data = [headers]
        for reg in registros:
            table_data.append([
                str(reg.get("establecimiento", "")),
                str(reg.get("apellido", "")),
                str(reg.get("nombre", "")),
                str(reg.get("dni", "") or reg.get("pasaporte", "")),
                str(reg.get("nacionalidad", "")),
                str(reg.get("fecha_entrada", "")),
                str(reg.get("fecha_salida", "")),
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f538d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
        ]))
        elements.append(table)

        doc.build(elements)
        logger.info("Exportación PDF: %s (%d registros)", filepath, len(registros))
        return filepath
'''

# ============================================================
# controllers/huesped_controller.py  (compatibilidad)
# ============================================================
FILES["controllers/huesped_controller.py"] = '''"""Controlador de compatibilidad — wrapper sobre persona + estadia."""

from controllers.persona_controller import PersonaController
from controllers.estadia_controller import EstadiaController
from utils.logger import get_logger

logger = get_logger("huesped_controller")


class HuespedController:
    """Wrapper de compatibilidad. Los métodos delegan a PersonaController + EstadiaController."""

    def __init__(self, usuario: str = "sistema"):
        self.usuario = usuario
        self.persona_ctrl = PersonaController(usuario)
        self.estadia_ctrl = EstadiaController(usuario)

    def buscar_rapida(self, termino: str, campo: str | None = None, limite: int = 50):
        resultados, _ = self.estadia_ctrl.buscar(termino=termino, campo=campo, por_pagina=limite)
        return resultados
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
    print("S.C.A.H. v2 - Reconstrucción: Fase 2")
    print("Excel Parser + Controllers")
    print("=" * 60)
    write_all()
    print("\nFase 2 completada.")
