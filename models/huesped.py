"""Modelo de compatibilidad: wrapper sobre persona + estadia para S.C.A.H. v2.

Mantiene la interfaz HuespedDAO para código que aún la use,
pero delega a PersonaDAO + EstadiaDAO internamente.
"""

from typing import Optional

from config.database import get_connection
from config.settings import PAGINATION_SIZE
from utils.logger import get_logger

logger = get_logger("models.huesped")


class HuespedDAO:
    """Wrapper de compatibilidad para consultas que unan personas + estadias."""

    @staticmethod
    def buscar_rapida(
        termino: str,
        campo: Optional[str] = None,
        limite: int = PAGINATION_SIZE,
    ) -> list[dict]:
        """Búsqueda rápida uniendo personas y estadías."""
        if not termino or not termino.strip():
            return []
        termino_like = f"%{termino.strip()}%"
        with get_connection() as conn:
            if campo and campo in ("dni", "pasaporte", "apellido", "nombre", "nacionalidad"):
                query = (
                    f"SELECT e.*, p.apellido, p.nombre, p.dni, p.pasaporte, "
                    f"p.nacionalidad, p.procedencia, p.fecha_nacimiento, p.profesion, p.telefono "
                    f"FROM estadias e JOIN personas p ON e.persona_id = p.id "
                    f"WHERE e.activo = 1 AND p.activo = 1 AND p.{campo} LIKE ? "
                    f"ORDER BY e.fecha_entrada DESC LIMIT ?"
                )
                cursor = conn.execute(query, (termino_like, limite))
            else:
                cursor = conn.execute(
                    "SELECT e.*, p.apellido, p.nombre, p.dni, p.pasaporte, "
                    "p.nacionalidad, p.procedencia, p.fecha_nacimiento, p.profesion, p.telefono "
                    "FROM estadias e JOIN personas p ON e.persona_id = p.id "
                    "WHERE e.activo = 1 AND p.activo = 1 AND ("
                    "p.dni LIKE ? OR p.pasaporte LIKE ? OR p.apellido LIKE ? OR p.nombre LIKE ?"
                    ") ORDER BY e.fecha_entrada DESC LIMIT ?",
                    (termino_like, termino_like, termino_like, termino_like, limite),
                )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def contar_total(solo_activos: bool = True) -> int:
        with get_connection() as conn:
            query = "SELECT COUNT(*) as total FROM estadias"
            if solo_activos:
                query += " WHERE activo = 1"
            cursor = conn.execute(query)
            return cursor.fetchone()["total"]
