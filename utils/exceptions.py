"""Excepciones personalizadas del sistema S.C.A.H.

Define una jerarquía de excepciones para manejar errores
de forma específica y descriptiva en toda la aplicación.
"""


class SCAHBaseError(Exception):
    """Excepción base para todas las excepciones del sistema S.C.A.H."""

    def __init__(self, message: str = "Error interno del sistema", code: str = "SCAH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# ============================================================
# Errores de Base de Datos
# ============================================================
class DatabaseError(SCAHBaseError):
    """Error relacionado con operaciones de base de datos."""

    def __init__(self, message: str = "Error en la base de datos"):
        super().__init__(message, "DB_ERROR")


class DatabaseConnectionError(DatabaseError):
    """No se pudo establecer conexión con la base de datos."""

    def __init__(self, message: str = "No se pudo conectar a la base de datos"):
        super().__init__(message)
        self.code = "DB_CONNECTION_ERROR"


class MigrationError(DatabaseError):
    """Error al ejecutar migraciones de base de datos."""

    def __init__(self, message: str = "Error al ejecutar migración"):
        super().__init__(message)
        self.code = "DB_MIGRATION_ERROR"


# ============================================================
# Errores de Autenticación
# ============================================================
class AuthenticationError(SCAHBaseError):
    """Error de autenticación genérico."""

    def __init__(self, message: str = "Error de autenticación"):
        super().__init__(message, "AUTH_ERROR")


class InvalidCredentialsError(AuthenticationError):
    """Credenciales de acceso inválidas."""

    def __init__(self, message: str = "Usuario o contraseña incorrectos"):
        super().__init__(message)
        self.code = "AUTH_INVALID_CREDENTIALS"


class AccountLockedError(AuthenticationError):
    """Cuenta bloqueada por exceso de intentos fallidos."""

    def __init__(self, message: str = "Cuenta bloqueada temporalmente", minutes_remaining: int = 0):
        self.minutes_remaining = minutes_remaining
        if minutes_remaining > 0:
            message = f"Cuenta bloqueada. Intente nuevamente en {minutes_remaining} minutos"
        super().__init__(message)
        self.code = "AUTH_ACCOUNT_LOCKED"


class AccountDisabledError(AuthenticationError):
    """Cuenta de usuario deshabilitada."""

    def __init__(self, message: str = "Cuenta deshabilitada. Contacte al administrador"):
        super().__init__(message)
        self.code = "AUTH_ACCOUNT_DISABLED"


class UserNotFoundError(AuthenticationError):
    """Usuario no encontrado en el sistema."""

    def __init__(self, message: str = "Usuario no encontrado"):
        super().__init__(message)
        self.code = "AUTH_USER_NOT_FOUND"


# ============================================================
# Errores de Validación
# ============================================================
class ValidationError(SCAHBaseError):
    """Error de validación de datos."""

    def __init__(self, message: str = "Datos inválidos", field: str = ""):
        self.field = field
        if field:
            message = f"Campo '{field}': {message}"
        super().__init__(message, "VALIDATION_ERROR")


class DuplicateRecordError(ValidationError):
    """Registro duplicado en la base de datos."""

    def __init__(self, message: str = "El registro ya existe", field: str = ""):
        super().__init__(message, field)
        self.code = "VALIDATION_DUPLICATE"


# ============================================================
# Errores de Importación
# ============================================================
class ImportFileError(SCAHBaseError):
    """Error durante la importación masiva de datos."""

    def __init__(self, message: str = "Error durante la importación"):
        super().__init__(message, "IMPORT_ERROR")


class InvalidFileFormatError(ImportFileError):
    """Formato de archivo no soportado."""

    def __init__(self, message: str = "Formato de archivo no válido"):
        super().__init__(message)
        self.code = "IMPORT_INVALID_FORMAT"


class MissingColumnsError(ImportFileError):
    """Columnas requeridas faltantes en el archivo."""

    def __init__(self, message: str = "Faltan columnas requeridas", missing: list[str] | None = None):
        self.missing_columns = missing or []
        if missing:
            cols = ", ".join(missing)
            message = f"Columnas faltantes: {cols}"
        super().__init__(message)
        self.code = "IMPORT_MISSING_COLUMNS"


# ============================================================
# Errores de Permisos
# ============================================================
class PermissionDeniedError(SCAHBaseError):
    """Acción no permitida para el rol del usuario."""

    def __init__(self, message: str = "No tiene permisos para realizar esta acción"):
        super().__init__(message, "PERMISSION_DENIED")
