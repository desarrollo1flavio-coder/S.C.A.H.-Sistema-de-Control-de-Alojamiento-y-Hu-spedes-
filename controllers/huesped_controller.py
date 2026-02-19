"""Controlador de compatibilidad — wrapper sobre persona + estadia."""

from controllers.persona_controller import PersonaController
from controllers.estadia_controller import EstadiaController
from utils.logger import get_logger

logger = get_logger("huesped_controller")


class HuespedController:
    """Wrapper de compatibilidad. Los métodos delegan a PersonaController + EstadiaController."""

    def __init__(self, usuario: str = "sistema"):
        self.usuario = usuario
        self.persona_ctrl = PersonaController(usuario)
        self.estadia_ctrl = EstadiaController(usuario)

    def buscar_rapida(self, termino: str, campo: str | None = None, limite: int = 50):
        resultados, _ = self.estadia_ctrl.buscar(termino=termino, campo=campo, por_pagina=limite)
        return resultados
