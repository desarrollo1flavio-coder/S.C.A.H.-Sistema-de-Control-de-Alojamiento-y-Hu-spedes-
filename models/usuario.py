"""Modelo y DAO (Data Access Object) de Usuario para S.C.A.H.

Define el modelo Pydantic para validación y las operaciones
de base de datos para la tabla 'usuarios'.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from config.database import get_connection, get_transaction
from config.settings import ROLES_USUARIO
from utils.logger import get_logger

logger = get_logger("models.usuario")


# ============================================================
# MODELO PYDANTIC
# ============================================================
class UsuarioSchema(BaseModel):
    """Esquema de validación para datos de usuario."""

    username: str = Field(..., min_length=3, max_length=50)
    password_hash: str = Field(..., min_length=1)
    nombre_completo: str = Field(..., min_length=2, max_length=200)
    rol: str = Field(default="operador")
    activo: bool = Field(default=True)

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, v: str) -> str:
        """Valida que el rol sea uno de los permitidos."""
        if v not in ROLES_USUARIO:
            raise ValueError(f"Rol inválido. Permitidos: {', '.join(ROLES_USUARIO)}")
        return v

    @field_validator("username")
    @classmethod
    def validar_username(cls, v: str) -> str:
        """Normaliza el nombre de usuario a minúsculas."""
        return v.strip().lower()


# ============================================================
# DAO - DATA ACCESS OBJECT
# ============================================================
class UsuarioDAO:
    """Operaciones de base de datos para la tabla 'usuarios'."""

    @staticmethod
    def crear(
        username: str, password_hash: str, nombre_completo: str, rol: str = "operador"
    ) -> int:
        """Crea un nuevo usuario en la base de datos.

        Args:
            username: Nombre de usuario único.
            password_hash: Hash bcrypt de la contraseña.
            nombre_completo: Nombre completo del usuario.
            rol: Rol del usuario ('admin', 'supervisor', 'operador').

        Returns:
            ID del usuario creado.
        """
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (username, password_hash, nombre_completo, rol) "
                "VALUES (?, ?, ?, ?)",
                (username.strip().lower(), password_hash, nombre_completo.strip(), rol),
            )
            user_id = cursor.lastrowid
            logger.info("Usuario creado: %s (ID: %s, Rol: %s)", username, user_id, rol)
            return user_id

    @staticmethod
    def obtener_por_username(username: str) -> Optional[dict]:
        """Obtiene un usuario por su nombre de usuario.

        Args:
            username: Nombre de usuario a buscar.

        Returns:
            Diccionario con datos del usuario o None si no existe.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM usuarios WHERE username = ?",
                (username.strip().lower(),),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def obtener_por_id(user_id: int) -> Optional[dict]:
        """Obtiene un usuario por su ID.

        Args:
            user_id: ID del usuario.

        Returns:
            Diccionario con datos del usuario o None.
        """
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def actualizar_ultimo_acceso(username: str) -> None:
        """Actualiza la fecha de último acceso del usuario.

        Args:
            username: Nombre de usuario.
        """
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE username = ?",
                (username.strip().lower(),),
            )

    @staticmethod
    def incrementar_intentos_fallidos(username: str) -> int:
        """Incrementa el contador de intentos fallidos.

        Args:
            username: Nombre de usuario.

        Returns:
            Número actual de intentos fallidos.
        """
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET intentos_fallidos = intentos_fallidos + 1 "
                "WHERE username = ?",
                (username.strip().lower(),),
            )
            cursor = conn.execute(
                "SELECT intentos_fallidos FROM usuarios WHERE username = ?",
                (username.strip().lower(),),
            )
            row = cursor.fetchone()
            intentos = row["intentos_fallidos"] if row else 0
            logger.warning("Intento fallido para %s: %d intentos", username, intentos)
            return intentos

    @staticmethod
    def bloquear_cuenta(username: str, hasta: datetime) -> None:
        """Bloquea la cuenta de un usuario hasta una fecha/hora específica.

        Args:
            username: Nombre de usuario.
            hasta: Fecha/hora hasta la que estará bloqueada.
        """
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET bloqueado_hasta = ? WHERE username = ?",
                (hasta.strftime("%Y-%m-%d %H:%M:%S"), username.strip().lower()),
            )
            logger.warning("Cuenta bloqueada: %s hasta %s", username, hasta)

    @staticmethod
    def resetear_intentos(username: str) -> None:
        """Resetea el contador de intentos y desbloquea la cuenta.

        Args:
            username: Nombre de usuario.
        """
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = NULL "
                "WHERE username = ?",
                (username.strip().lower(),),
            )

    @staticmethod
    def listar_todos(incluir_inactivos: bool = False) -> list[dict]:
        """Lista todos los usuarios del sistema.

        Args:
            incluir_inactivos: Si True, incluye usuarios desactivados.

        Returns:
            Lista de diccionarios con datos de usuarios.
        """
        with get_connection() as conn:
            query = (
                "SELECT id, username, nombre_completo, rol, activo, "
                "ultimo_acceso, fecha_creacion FROM usuarios"
            )
            if not incluir_inactivos:
                query += " WHERE activo = 1"
            query += " ORDER BY nombre_completo"
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def existe_username(username: str) -> bool:
        """Verifica si un nombre de usuario ya existe.

        Args:
            username: Nombre de usuario a verificar.

        Returns:
            True si existe, False si no.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM usuarios WHERE username = ?",
                (username.strip().lower(),),
            )
            return cursor.fetchone()["count"] > 0

    @staticmethod
    def actualizar(
        user_id: int,
        nombre_completo: str | None = None,
        rol: str | None = None,
        activo: bool | None = None,
        password_hash: str | None = None,
    ) -> bool:
        """Actualiza los datos de un usuario.

        Args:
            user_id: ID del usuario a actualizar.
            nombre_completo: Nuevo nombre completo.
            rol: Nuevo rol.
            activo: Nuevo estado activo/inactivo.
            password_hash: Nuevo hash de contraseña.

        Returns:
            True si se actualizó al menos un registro.
        """
        campos: list[str] = []
        valores: list = []

        if nombre_completo is not None:
            campos.append("nombre_completo = ?")
            valores.append(nombre_completo.strip())
        if rol is not None:
            campos.append("rol = ?")
            valores.append(rol)
        if activo is not None:
            campos.append("activo = ?")
            valores.append(1 if activo else 0)
        if password_hash is not None:
            campos.append("password_hash = ?")
            valores.append(password_hash)

        if not campos:
            return False

        valores.append(user_id)
        query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?"

        with get_transaction() as conn:
            cursor = conn.execute(query, valores)
            updated = cursor.rowcount > 0
            if updated:
                logger.info("Usuario ID %d actualizado: %s", user_id, ", ".join(campos))
            return updated
