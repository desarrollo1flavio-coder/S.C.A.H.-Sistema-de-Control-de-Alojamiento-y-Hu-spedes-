"""Modelo y DAO de Habitación para S.C.A.H. v2."""

from typing import Optional
from pydantic import BaseModel, Field

from config.database import get_connection, get_transaction
from utils.logger import get_logger

logger = get_logger("models.habitacion")


class HabitacionSchema(BaseModel):
    """Esquema de validación para datos de habitación."""
    establecimiento_id: int
    numero: str = Field(..., min_length=1, max_length=20)
    tipo: str = Field(default="standard", max_length=50)
    capacidad: int = Field(default=2, gt=0, le=20)
    estado: str = Field(default="disponible")


class HabitacionDAO:
    """Operaciones de base de datos para la tabla 'habitaciones'."""

    @staticmethod
    def crear(datos: dict) -> int:
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO habitaciones "
                "(establecimiento_id, numero, tipo, capacidad, estado) "
                "VALUES (?, ?, ?, ?, ?)",
                (datos["establecimiento_id"], datos["numero"],
                 datos.get("tipo", "standard"), datos.get("capacidad", 2),
                 datos.get("estado", "disponible")),
            )
            hab_id = cursor.lastrowid
            logger.info("Habitación creada ID %d: %s", hab_id, datos["numero"])
            return hab_id

    @staticmethod
    def obtener_por_id(hab_id: int) -> Optional[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT h.*, e.nombre as establecimiento_nombre "
                "FROM habitaciones h JOIN establecimientos e ON h.establecimiento_id = e.id "
                "WHERE h.id = ? AND h.activo = 1",
                (hab_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def listar_por_establecimiento(est_id: int) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM habitaciones "
                "WHERE establecimiento_id = ? AND activo = 1 ORDER BY numero",
                (est_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def actualizar_estado(hab_id: int, estado: str) -> bool:
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE habitaciones SET estado = ? WHERE id = ? AND activo = 1",
                (estado, hab_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def actualizar(hab_id: int, datos: dict) -> bool:
        campos: list[str] = []
        valores: list = []
        for campo in ("numero", "tipo", "capacidad", "estado"):
            if campo in datos:
                campos.append(f"{campo} = ?")
                valores.append(datos[campo])
        if not campos:
            return False
        valores.append(hab_id)
        with get_transaction() as conn:
            cursor = conn.execute(
                f"UPDATE habitaciones SET {', '.join(campos)} WHERE id = ? AND activo = 1",
                valores,
            )
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(hab_id: int) -> bool:
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE habitaciones SET activo = 0 WHERE id = ? AND activo = 1",
                (hab_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def contar_por_estado(est_id: int) -> dict[str, int]:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT estado, COUNT(*) as cantidad FROM habitaciones "
                "WHERE establecimiento_id = ? AND activo = 1 GROUP BY estado",
                (est_id,),
            )
            return {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
