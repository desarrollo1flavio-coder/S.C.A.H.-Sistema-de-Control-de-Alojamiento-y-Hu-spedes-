"""Modelo y DAO de Persona para S.C.A.H. v2.

Almacena datos fijos de una persona (separado de sus estadías).
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from config.database import get_connection, get_transaction
from config.settings import PAGINATION_SIZE
from utils.logger import get_logger
from utils.validators import sanitizar_texto, limpiar_dni

logger = get_logger("models.persona")


class PersonaSchema(BaseModel):
    """Esquema de validación para datos de persona."""

    nacionalidad: str = Field(..., min_length=2, max_length=100)
    procedencia: str = Field(..., min_length=2, max_length=200)
    apellido: str = Field(..., min_length=1, max_length=100)
    nombre: str = Field(..., min_length=1, max_length=100)
    dni: Optional[str] = Field(default=None, max_length=8)
    pasaporte: Optional[str] = Field(default=None, max_length=15)
    fecha_nacimiento: Optional[date] = None
    profesion: Optional[str] = Field(default=None, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=30)

    @model_validator(mode="after")
    def validar_documento(self) -> "PersonaSchema":
        if not self.dni and not self.pasaporte:
            raise ValueError("Debe ingresar al menos DNI o Pasaporte")
        return self

    @field_validator("apellido", "nombre", "nacionalidad", "procedencia")
    @classmethod
    def sanitizar(cls, v: str) -> str:
        return sanitizar_texto(v)

    @field_validator("dni")
    @classmethod
    def validar_formato_dni(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = limpiar_dni(v)
        if not v.isdigit() or len(v) < 7 or len(v) > 8:
            raise ValueError("El DNI debe tener 7 u 8 dígitos numéricos")
        return v

    @field_validator("pasaporte")
    @classmethod
    def validar_formato_pasaporte(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip().upper()
        if not v.isalnum() or len(v) < 5 or len(v) > 15:
            raise ValueError("El pasaporte debe tener entre 5 y 15 caracteres alfanuméricos")
        return v


class PersonaDAO:
    """Operaciones de base de datos para la tabla 'personas'."""

    @staticmethod
    def crear(datos: dict) -> int:
        """Crea un nuevo registro de persona."""
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO personas "
                "(nacionalidad, procedencia, apellido, nombre, dni, pasaporte, "
                "fecha_nacimiento, profesion, telefono) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datos["nacionalidad"],
                    datos["procedencia"],
                    datos["apellido"],
                    datos["nombre"],
                    datos.get("dni"),
                    datos.get("pasaporte"),
                    str(datos["fecha_nacimiento"]) if datos.get("fecha_nacimiento") else None,
                    datos.get("profesion"),
                    datos.get("telefono"),
                ),
            )
            persona_id = cursor.lastrowid
            logger.info("Persona creada ID %d: %s %s", persona_id, datos["apellido"], datos["nombre"])
            return persona_id

    @staticmethod
    def obtener_por_id(persona_id: int) -> Optional[dict]:
        """Obtiene una persona por su ID."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM personas WHERE id = ? AND activo = 1",
                (persona_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def buscar_por_documento(dni: str | None = None, pasaporte: str | None = None) -> Optional[dict]:
        """Busca una persona por DNI o pasaporte. Retorna la primera coincidencia."""
        with get_connection() as conn:
            if dni:
                cursor = conn.execute(
                    "SELECT * FROM personas WHERE dni = ? AND activo = 1", (dni.strip(),)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
            if pasaporte:
                cursor = conn.execute(
                    "SELECT * FROM personas WHERE pasaporte = ? AND activo = 1",
                    (pasaporte.strip(),),
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
        return None

    @staticmethod
    def actualizar(persona_id: int, datos: dict) -> bool:
        """Actualiza los datos de una persona."""
        campos_permitidos = [
            "nacionalidad", "procedencia", "apellido", "nombre", "dni", "pasaporte",
            "fecha_nacimiento", "profesion", "telefono",
        ]
        campos: list[str] = []
        valores: list = []

        for campo in campos_permitidos:
            if campo in datos:
                valor = datos[campo]
                if campo == "fecha_nacimiento" and valor is not None:
                    valor = str(valor)
                campos.append(f"{campo} = ?")
                valores.append(valor)

        if not campos:
            return False

        valores.append(persona_id)
        query = f"UPDATE personas SET {', '.join(campos)} WHERE id = ? AND activo = 1"

        with get_transaction() as conn:
            cursor = conn.execute(query, valores)
            return cursor.rowcount > 0

    @staticmethod
    def eliminar(persona_id: int) -> bool:
        """Elimina lógicamente una persona (soft-delete)."""
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE personas SET activo = 0 WHERE id = ? AND activo = 1",
                (persona_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def buscar_rapida(
        termino: str,
        campo: Optional[str] = None,
        limite: int = PAGINATION_SIZE,
    ) -> list[dict]:
        """Búsqueda rápida en uno o varios campos."""
        if not termino or not termino.strip():
            return []

        termino_like = f"%{termino.strip()}%"
        with get_connection() as conn:
            if campo and campo in ("dni", "pasaporte", "apellido", "nombre", "nacionalidad"):
                query = f"SELECT * FROM personas WHERE activo = 1 AND {campo} LIKE ? ORDER BY apellido LIMIT ?"
                cursor = conn.execute(query, (termino_like, limite))
            else:
                cursor = conn.execute(
                    "SELECT * FROM personas WHERE activo = 1 AND ("
                    "dni LIKE ? OR pasaporte LIKE ? OR apellido LIKE ? OR nombre LIKE ?"
                    ") ORDER BY apellido LIMIT ?",
                    (termino_like, termino_like, termino_like, termino_like, limite),
                )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def contar_total(solo_activos: bool = True) -> int:
        """Cuenta el total de personas."""
        with get_connection() as conn:
            query = "SELECT COUNT(*) as total FROM personas"
            if solo_activos:
                query += " WHERE activo = 1"
            cursor = conn.execute(query)
            return cursor.fetchone()["total"]

    @staticmethod
    def listar(pagina: int = 1, por_pagina: int = PAGINATION_SIZE) -> tuple[list[dict], int]:
        """Lista personas con paginación."""
        with get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as total FROM personas WHERE activo = 1")
            total = cursor.fetchone()["total"]
            offset = (pagina - 1) * por_pagina
            cursor = conn.execute(
                "SELECT * FROM personas WHERE activo = 1 ORDER BY apellido, nombre LIMIT ? OFFSET ?",
                (por_pagina, offset),
            )
            return [dict(row) for row in cursor.fetchall()], total
