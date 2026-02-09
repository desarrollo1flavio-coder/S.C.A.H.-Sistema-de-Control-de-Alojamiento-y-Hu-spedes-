"""Modelo y DAO de Huésped para S.C.A.H.

Define el modelo Pydantic para validación y las operaciones
de base de datos para la tabla 'huespedes'.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from config.database import get_connection, get_transaction
from config.settings import PAGINATION_SIZE
from utils.logger import get_logger
from utils.validators import sanitizar_texto

logger = get_logger("models.huesped")


# ============================================================
# MODELO PYDANTIC
# ============================================================
class HuespedSchema(BaseModel):
    """Esquema de validación para datos de huésped."""

    nacionalidad: str = Field(..., min_length=2, max_length=100)
    procedencia: str = Field(..., min_length=2, max_length=200)
    apellido: str = Field(..., min_length=2, max_length=100)
    nombre: str = Field(..., min_length=2, max_length=100)
    dni: Optional[str] = Field(default=None, max_length=8)
    pasaporte: Optional[str] = Field(default=None, max_length=15)
    edad: Optional[int] = Field(default=None, gt=0, lt=150)
    fecha_nacimiento: Optional[date] = None
    profesion: Optional[str] = Field(default=None, max_length=100)
    establecimiento: Optional[str] = Field(default=None, max_length=150)
    habitacion: Optional[str] = Field(default="S/N", max_length=20)
    destino: Optional[str] = Field(default=None, max_length=200)
    vehiculo_tiene: bool = Field(default=False)
    vehiculo_datos: Optional[str] = Field(default=None, max_length=200)
    telefono: Optional[str] = Field(default=None, max_length=30)
    fecha_entrada: date
    fecha_salida: Optional[date] = None
    usuario_carga: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validar_documento(self) -> "HuespedSchema":
        """Valida que al menos uno de DNI o Pasaporte esté presente."""
        if not self.dni and not self.pasaporte:
            raise ValueError("Debe ingresar al menos DNI o Pasaporte")
        return self

    @model_validator(mode="after")
    def validar_fechas(self) -> "HuespedSchema":
        """Valida que la fecha de salida no sea anterior a la de entrada."""
        if self.fecha_salida and self.fecha_salida < self.fecha_entrada:
            raise ValueError("La fecha de salida no puede ser anterior a la de entrada")
        return self

    @field_validator("apellido", "nombre", "nacionalidad", "procedencia")
    @classmethod
    def sanitizar(cls, v: str) -> str:
        """Sanitiza y normaliza campos de texto."""
        return sanitizar_texto(v)

    @field_validator("dni")
    @classmethod
    def validar_formato_dni(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato de DNI (7-8 dígitos)."""
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not v.isdigit() or len(v) < 7 or len(v) > 8:
            raise ValueError("El DNI debe tener 7 u 8 dígitos numéricos")
        return v

    @field_validator("pasaporte")
    @classmethod
    def validar_formato_pasaporte(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato de pasaporte (5-15 alfanumérico)."""
        if v is None or not v.strip():
            return None
        v = v.strip().upper()
        if not v.isalnum() or len(v) < 5 or len(v) > 15:
            raise ValueError("El pasaporte debe tener entre 5 y 15 caracteres alfanuméricos")
        return v


# ============================================================
# DAO - DATA ACCESS OBJECT
# ============================================================
class HuespedDAO:
    """Operaciones de base de datos para la tabla 'huespedes'."""

    @staticmethod
    def crear(datos: dict) -> int:
        """Crea un nuevo registro de huésped.

        Args:
            datos: Diccionario con los datos del huésped.

        Returns:
            ID del huésped creado.
        """
        with get_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO huespedes "
                "(nacionalidad, procedencia, apellido, nombre, dni, pasaporte, "
                "edad, fecha_nacimiento, profesion, establecimiento, habitacion, destino, "
                "vehiculo_tiene, vehiculo_datos, telefono, fecha_entrada, fecha_salida, usuario_carga) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datos["nacionalidad"],
                    datos["procedencia"],
                    datos["apellido"],
                    datos["nombre"],
                    datos.get("dni"),
                    datos.get("pasaporte"),
                    datos.get("edad"),
                    str(datos["fecha_nacimiento"]) if datos.get("fecha_nacimiento") else None,
                    datos.get("profesion"),
                    datos.get("establecimiento"),
                    datos.get("habitacion", "S/N"),
                    datos.get("destino"),
                    1 if datos.get("vehiculo_tiene") else 0,
                    datos.get("vehiculo_datos"),
                    datos.get("telefono"),
                    str(datos["fecha_entrada"]),
                    str(datos["fecha_salida"]) if datos.get("fecha_salida") else None,
                    datos["usuario_carga"],
                ),
            )
            huesped_id = cursor.lastrowid
            logger.info(
                "Huésped creado ID %d: %s %s",
                huesped_id,
                datos["apellido"],
                datos["nombre"],
            )
            return huesped_id

    @staticmethod
    def obtener_por_id(huesped_id: int) -> Optional[dict]:
        """Obtiene un huésped por su ID.

        Args:
            huesped_id: ID del huésped.

        Returns:
            Diccionario con datos del huésped o None.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM huespedes WHERE id = ? AND activo = 1",
                (huesped_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def actualizar(huesped_id: int, datos: dict) -> bool:
        """Actualiza los datos de un huésped.

        Args:
            huesped_id: ID del huésped a actualizar.
            datos: Diccionario con los campos a actualizar.

        Returns:
            True si se actualizó el registro.
        """
        campos_permitidos = [
            "nacionalidad", "procedencia", "apellido", "nombre", "dni", "pasaporte",
            "edad", "fecha_nacimiento", "profesion", "establecimiento", "habitacion",
            "destino", "vehiculo_tiene", "vehiculo_datos", "telefono", "fecha_entrada",
            "fecha_salida",
        ]
        campos: list[str] = []
        valores: list = []

        for campo in campos_permitidos:
            if campo in datos:
                valor = datos[campo]
                if campo == "vehiculo_tiene":
                    valor = 1 if valor else 0
                elif campo in ("fecha_entrada", "fecha_salida", "fecha_nacimiento") and valor is not None:
                    valor = str(valor)
                campos.append(f"{campo} = ?")
                valores.append(valor)

        if not campos:
            return False

        valores.append(huesped_id)
        query = f"UPDATE huespedes SET {', '.join(campos)} WHERE id = ? AND activo = 1"

        with get_transaction() as conn:
            cursor = conn.execute(query, valores)
            updated = cursor.rowcount > 0
            if updated:
                logger.info("Huésped ID %d actualizado", huesped_id)
            return updated

    @staticmethod
    def eliminar(huesped_id: int) -> bool:
        """Elimina lógicamente un huésped (soft-delete).

        Args:
            huesped_id: ID del huésped a eliminar.

        Returns:
            True si se desactivó el registro.
        """
        with get_transaction() as conn:
            cursor = conn.execute(
                "UPDATE huespedes SET activo = 0 WHERE id = ? AND activo = 1",
                (huesped_id,),
            )
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("Huésped ID %d desactivado (soft-delete)", huesped_id)
            return deleted

    @staticmethod
    def buscar_por_documento(dni: str | None = None, pasaporte: str | None = None) -> list[dict]:
        """Busca huéspedes por DNI o pasaporte.

        Args:
            dni: Número de DNI a buscar.
            pasaporte: Número de pasaporte a buscar.

        Returns:
            Lista de huéspedes encontrados.
        """
        with get_connection() as conn:
            conditions: list[str] = ["activo = 1"]
            params: list = []

            if dni:
                conditions.append("dni = ?")
                params.append(dni.strip())
            if pasaporte:
                conditions.append("pasaporte = ?")
                params.append(pasaporte.strip())

            if len(conditions) == 1:
                return []

            where = " OR ".join(conditions[1:])
            query = f"SELECT * FROM huespedes WHERE activo = 1 AND ({where}) ORDER BY fecha_entrada DESC"
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def buscar_rapida(
        termino: str,
        campo: Optional[str] = None,
        limite: int = PAGINATION_SIZE,
    ) -> list[dict]:
        """Búsqueda rápida en uno o varios campos.

        Args:
            termino: Texto a buscar.
            campo: Campo específico (dni, pasaporte, apellido, nombre, nacionalidad,
                   establecimiento, habitacion). Si es None, busca en todos.
            limite: Máximo de resultados.

        Returns:
            Lista de huéspedes que coinciden.
        """
        if not termino or not termino.strip():
            return []

        termino_like = f"%{termino.strip()}%"
        with get_connection() as conn:
            if campo and campo in (
                "dni", "pasaporte", "apellido", "nombre",
                "nacionalidad", "establecimiento", "habitacion",
            ):
                # Búsqueda en campo específico
                query = f"SELECT * FROM huespedes WHERE activo = 1 AND {campo} LIKE ? ORDER BY fecha_entrada DESC LIMIT ?"
                cursor = conn.execute(query, (termino_like, limite))
            else:
                # Búsqueda en todos los campos principales
                cursor = conn.execute(
                    "SELECT * FROM huespedes WHERE activo = 1 AND ("
                    "dni LIKE ? OR pasaporte LIKE ? OR apellido LIKE ? OR nombre LIKE ?"
                    ") ORDER BY fecha_entrada DESC LIMIT ?",
                    (termino_like, termino_like, termino_like, termino_like, limite),
                )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def buscar_avanzada(
        filtros: dict,
        operador: str = "AND",
        pagina: int = 1,
        por_pagina: int = PAGINATION_SIZE,
    ) -> tuple[list[dict], int]:
        """Búsqueda avanzada con múltiples filtros.

        Args:
            filtros: Diccionario con filtros (fecha_desde, fecha_hasta,
                     nacionalidad, procedencia, edad_min, edad_max).
            operador: 'AND' o 'OR' para combinar filtros.
            pagina: Número de página (1-based).
            por_pagina: Registros por página.

        Returns:
            Tupla (lista_resultados, total_registros).
        """
        conditions: list[str] = []
        params: list = []

        if filtros.get("fecha_desde"):
            conditions.append("fecha_entrada >= ?")
            params.append(str(filtros["fecha_desde"]))
        if filtros.get("fecha_hasta"):
            conditions.append("fecha_entrada <= ?")
            params.append(str(filtros["fecha_hasta"]))
        if filtros.get("nacionalidad"):
            conditions.append("nacionalidad = ?")
            params.append(filtros["nacionalidad"])
        if filtros.get("procedencia"):
            conditions.append("procedencia LIKE ?")
            params.append(f"%{filtros['procedencia']}%")
        if filtros.get("edad_min"):
            conditions.append("edad >= ?")
            params.append(int(filtros["edad_min"]))
        if filtros.get("edad_max"):
            conditions.append("edad <= ?")
            params.append(int(filtros["edad_max"]))
        if filtros.get("apellido"):
            conditions.append("apellido LIKE ?")
            params.append(f"%{filtros['apellido']}%")

        where_base = "activo = 1"
        if conditions:
            joiner = f" {operador} "
            where_base += f" AND ({joiner.join(conditions)})"

        with get_connection() as conn:
            # Contar total
            count_query = f"SELECT COUNT(*) as total FROM huespedes WHERE {where_base}"
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()["total"]

            # Obtener página
            offset = (pagina - 1) * por_pagina
            data_query = (
                f"SELECT * FROM huespedes WHERE {where_base} "
                f"ORDER BY fecha_entrada DESC LIMIT ? OFFSET ?"
            )
            cursor = conn.execute(data_query, params + [por_pagina, offset])
            resultados = [dict(row) for row in cursor.fetchall()]

            return resultados, total

    @staticmethod
    def contar_total(solo_activos: bool = True) -> int:
        """Cuenta el total de registros de huéspedes.

        Args:
            solo_activos: Si True, cuenta solo registros activos.

        Returns:
            Número total de registros.
        """
        with get_connection() as conn:
            query = "SELECT COUNT(*) as total FROM huespedes"
            if solo_activos:
                query += " WHERE activo = 1"
            cursor = conn.execute(query)
            return cursor.fetchone()["total"]

    @staticmethod
    def crear_masivo(lista_datos: list[dict]) -> tuple[int, list[dict]]:
        """Inserta múltiples huéspedes en una sola transacción.

        Args:
            lista_datos: Lista de diccionarios con datos de huéspedes.

        Returns:
            Tupla (cantidad_insertados, lista_errores).
        """
        insertados = 0
        errores: list[dict] = []

        with get_transaction() as conn:
            for i, datos in enumerate(lista_datos):
                try:
                    conn.execute(
                        "INSERT INTO huespedes "
                        "(nacionalidad, procedencia, apellido, nombre, dni, pasaporte, "
                        "edad, fecha_nacimiento, profesion, establecimiento, habitacion, "
                        "destino, vehiculo_tiene, vehiculo_datos, telefono, fecha_entrada, "
                        "fecha_salida, usuario_carga) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            datos["nacionalidad"],
                            datos["procedencia"],
                            datos["apellido"],
                            datos["nombre"],
                            datos.get("dni"),
                            datos.get("pasaporte"),
                            datos.get("edad"),
                            str(datos["fecha_nacimiento"]) if datos.get("fecha_nacimiento") else None,
                            datos.get("profesion"),
                            datos.get("establecimiento"),
                            datos.get("habitacion", "S/N"),
                            datos.get("destino"),
                            1 if datos.get("vehiculo_tiene") else 0,
                            datos.get("vehiculo_datos"),
                            datos.get("telefono"),
                            str(datos["fecha_entrada"]),
                            str(datos["fecha_salida"]) if datos.get("fecha_salida") else None,
                            datos["usuario_carga"],
                        ),
                    )
                    insertados += 1
                except Exception as e:
                    errores.append({"fila": i + 1, "error": str(e), "datos": datos})
                    logger.warning("Error al insertar fila %d: %s", i + 1, e)

        logger.info("Importación masiva: %d insertados, %d errores", insertados, len(errores))
        return insertados, errores
