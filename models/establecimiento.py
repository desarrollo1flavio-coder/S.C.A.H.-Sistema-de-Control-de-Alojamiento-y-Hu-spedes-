"""Modelo y DAO de Establecimiento para S.C.A.H. v2."""

from typing import Optional
from pydantic import BaseModel, Field

from config.database import get_connection, get_transaction
from utils.logger import get_logger

logger = get_logger("models.establecimiento")


class EstablecimientoSchema(BaseModel):
    """Esquema de validación para datos de establecimiento."""
    nombre: str = Field(..., min_length=2, max_length=150)
    direccion: Optional[str] = Field(default=None, max_length=300)
    telefono: Optional[str] = Field(default=None, max_length=30)


class EstablecimientoDAO:
    """Operaciones de base de datos para la tabla 'establecimientos'."""

    @staticmethod
    def crear(datos: dict) -> int:
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO establecimientos (nombre, direccion, telefono) VALUES (?, ?, ?)",
                (datos["nombre"], datos.get("direccion"), datos.get("telefono")),
            )
            est_id = cursor.lastrowid
            logger.info("Establecimiento creado ID %d: %s", est_id, datos["nombre"])
            return est_id

    @staticmethod
    def obtener_por_id(est_id: int) -> Optional[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM establecimientos WHERE id = ? AND activo = 1", (est_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def obtener_por_nombre(nombre: str) -> Optional[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM establecimientos WHERE nombre = ? COLLATE NOCASE AND activo = 1",
                (nombre.strip(),),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def obtener_o_crear(nombre: str) -> int:
        """Obtiene el ID de un establecimiento por nombre, o lo crea si no existe."""
        existente = EstablecimientoDAO.obtener_por_nombre(nombre)
        if existente:
            return existente["id"]
        return EstablecimientoDAO.crear({"nombre": nombre.strip()})

    @staticmethod
    def listar(incluir_inactivos: bool = False) -> list[dict]:
        with get_connection() as conn:
            query = "SELECT * FROM establecimientos"
            if not incluir_inactivos:
                query += " WHERE activo = 1"
            query += " ORDER BY nombre"
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def actualizar(est_id: int, datos: dict) -> bool:
        campos: list[str] = []
        valores: list = []
        for campo in ("nombre", "direccion", "telefono"):
            if campo in datos:
                campos.append(f"{campo} = ?")
                valores.append(datos[campo])
        if not campos:
            return False
        valores.append(est_id)
        with get_transaction() as conn:
            cursor = conn.execute(
                f"UPDATE establecimientos SET {', '.join(campos)} WHERE id = ? AND activo = 1",
                valores,
            )
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(est_id: int) -> bool:
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE establecimientos SET activo = 0 WHERE id = ? AND activo = 1",
                (est_id,),
            )
            return cursor.rowcount > 0
