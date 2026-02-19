"""Controlador de autenticación para S.C.A.H. v2."""

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
