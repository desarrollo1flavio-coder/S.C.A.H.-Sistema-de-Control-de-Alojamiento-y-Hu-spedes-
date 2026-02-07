"""Validaciones de datos para el sistema S.C.A.H.

Funciones de validación para DNI, pasaporte, teléfono,
fechas y otros campos del formulario de huéspedes.
"""

import re
from datetime import date, datetime

from utils.logger import get_logger

logger = get_logger("validators")

# ============================================================
# PATRONES REGEX
# ============================================================
DNI_PATTERN: re.Pattern[str] = re.compile(r"^\d{7,8}$")
PASAPORTE_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9]{5,15}$")
TELEFONO_PATTERN: re.Pattern[str] = re.compile(r"^[\+\-\d\s\(\)]{6,20}$")
NOMBRE_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-záéíóúñÁÉÍÓÚÑüÜ\s\'\-]{2,100}$")


def validar_dni(dni: str) -> tuple[bool, str]:
    """Valida el formato de un número de DNI argentino (7-8 dígitos).

    Args:
        dni: Número de DNI a validar.

    Returns:
        Tupla (es_válido, mensaje_error).
    """
    if not dni or not dni.strip():
        return True, ""  # DNI es condicional
    dni_limpio = dni.strip()
    if DNI_PATTERN.match(dni_limpio):
        return True, ""
    return False, "El DNI debe tener 7 u 8 dígitos numéricos"


def validar_pasaporte(pasaporte: str) -> tuple[bool, str]:
    """Valida el formato de un número de pasaporte (5-15 alfanumérico).

    Args:
        pasaporte: Número de pasaporte a validar.

    Returns:
        Tupla (es_válido, mensaje_error).
    """
    if not pasaporte or not pasaporte.strip():
        return True, ""  # Pasaporte es condicional
    pasaporte_limpio = pasaporte.strip()
    if PASAPORTE_PATTERN.match(pasaporte_limpio):
        return True, ""
    return False, "El pasaporte debe tener entre 5 y 15 caracteres alfanuméricos"


def validar_dni_o_pasaporte(dni: str, pasaporte: str) -> tuple[bool, str]:
    """Valida que al menos uno de los dos documentos esté presente y sea válido.

    Args:
        dni: Número de DNI.
        pasaporte: Número de pasaporte.

    Returns:
        Tupla (es_válido, mensaje_error).
    """
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
    """Valida el formato de un número de teléfono.

    Args:
        telefono: Número de teléfono a validar.

    Returns:
        Tupla (es_válido, mensaje_error).
    """
    if not telefono or not telefono.strip():
        return True, ""  # Teléfono es opcional
    if TELEFONO_PATTERN.match(telefono.strip()):
        return True, ""
    return False, "Formato de teléfono inválido"


def validar_nombre(valor: str, campo: str = "Nombre") -> tuple[bool, str]:
    """Valida un nombre o apellido.

    Args:
        valor: Texto a validar.
        campo: Nombre del campo para el mensaje de error.

    Returns:
        Tupla (es_válido, mensaje_error).
    """
    if not valor or not valor.strip():
        return False, f"{campo} es obligatorio"
    valor_limpio = valor.strip()
    if len(valor_limpio) < 2:
        return False, f"{campo} debe tener al menos 2 caracteres"
    if NOMBRE_PATTERN.match(valor_limpio):
        return True, ""
    return False, f"{campo} contiene caracteres no válidos"


def validar_edad(edad: str | int | None) -> tuple[bool, str]:
    """Valida que la edad sea un número válido entre 1 y 149.

    Args:
        edad: Edad a validar (string o entero).

    Returns:
        Tupla (es_válido, mensaje_error).
    """
    if edad is None or (isinstance(edad, str) and not edad.strip()):
        return True, ""  # Edad es opcional
    try:
        edad_int = int(edad)
    except (ValueError, TypeError):
        return False, "La edad debe ser un número entero"
    if edad_int < 1 or edad_int > 149:
        return False, "La edad debe estar entre 1 y 149 años"
    return True, ""


def validar_fecha_entrada(fecha: str | date) -> tuple[bool, str]:
    """Valida la fecha de entrada (no puede ser futura).

    Args:
        fecha: Fecha a validar.

    Returns:
        Tupla (es_válido, mensaje_error).
    """
    if not fecha:
        return False, "La fecha de entrada es obligatoria"
    try:
        if isinstance(fecha, str):
            fecha_obj = datetime.strptime(fecha.strip(), "%Y-%m-%d").date()
        else:
            fecha_obj = fecha
        if fecha_obj > date.today():
            return False, "La fecha de entrada no puede ser futura"
        return True, ""
    except ValueError:
        return False, "Formato de fecha inválido. Use AAAA-MM-DD"


def validar_fecha_salida(
    fecha_salida: str | date | None, fecha_entrada: str | date
) -> tuple[bool, str]:
    """Valida la fecha de salida en relación a la fecha de entrada.

    Args:
        fecha_salida: Fecha de salida a validar (puede ser None).
        fecha_entrada: Fecha de entrada para comparación.

    Returns:
        Tupla (es_válido, mensaje_error).
    """
    if not fecha_salida:
        return True, ""  # Fecha de salida es opcional
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
    """Sanitiza un texto eliminando caracteres peligrosos y espacios extra.

    Args:
        texto: Texto a sanitizar.

    Returns:
        Texto limpio y seguro.
    """
    if not texto:
        return ""
    limpio = " ".join(texto.strip().split())
    limpio = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", limpio)
    return limpio
