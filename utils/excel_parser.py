"""Parser de archivos Excel para S.C.A.H. v2.

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
