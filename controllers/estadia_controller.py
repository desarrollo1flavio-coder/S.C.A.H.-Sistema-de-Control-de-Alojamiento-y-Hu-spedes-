"""Controlador de Estadía para S.C.A.H. v2."""

from pydantic import ValidationError

from models.auditoria import AuditoriaDAO
from models.estadia import EstadiaDAO, EstadiaSchema
from utils.exceptions import ValidationError as AppValidationError
from utils.logger import get_logger

logger = get_logger("estadia_controller")


class EstadiaController:
    """Gestiona operaciones CRUD de estadías."""

    def __init__(self, usuario: str = "sistema"):
        self.usuario = usuario

    def crear(self, datos: dict) -> int:
        """Crea una nueva estadía con validación."""
        datos.setdefault("usuario_carga", self.usuario)
        try:
            schema = EstadiaSchema(**datos)
        except ValidationError as e:
            errores = "; ".join(err["msg"] for err in e.errors())
            raise AppValidationError(errores)

        estadia_id = EstadiaDAO.crear(schema.model_dump())
        AuditoriaDAO.registrar(
            usuario=self.usuario,
            accion="CREAR_ESTADIA",
            tabla_afectada="estadias",
            registro_id=estadia_id,
            datos_nuevos=schema.model_dump(),
        )
        return estadia_id

    def actualizar(self, estadia_id: int, datos: dict) -> bool:
        """Actualiza una estadía existente."""
        anterior = EstadiaDAO.obtener_por_id(estadia_id)
        if not anterior:
            raise AppValidationError("Estadía no encontrada")

        resultado = EstadiaDAO.actualizar(estadia_id, datos)
        if resultado:
            AuditoriaDAO.registrar(
                usuario=self.usuario,
                accion="ACTUALIZAR_ESTADIA",
                tabla_afectada="estadias",
                registro_id=estadia_id,
                datos_anteriores=anterior,
                datos_nuevos=datos,
            )
        return resultado

    def eliminar(self, estadia_id: int) -> bool:
        """Elimina lógicamente una estadía."""
        anterior = EstadiaDAO.obtener_por_id(estadia_id)
        if not anterior:
            raise AppValidationError("Estadía no encontrada")

        resultado = EstadiaDAO.eliminar(estadia_id)
        if resultado:
            AuditoriaDAO.registrar(
                usuario=self.usuario,
                accion="ELIMINAR_ESTADIA",
                tabla_afectada="estadias",
                registro_id=estadia_id,
                datos_anteriores=anterior,
            )
        return resultado

    def buscar(
        self,
        termino: str = "",
        campo: str | None = None,
        filtros: dict | None = None,
        pagina: int = 1,
        por_pagina: int = 50,
    ) -> tuple[list[dict], int]:
        return EstadiaDAO.buscar_completa(termino, campo, filtros, pagina=pagina, por_pagina=por_pagina)

    def historial_persona(self, persona_id: int) -> list[dict]:
        return EstadiaDAO.obtener_por_persona(persona_id)
