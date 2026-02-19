"""Modelo y DAO de Estadía para S.C.A.H. v2.

Cada estadía representa una visita/check-in de una persona en un establecimiento.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from config.database import get_connection, get_transaction
from config.settings import PAGINATION_SIZE
from utils.logger import get_logger

logger = get_logger("models.estadia")


class EstadiaSchema(BaseModel):
    """Esquema de validación para datos de estadía."""

    persona_id: int
    establecimiento: Optional[str] = Field(default=None, max_length=150)
    habitacion: Optional[str] = Field(default="S/N", max_length=20)
    edad: Optional[int] = Field(default=None, gt=0, lt=150)
    fecha_entrada: date
    fecha_salida: Optional[date] = None
    destino: Optional[str] = Field(default=None, max_length=200)
    vehiculo_tiene: bool = Field(default=False)
    vehiculo_datos: Optional[str] = Field(default=None, max_length=200)
    usuario_carga: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validar_fechas(self) -> "EstadiaSchema":
        if self.fecha_salida and self.fecha_salida < self.fecha_entrada:
            raise ValueError("La fecha de salida no puede ser anterior a la de entrada")
        return self


class EstadiaDAO:
    """Operaciones de base de datos para la tabla 'estadias'."""

    @staticmethod
    def crear(datos: dict) -> int:
        """Crea un nuevo registro de estadía."""
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO estadias "
                "(persona_id, establecimiento, habitacion, edad, fecha_entrada, "
                "fecha_salida, destino, vehiculo_tiene, vehiculo_datos, usuario_carga) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datos["persona_id"],
                    datos.get("establecimiento"),
                    datos.get("habitacion", "S/N"),
                    datos.get("edad"),
                    str(datos["fecha_entrada"]),
                    str(datos["fecha_salida"]) if datos.get("fecha_salida") else None,
                    datos.get("destino"),
                    1 if datos.get("vehiculo_tiene") else 0,
                    datos.get("vehiculo_datos"),
                    datos["usuario_carga"],
                ),
            )
            estadia_id = cursor.lastrowid
            logger.info("Estadía creada ID %d para persona %d", estadia_id, datos["persona_id"])
            return estadia_id

    @staticmethod
    def obtener_por_id(estadia_id: int) -> Optional[dict]:
        """Obtiene una estadía por su ID."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT e.*, p.apellido, p.nombre, p.dni, p.pasaporte, p.nacionalidad, "
                "p.procedencia, p.fecha_nacimiento, p.profesion, p.telefono "
                "FROM estadias e "
                "JOIN personas p ON e.persona_id = p.id "
                "WHERE e.id = ? AND e.activo = 1",
                (estadia_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def obtener_por_persona(persona_id: int) -> list[dict]:
        """Obtiene todas las estadías de una persona (historial)."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM estadias WHERE persona_id = ? AND activo = 1 "
                "ORDER BY fecha_entrada DESC",
                (persona_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def actualizar(estadia_id: int, datos: dict) -> bool:
        """Actualiza una estadía existente."""
        campos_permitidos = [
            "establecimiento", "habitacion", "edad", "fecha_entrada",
            "fecha_salida", "destino", "vehiculo_tiene", "vehiculo_datos",
        ]
        campos: list[str] = []
        valores: list = []

        for campo in campos_permitidos:
            if campo in datos:
                valor = datos[campo]
                if campo == "vehiculo_tiene":
                    valor = 1 if valor else 0
                elif campo in ("fecha_entrada", "fecha_salida") and valor is not None:
                    valor = str(valor)
                campos.append(f"{campo} = ?")
                valores.append(valor)

        if not campos:
            return False

        valores.append(estadia_id)
        query = f"UPDATE estadias SET {', '.join(campos)} WHERE id = ? AND activo = 1"

        with get_transaction() as conn:
            cursor = conn.execute(query, valores)
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(estadia_id: int) -> bool:
        """Elimina lógicamente una estadía (soft-delete)."""
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE estadias SET activo = 0 WHERE id = ? AND activo = 1",
                (estadia_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def buscar_completa(
        termino: str = "",
        campo: str | None = None,
        filtros: dict | None = None,
        operador: str = "AND",
        pagina: int = 1,
        por_pagina: int = PAGINATION_SIZE,
    ) -> tuple[list[dict], int]:
        """Búsqueda completa uniendo personas y estadías."""
        base = (
            "FROM estadias e "
            "JOIN personas p ON e.persona_id = p.id "
            "WHERE e.activo = 1 AND p.activo = 1"
        )
        conditions: list[str] = []
        params: list = []

        # Búsqueda rápida por término
        if termino and termino.strip():
            t = f"%{termino.strip()}%"
            if campo and campo in ("dni", "pasaporte", "apellido", "nombre", "nacionalidad", "establecimiento"):
                if campo in ("dni", "pasaporte", "apellido", "nombre", "nacionalidad"):
                    conditions.append(f"p.{campo} LIKE ?")
                else:
                    conditions.append(f"e.{campo} LIKE ?")
                params.append(t)
            else:
                conditions.append(
                    "(p.dni LIKE ? OR p.pasaporte LIKE ? OR p.apellido LIKE ? OR p.nombre LIKE ? OR e.establecimiento LIKE ?)"
                )
                params.extend([t, t, t, t, t])

        # Filtros avanzados
        if filtros:
            if filtros.get("fecha_desde"):
                conditions.append("e.fecha_entrada >= ?")
                params.append(str(filtros["fecha_desde"]))
            if filtros.get("fecha_hasta"):
                conditions.append("e.fecha_entrada <= ?")
                params.append(str(filtros["fecha_hasta"]))
            if filtros.get("nacionalidad"):
                conditions.append("p.nacionalidad = ?")
                params.append(filtros["nacionalidad"])
            if filtros.get("procedencia"):
                conditions.append("p.procedencia LIKE ?")
                params.append(f"%{filtros['procedencia']}%")
            if filtros.get("establecimiento"):
                conditions.append("e.establecimiento LIKE ?")
                params.append(f"%{filtros['establecimiento']}%")
            if filtros.get("apellido"):
                conditions.append("p.apellido LIKE ?")
                params.append(f"%{filtros['apellido']}%")
            if filtros.get("nombre"):
                conditions.append("p.nombre LIKE ?")
                params.append(f"%{filtros['nombre']}%")
            if filtros.get("edad_min"):
                conditions.append("e.edad >= ?")
                params.append(int(filtros["edad_min"]))
            if filtros.get("edad_max"):
                conditions.append("e.edad <= ?")
                params.append(int(filtros["edad_max"]))

        if conditions:
            joiner = f" {operador} "
            base += f" AND ({joiner.join(conditions)})"

        with get_connection() as conn:
            count_query = f"SELECT COUNT(*) as total {base}"
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()["total"]

            offset = (pagina - 1) * por_pagina
            data_query = (
                f"SELECT e.*, p.apellido, p.nombre, p.dni, p.pasaporte, "
                f"p.nacionalidad, p.procedencia, p.fecha_nacimiento, p.profesion, p.telefono "
                f"{base} ORDER BY e.fecha_entrada DESC LIMIT ? OFFSET ?"
            )
            cursor = conn.execute(data_query, params + [por_pagina, offset])
            return [dict(row) for row in cursor.fetchall()], total

    @staticmethod
    def contar_total(solo_activos: bool = True) -> int:
        """Cuenta el total de estadías."""
        with get_connection() as conn:
            query = "SELECT COUNT(*) as total FROM estadias"
            if solo_activos:
                query += " WHERE activo = 1"
            cursor = conn.execute(query)
            return cursor.fetchone()["total"]

    @staticmethod
    def contar_activas_hoy() -> int:
        """Cuenta huéspedes hospedados hoy (con check-in y sin check-out)."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as total FROM estadias "
                "WHERE activo = 1 AND fecha_entrada <= date('now') "
                "AND (fecha_salida IS NULL OR fecha_salida >= date('now'))"
            )
            return cursor.fetchone()["total"]

    @staticmethod
    def estadisticas_nacionalidades(limite: int = 10) -> list[dict]:
        """Top nacionalidades de huéspedes."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT p.nacionalidad, COUNT(*) as cantidad "
                "FROM estadias e JOIN personas p ON e.persona_id = p.id "
                "WHERE e.activo = 1 "
                "GROUP BY p.nacionalidad ORDER BY cantidad DESC LIMIT ?",
                (limite,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def estadisticas_establecimientos(limite: int = 10) -> list[dict]:
        """Top establecimientos por cantidad de estadías."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT establecimiento, COUNT(*) as cantidad "
                "FROM estadias WHERE activo = 1 AND establecimiento IS NOT NULL "
                "GROUP BY establecimiento ORDER BY cantidad DESC LIMIT ?",
                (limite,),
            )
            return [dict(row) for row in cursor.fetchall()]
