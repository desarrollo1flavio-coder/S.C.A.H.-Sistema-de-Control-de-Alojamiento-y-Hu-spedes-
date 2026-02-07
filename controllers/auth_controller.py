"""Controlador de autenticación para S.C.A.H.

Gestiona el login, logout, verificación de sesiones,
bloqueo de cuentas y creación del usuario administrador inicial.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from config.settings import (
    DEFAULT_ADMIN_FULLNAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    LOCKOUT_DURATION_MINUTES,
    MAX_LOGIN_ATTEMPTS,
)
from models.auditoria import AuditoriaDAO
from models.usuario import UsuarioDAO
from utils.encryption import hash_password, verify_password
from utils.exceptions import (
    AccountDisabledError,
    AccountLockedError,
    InvalidCredentialsError,
)
from utils.logger import get_logger

logger = get_logger("auth_controller")


@dataclass
class SessionInfo:
    """Información de la sesión activa del usuario."""

    user_id: int
    username: str
    nombre_completo: str
    rol: str
    login_time: datetime = field(default_factory=datetime.now)

    def tiene_permiso(self, permiso: str) -> bool:
        """Verifica si el rol del usuario tiene un permiso específico.

        Args:
            permiso: Permiso a verificar ('admin', 'escritura', 'lectura', etc.).

        Returns:
            True si el usuario tiene el permiso.
        """
        permisos_por_rol: dict[str, list[str]] = {
            "admin": ["admin", "escritura", "lectura", "eliminar", "configurar", "exportar"],
            "supervisor": ["escritura", "lectura", "exportar"],
            "operador": ["escritura", "lectura"],
        }
        return permiso in permisos_por_rol.get(self.rol, [])


class AuthController:
    """Controlador de autenticación y gestión de sesiones."""

    def __init__(self) -> None:
        """Inicializa el controlador con sesión vacía."""
        self._session: Optional[SessionInfo] = None
        logger.debug("AuthController inicializado")

    @property
    def session(self) -> Optional[SessionInfo]:
        """Retorna la sesión activa actual."""
        return self._session

    @property
    def is_authenticated(self) -> bool:
        """Indica si hay un usuario autenticado."""
        return self._session is not None

    def login(self, username: str, password: str) -> SessionInfo:
        """Autentica un usuario con username y contraseña.

        Args:
            username: Nombre de usuario.
            password: Contraseña en texto plano.

        Returns:
            SessionInfo con datos de la sesión activa.

        Raises:
            InvalidCredentialsError: Si las credenciales son incorrectas.
            AccountDisabledError: Si la cuenta está deshabilitada.
            AccountLockedError: Si la cuenta está bloqueada.
        """
        username_clean = username.strip().lower()
        logger.info("Intento de login: %s", username_clean)

        # 1. Buscar usuario
        user = UsuarioDAO.obtener_por_username(username_clean)
        if not user:
            logger.warning("Login fallido - usuario no encontrado: %s", username_clean)
            AuditoriaDAO.registrar(
                usuario=username_clean,
                accion="LOGIN_FAILED",
                detalles="Usuario no encontrado",
            )
            raise InvalidCredentialsError()

        # 2. Verificar cuenta activa
        if not user["activo"]:
            logger.warning("Login fallido - cuenta deshabilitada: %s", username_clean)
            AuditoriaDAO.registrar(
                usuario=username_clean,
                accion="LOGIN_FAILED",
                detalles="Cuenta deshabilitada",
            )
            raise AccountDisabledError()

        # 3. Verificar bloqueo temporal
        if user["bloqueado_hasta"]:
            bloqueado_hasta = datetime.fromisoformat(user["bloqueado_hasta"])
            if datetime.now() < bloqueado_hasta:
                minutos = int((bloqueado_hasta - datetime.now()).total_seconds() / 60) + 1
                logger.warning("Login fallido - cuenta bloqueada: %s (%d min)", username_clean, minutos)
                AuditoriaDAO.registrar(
                    usuario=username_clean,
                    accion="LOGIN_FAILED",
                    detalles=f"Cuenta bloqueada por {minutos} minutos más",
                )
                raise AccountLockedError(minutes_remaining=minutos)
            else:
                UsuarioDAO.resetear_intentos(username_clean)

        # 4. Verificar contraseña
        if not verify_password(password, user["password_hash"]):
            intentos = UsuarioDAO.incrementar_intentos_fallidos(username_clean)

            if intentos >= MAX_LOGIN_ATTEMPTS:
                hasta = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                UsuarioDAO.bloquear_cuenta(username_clean, hasta)
                logger.warning("Cuenta bloqueada: %s (%d min)", username_clean, LOCKOUT_DURATION_MINUTES)
                AuditoriaDAO.registrar(
                    usuario=username_clean,
                    accion="LOGIN_FAILED",
                    detalles=f"Cuenta bloqueada tras {intentos} intentos fallidos",
                )
                raise AccountLockedError(minutes_remaining=LOCKOUT_DURATION_MINUTES)

            restantes = MAX_LOGIN_ATTEMPTS - intentos
            logger.warning("Contraseña incorrecta: %s (%d restantes)", username_clean, restantes)
            AuditoriaDAO.registrar(
                usuario=username_clean,
                accion="LOGIN_FAILED",
                detalles=f"Contraseña incorrecta. Intento {intentos}/{MAX_LOGIN_ATTEMPTS}",
            )
            raise InvalidCredentialsError()

        # 5. Login exitoso
        UsuarioDAO.resetear_intentos(username_clean)
        UsuarioDAO.actualizar_ultimo_acceso(username_clean)

        self._session = SessionInfo(
            user_id=user["id"],
            username=user["username"],
            nombre_completo=user["nombre_completo"],
            rol=user["rol"],
        )

        AuditoriaDAO.registrar(
            usuario=username_clean,
            accion="LOGIN",
            detalles=f"Inicio de sesión exitoso (Rol: {user['rol']})",
        )
        logger.info("Login exitoso: %s (Rol: %s)", username_clean, user["rol"])
        return self._session

    def logout(self) -> None:
        """Cierra la sesión activa del usuario."""
        if self._session:
            AuditoriaDAO.registrar(
                usuario=self._session.username,
                accion="LOGOUT",
                detalles="Cierre de sesión",
            )
            logger.info("Logout: %s", self._session.username)
            self._session = None

    def ensure_admin_exists(self) -> None:
        """Crea el usuario administrador por defecto si no existe."""
        if UsuarioDAO.existe_username(DEFAULT_ADMIN_USERNAME):
            logger.debug("Usuario admin ya existe")
            return

        logger.info("Creando usuario administrador por defecto...")
        try:
            password_hashed = hash_password(DEFAULT_ADMIN_PASSWORD)
            UsuarioDAO.crear(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=password_hashed,
                nombre_completo=DEFAULT_ADMIN_FULLNAME,
                rol="admin",
            )
            AuditoriaDAO.registrar(
                usuario="sistema",
                accion="USER_CREATE",
                tabla_afectada="usuarios",
                detalles="Usuario admin creado en la inicialización",
            )
            logger.info("Usuario administrador creado exitosamente")
        except Exception as e:
            logger.error("Error al crear usuario admin: %s", e)
            raise
