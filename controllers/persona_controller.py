"""Controlador de Persona para S.C.A.H. v2."""

from pydantic import ValidationError

from models.auditoria import AuditoriaDAO
from models.persona import PersonaDAO, PersonaSchema
from utils.exceptions import DuplicateRecordError, ValidationError as AppValidationError
from utils.logger import get_logger

logger = get_logger("persona_controller")


class PersonaController:
    """Gestiona operaciones CRUD de personas."""

    def __init__(self, usuario: str = "sistema"):
        self.usuario = usuario

    def crear(self, datos: dict) -> int:
        """Crea una nueva persona con validación."""
        try:
            schema = PersonaSchema(**datos)
        except ValidationError as e:
            errores = "; ".join(err["msg"] for err in e.errors())
            raise AppValidationError(errores)

        # Verificar duplicado por documento
        existente = PersonaDAO.buscar_por_documento(
            dni=schema.dni, pasaporte=schema.pasaporte
        )
        if existente:
            raise DuplicateRecordError(
                f"Ya existe una persona con ese documento (ID: {existente['id']})"
            )

        persona_id = PersonaDAO.crear(schema.model_dump())
        AuditoriaDAO.registrar(
            usuario=self.usuario,
            accion="CREAR_PERSONA",
            tabla_afectada="personas",
            registro_id=persona_id,
            datos_nuevos=schema.model_dump(),
        )
        return persona_id

    def obtener_o_crear(self, datos: dict) -> int:
        """Obtiene una persona existente por documento, o la crea si no existe.
        Usado durante importación masiva."""
        dni = datos.get("dni")
        pasaporte = datos.get("pasaporte")

        existente = PersonaDAO.buscar_por_documento(dni=dni, pasaporte=pasaporte)
        if existente:
            return existente["id"]

        try:
            schema = PersonaSchema(**datos)
        except ValidationError:
            # Mínimo para crear: relajar validación
            datos_min = {
                "nacionalidad": datos.get("nacionalidad", "Argentina"),
                "procedencia": datos.get("procedencia", "S/D"),
                "apellido": datos.get("apellido", "S/D"),
                "nombre": datos.get("nombre", "S/D"),
                "dni": dni,
                "pasaporte": pasaporte,
                "fecha_nacimiento": datos.get("fecha_nacimiento"),
                "profesion": datos.get("profesion"),
                "telefono": datos.get("telefono"),
            }
            schema = PersonaSchema(**datos_min)

        return PersonaDAO.crear(schema.model_dump())

    def actualizar(self, persona_id: int, datos: dict) -> bool:
        """Actualiza los datos de una persona."""
        anterior = PersonaDAO.obtener_por_id(persona_id)
        if not anterior:
            raise AppValidationError("Persona no encontrada")

        resultado = PersonaDAO.actualizar(persona_id, datos)
        if resultado:
            AuditoriaDAO.registrar(
                usuario=self.usuario,
                accion="ACTUALIZAR_PERSONA",
                tabla_afectada="personas",
                registro_id=persona_id,
                datos_anteriores=anterior,
                datos_nuevos=datos,
            )
        return resultado

    def eliminar(self, persona_id: int) -> bool:
        """Elimina lógicamente una persona."""
        anterior = PersonaDAO.obtener_por_id(persona_id)
        if not anterior:
            raise AppValidationError("Persona no encontrada")

        resultado = PersonaDAO.eliminar(persona_id)
        if resultado:
            AuditoriaDAO.registrar(
                usuario=self.usuario,
                accion="ELIMINAR_PERSONA",
                tabla_afectada="personas",
                registro_id=persona_id,
                datos_anteriores=anterior,
            )
        return resultado

    def buscar(self, termino: str, campo: str | None = None, limite: int = 50) -> list[dict]:
        return PersonaDAO.buscar_rapida(termino, campo, limite)
