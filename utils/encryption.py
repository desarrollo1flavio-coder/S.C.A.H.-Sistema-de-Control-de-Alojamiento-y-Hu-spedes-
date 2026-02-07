"""Funciones de seguridad y encriptación para S.C.A.H.

Proporciona hashing seguro de contraseñas con bcrypt
y funciones auxiliares de seguridad.
"""

import bcrypt

from config.settings import BCRYPT_WORK_FACTOR
from utils.logger import get_logger

logger = get_logger("encryption")


def hash_password(password: str) -> str:
    """Genera un hash bcrypt seguro para una contraseña.

    Args:
        password: Contraseña en texto plano a hashear.

    Returns:
        Hash bcrypt como string UTF-8.

    Raises:
        ValueError: Si la contraseña está vacía o es None.
        RuntimeError: Si ocurre un error durante el hashing.
    """
    if not password:
        raise ValueError("La contraseña no puede estar vacía")

    try:
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=BCRYPT_WORK_FACTOR)
        hashed = bcrypt.hashpw(password_bytes, salt)
        logger.debug("Contraseña hasheada exitosamente")
        return hashed.decode("utf-8")
    except Exception as e:
        logger.error("Error al hashear contraseña: %s", e)
        raise RuntimeError("Error al procesar la contraseña") from e


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica si una contraseña coincide con su hash bcrypt.

    Args:
        password: Contraseña en texto plano a verificar.
        password_hash: Hash bcrypt almacenado previamente.

    Returns:
        True si la contraseña coincide, False en caso contrario.

    Raises:
        ValueError: Si alguno de los parámetros está vacío.
    """
    if not password or not password_hash:
        raise ValueError("La contraseña y el hash no pueden estar vacíos")

    try:
        password_bytes = password.encode("utf-8")
        hash_bytes = password_hash.encode("utf-8")
        result = bcrypt.checkpw(password_bytes, hash_bytes)
        logger.debug("Verificación de contraseña: %s", "exitosa" if result else "fallida")
        return result
    except (ValueError, TypeError) as e:
        logger.warning("Error al verificar contraseña (formato inválido): %s", e)
        return False
    except Exception as e:
        logger.error("Error inesperado al verificar contraseña: %s", e)
        return False


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Valida que una contraseña cumpla los requisitos mínimos de seguridad.

    Requisitos:
        - Mínimo 8 caracteres
        - Al menos una letra mayúscula
        - Al menos una letra minúscula
        - Al menos un dígito
        - Al menos un carácter especial (!@#$%^&*.,_-)

    Args:
        password: Contraseña a validar.

    Returns:
        Tupla (es_válida, lista_de_errores).
    """
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

    is_valid = len(errors) == 0
    if not is_valid:
        logger.debug("Contraseña no cumple requisitos: %d errores", len(errors))

    return is_valid, errors
