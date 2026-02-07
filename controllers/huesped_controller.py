"""Controlador de huéspedes para S.C.A.H.

Gestiona CRUD completo de huéspedes con validación Pydantic,
auditoría automática y verificación de permisos.
"""

from typing import Optional

from controllers.auth_controller import SessionInfo
from models.auditoria import AuditoriaDAO
from models.huesped import HuespedDAO, HuespedSchema
from utils.exceptions import DuplicateRecordError, PermissionDeniedError, ValidationError
from utils.logger import get_logger

logger = get_logger("huesped_controller")


class HuespedController:
    """Controlador para operaciones CRUD de huéspedes."""

    def __init__(self, session: SessionInfo) -> None:
        """Inicializa el controlador con la sesión del usuario.

        Args:
            session: Información de la sesión activa.
        """
        self._session = session

    def crear(self, datos: dict) -> int:
        """Crea un nuevo registro de huésped con validación y auditoría.

        Args:
            datos: Diccionario con los datos del huésped.

        Returns:
            ID del huésped creado.

        Raises:
            ValidationError: Si los datos no son válidos.
            DuplicateRecordError: Si el DNI o pasaporte ya existe.
            PermissionDeniedError: Si el usuario no tiene permisos.
        """
        if not self._session.tiene_permiso("escritura"):
            raise PermissionDeniedError()

        # Agregar usuario que carga
        datos["usuario_carga"] = self._session.username

        # Validar con Pydantic
        try:
            schema = HuespedSchema(**datos)
            datos_validados = schema.model_dump()
        except Exception as e:
            logger.warning("Validación fallida al crear huésped: %s", e)
            raise ValidationError(str(e)) from e

        # Verificar duplicados
        existentes = HuespedDAO.buscar_por_documento(
            dni=datos_validados.get("dni"),
            pasaporte=datos_validados.get("pasaporte"),
        )
        if existentes:
            doc = datos_validados.get("dni") or datos_validados.get("pasaporte")
            raise DuplicateRecordError(f"Ya existe un huésped con documento {doc}")

        # Crear registro
        huesped_id = HuespedDAO.crear(datos_validados)

        # Auditoría
        AuditoriaDAO.registrar(
            usuario=self._session.username,
            accion="INSERT",
            tabla_afectada="huespedes",
            registro_id=huesped_id,
            datos_nuevos=datos_validados,
        )

        logger.info(
            "Huésped creado por %s: %s %s (ID: %d)",
            self._session.username,
            datos_validados["apellido"],
            datos_validados["nombre"],
            huesped_id,
        )
        return huesped_id

    def obtener(self, huesped_id: int) -> Optional[dict]:
        """Obtiene un huésped por ID.

        Args:
            huesped_id: ID del huésped.

        Returns:
            Diccionario con datos del huésped o None.
        """
        if not self._session.tiene_permiso("lectura"):
            raise PermissionDeniedError()
        return HuespedDAO.obtener_por_id(huesped_id)

    def actualizar(self, huesped_id: int, datos: dict) -> bool:
        """Actualiza un huésped con validación y auditoría.

        Args:
            huesped_id: ID del huésped a actualizar.
            datos: Diccionario con los campos a actualizar.

        Returns:
            True si se actualizó el registro.
        """
        if not self._session.tiene_permiso("escritura"):
            raise PermissionDeniedError()

        # Obtener datos anteriores para auditoría
        datos_anteriores = HuespedDAO.obtener_por_id(huesped_id)
        if not datos_anteriores:
            raise ValidationError("Huésped no encontrado", field="id")

        # Actualizar
        resultado = HuespedDAO.actualizar(huesped_id, datos)

        if resultado:
            AuditoriaDAO.registrar(
                usuario=self._session.username,
                accion="UPDATE",
                tabla_afectada="huespedes",
                registro_id=huesped_id,
                datos_anteriores=datos_anteriores,
                datos_nuevos=datos,
            )
            logger.info("Huésped ID %d actualizado por %s", huesped_id, self._session.username)

        return resultado

    def eliminar(self, huesped_id: int) -> bool:
        """Elimina lógicamente un huésped (soft-delete).

        Args:
            huesped_id: ID del huésped a eliminar.

        Returns:
            True si se desactivó el registro.
        """
        if not self._session.tiene_permiso("eliminar"):
            raise PermissionDeniedError("No tiene permisos para eliminar registros")

        datos_anteriores = HuespedDAO.obtener_por_id(huesped_id)
        if not datos_anteriores:
            raise ValidationError("Huésped no encontrado", field="id")

        resultado = HuespedDAO.eliminar(huesped_id)

        if resultado:
            AuditoriaDAO.registrar(
                usuario=self._session.username,
                accion="DELETE",
                tabla_afectada="huespedes",
                registro_id=huesped_id,
                datos_anteriores=datos_anteriores,
                detalles="Eliminación lógica (soft-delete)",
            )
            logger.info("Huésped ID %d eliminado por %s", huesped_id, self._session.username)

        return resultado

    def buscar_rapida(self, termino: str) -> list[dict]:
        """Búsqueda rápida en DNI, pasaporte, apellido y nombre.

        Args:
            termino: Texto a buscar.

        Returns:
            Lista de huéspedes encontrados.
        """
        if not self._session.tiene_permiso("lectura"):
            raise PermissionDeniedError()
        return HuespedDAO.buscar_rapida(termino)

    def buscar_avanzada(
        self,
        filtros: dict,
        operador: str = "AND",
        pagina: int = 1,
        por_pagina: int = 50,
    ) -> tuple[list[dict], int]:
        """Búsqueda avanzada con filtros combinables.

        Args:
            filtros: Diccionario con filtros.
            operador: 'AND' o 'OR'.
            pagina: Número de página.
            por_pagina: Registros por página.

        Returns:
            Tupla (resultados, total).
        """
        if not self._session.tiene_permiso("lectura"):
            raise PermissionDeniedError()
        return HuespedDAO.buscar_avanzada(filtros, operador, pagina, por_pagina)

    def contar_total(self) -> int:
        """Cuenta el total de huéspedes activos.

        Returns:
            Número total de registros activos.
        """
        return HuespedDAO.contar_total()
