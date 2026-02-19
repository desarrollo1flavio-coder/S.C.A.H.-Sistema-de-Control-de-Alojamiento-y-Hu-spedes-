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
            message = f"Campo '{field}': {message}"
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
