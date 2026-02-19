"""Modelo y DAO de Usuario para S.C.A.H. v2."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from config.database import get_connection, get_transaction
from config.settings import ROLES_USUARIO
from utils.logger import get_logger

logger = get_logger("models.usuario")


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
        if v not in ROLES_USUARIO:
            raise ValueError(f"Rol inválido. Permitidos: {', '.join(ROLES_USUARIO)}")
        return v

    @field_validator("username")
    @classmethod
    def validar_username(cls, v: str) -> str:
        return v.strip().lower()


class UsuarioDAO:
    """Operaciones de base de datos para la tabla 'usuarios'."""

    @staticmethod
    def crear(username: str, password_hash: str, nombre_completo: str, rol: str = "operador") -> int:
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
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM usuarios WHERE username = ?",
                (username.strip().lower(),),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def obtener_por_id(user_id: int) -> Optional[dict]:
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def actualizar_ultimo_acceso(username: str) -> None:
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE username = ?",
                (username.strip().lower(),),
            )

    @staticmethod
    def incrementar_intentos_fallidos(username: str) -> int:
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET intentos_fallidos = intentos_fallidos + 1 WHERE username = ?",
                (username.strip().lower(),),
            )
            cursor = conn.execute(
                "SELECT intentos_fallidos FROM usuarios WHERE username = ?",
                (username.strip().lower(),),
            )
            row = cursor.fetchone()
            return row["intentos_fallidos"] if row else 0

    @staticmethod
    def bloquear_cuenta(username: str, hasta: datetime) -> None:
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET bloqueado_hasta = ? WHERE username = ?",
                (hasta.strftime("%Y-%m-%d %H:%M:%S"), username.strip().lower()),
            )

    @staticmethod
    def resetear_intentos(username: str) -> None:
        with get_transaction() as conn:
            conn.execute(
                "UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE username = ?",
                (username.strip().lower(),),
            )

    @staticmethod
    def listar_todos(incluir_inactivos: bool = False) -> list[dict]:
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
        with get_transaction() as conn:
            cursor = conn.execute(
                f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?", valores
            )
            return cursor.rowcount > 0
