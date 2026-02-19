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
