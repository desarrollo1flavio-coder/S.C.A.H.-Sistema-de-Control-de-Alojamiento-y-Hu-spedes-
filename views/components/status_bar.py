"""Barra de estado reutilizable para el dashboard de S.C.A.H.

Muestra el usuario actual, rol, reloj en tiempo real y estado de BD.
"""

from datetime import datetime

import customtkinter as ctk

from utils.logger import get_logger

logger = get_logger("components.status_bar")


class StatusBar(ctk.CTkFrame):
    """Barra de estado inferior del dashboard."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        username: str = "",
        rol: str = "",
        **kwargs,
    ) -> None:
        """Inicializa la barra de estado.

        Args:
            master: Widget padre.
            username: Nombre del usuario actual.
            rol: Rol del usuario actual.
        """
        super().__init__(master, height=30, corner_radius=0, **kwargs)

        self._username = username
        self._rol = rol

        self.grid_columnconfigure(1, weight=1)

        # Usuario y rol
        self._user_label = ctk.CTkLabel(
            self,
            text=f"👤 {username}  |  Rol: {rol.capitalize()}",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._user_label.grid(row=0, column=0, padx=15, pady=5, sticky="w")

        # Estado BD
        self._db_label = ctk.CTkLabel(
            self,
            text="🟢 BD Conectada",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._db_label.grid(row=0, column=1, pady=5)

        # Reloj
        self._clock_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray40", "gray60"),
        )
        self._clock_label.grid(row=0, column=2, padx=15, pady=5, sticky="e")

        self._update_clock()

    def _update_clock(self) -> None:
        """Actualiza el reloj cada segundo."""
        now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
        self._clock_label.configure(text=f"🕐 {now}")
        self.after(1000, self._update_clock)

    def set_db_status(self, connected: bool) -> None:
        """Actualiza el indicador de estado de la BD.

        Args:
            connected: True si la BD está conectada.
        """
        if connected:
            self._db_label.configure(text="🟢 BD Conectada")
        else:
            self._db_label.configure(text="🔴 BD Desconectada")

    def update_user(self, username: str, rol: str) -> None:
        """Actualiza la información del usuario mostrada.

        Args:
            username: Nuevo nombre de usuario.
            rol: Nuevo rol.
        """
        self._user_label.configure(
            text=f"👤 {username}  |  Rol: {rol.capitalize()}"
        )
