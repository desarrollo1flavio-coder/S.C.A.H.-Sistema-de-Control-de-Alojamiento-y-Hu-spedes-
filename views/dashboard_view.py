"""Vista principal (Dashboard) de S.C.A.H.

Ventana principal con barra de navegación, área de contenido dinámica y barra de estado.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

import customtkinter as ctk

from controllers.auth_controller import AuthController, SessionInfo
from utils.logger import get_logger
from views.components.status_bar import StatusBar

logger = get_logger("views.dashboard")


class DashboardView(ctk.CTkToplevel):
    """Ventana principal del sistema S.C.A.H."""

    def __init__(
        self,
        master: ctk.CTk,
        session: SessionInfo,
        auth_controller: AuthController,
        on_logout: Optional[Callable[[], None]] = None,
    ) -> None:
        """Inicializa el dashboard.

        Args:
            master: Ventana padre (login).
            session: Sesión del usuario.
            auth_controller: Controlador de autenticación.
            on_logout: Callback al cerrar sesión.
        """
        super().__init__(master)

        self._session = session
        self._auth = auth_controller
        self._on_logout = on_logout
        self._current_module: Optional[ctk.CTkFrame] = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self.title("S.C.A.H. — Sistema de Control de Alojamiento y Huéspedes")
        self.geometry("1280x800")
        self.minsize(1024, 700)
        self._maximize()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._show_welcome()

        logger.info("Dashboard abierto — usuario: %s", session.username)

    def _maximize(self) -> None:
        """Maximiza la ventana."""
        try:
            self.state("zoomed")
        except tk.TclError:
            self.attributes("-zoomed", True)

    # ── UI ────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Construye la interfaz principal."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_topbar()
        self._build_sidebar()
        self._build_content_area()
        self._build_statusbar()

    def _build_topbar(self) -> None:
        """Barra superior con título y datos de sesión."""
        top = ctk.CTkFrame(self, height=55, corner_radius=0)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.grid_propagate(False)

        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left", fill="y", padx=15)

        ctk.CTkLabel(
            left, text="🛡️  S.C.A.H.",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", pady=10)

        ctk.CTkLabel(
            left, text="  |  Sección Hoteles — Policía de Tucumán",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60"),
        ).pack(side="left", padx=(5, 0))

        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="right", fill="y", padx=15)

        rol_text = self._session.rol.capitalize()
        ctk.CTkLabel(
            right, text=f"👤 {self._session.nombre_completo}  ({rol_text})",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", pady=10, padx=(0, 10))

        ctk.CTkButton(
            right, text="Cerrar Sesión", width=110, height=32,
            font=ctk.CTkFont(size=11), fg_color="transparent",
            border_width=1, hover_color=("gray80", "gray30"),
            command=self._handle_logout,
        ).pack(side="left")

        ctk.CTkButton(
            right, text="🌙/☀️", width=35, height=32,
            fg_color="transparent", hover_color=("gray80", "gray30"),
            command=self._toggle_theme,
        ).pack(side="left", padx=(5, 0))

    def _build_sidebar(self) -> None:
        """Panel de navegación lateral."""
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=1, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="NAVEGACIÓN",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("gray40", "gray60"),
        ).pack(fill="x", padx=15, pady=(20, 10))

        modules = [
            ("📋  Carga Manual", "manual", True),
            ("📂  Importar Excel", "import", True),
            ("🔍  Búsqueda", "search", True),
        ]

        if self._session.tiene_permiso("gestionar_usuarios"):
            modules.append(("👥  Usuarios", "users", True))

        for text, key, enabled in modules:
            btn = ctk.CTkButton(
                sidebar, text=text, anchor="w",
                height=40, corner_radius=6,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray25"),
                command=lambda k=key: self._nav_to(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[key] = btn

    def _build_content_area(self) -> None:
        """Área de contenido dinámico."""
        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self._content.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)

    def _build_statusbar(self) -> None:
        """Barra de estado inferior."""
        self._statusbar = StatusBar(self)
        self._statusbar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self._statusbar.update_user(
            self._session.nombre_completo, self._session.rol,
        )

    # ── Navigation ───────────────────────────────────────────────

    def _nav_to(self, module_key: str) -> None:
        """Navega a un módulo.

        Args:
            module_key: Clave del módulo.
        """
        for key, btn in self._nav_buttons.items():
            if key == module_key:
                btn.configure(
                    fg_color=("gray75", "gray30"),
                    text_color=("gray10", "gray90"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                )

        if self._current_module:
            self._current_module.destroy()
            self._current_module = None

        try:
            if module_key == "manual":
                from views.manual_view import ManualView
                self._current_module = ManualView(self._content, self._session)
            elif module_key == "import":
                from views.import_view import ImportView
                self._current_module = ImportView(self._content, self._session)
            elif module_key == "search":
                from views.search_view import SearchView
                self._current_module = SearchView(self._content, self._session)
            elif module_key == "users":
                self._show_users_module()
                return

            if self._current_module:
                self._current_module.pack(fill="both", expand=True)

        except Exception as e:
            logger.error("Error al cargar módulo '%s': %s", module_key, e)
            self._show_error_module(f"Error al cargar el módulo: {e}")

    def _show_welcome(self) -> None:
        """Muestra pantalla de bienvenida."""
        if self._current_module:
            self._current_module.destroy()

        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        center = ctk.CTkFrame(frame, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(
            center, text="🛡️",
            font=ctk.CTkFont(size=64),
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            center, text="S.C.A.H.",
            font=ctk.CTkFont(size=36, weight="bold"),
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            center,
            text="Sistema de Control de Alojamiento y Huéspedes",
            font=ctk.CTkFont(size=16),
            text_color=("gray40", "gray60"),
        ).pack(pady=(0, 20))

        ctk.CTkLabel(
            center,
            text=f"Bienvenido, {self._session.nombre_completo}",
            font=ctk.CTkFont(size=18),
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            center,
            text="Seleccione un módulo en el panel lateral para comenzar.",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray50"),
        ).pack()

        self._current_module = frame

    def _show_error_module(self, msg: str) -> None:
        """Muestra un módulo de error.

        Args:
            msg: Mensaje de error.
        """
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            frame, text="⚠️ Error",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="red",
        ).pack(pady=(50, 10))

        ctk.CTkLabel(
            frame, text=msg,
            font=ctk.CTkFont(size=13), wraplength=600,
        ).pack()

        self._current_module = frame

    def _show_users_module(self) -> None:
        """Muestra módulo básico de gestión de usuarios (placeholder)."""
        if self._current_module:
            self._current_module.destroy()

        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            frame, text="👥 Gestión de Usuarios",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            frame, text="Módulo en desarrollo.",
            font=ctk.CTkFont(size=13), text_color=("gray50", "gray50"),
        ).pack()

        self._current_module = frame

    # ── Actions ──────────────────────────────────────────────────

    def _handle_logout(self) -> None:
        """Cierre de sesión con confirmación."""
        confirm = messagebox.askyesno(
            "Cerrar Sesión",
            "¿Está seguro de que desea cerrar sesión?",
            parent=self,
        )
        if not confirm:
            return

        self._auth.logout()
        logger.info("Sesión cerrada — usuario: %s", self._session.username)

        self.destroy()
        if self._on_logout:
            self._on_logout()

    def _toggle_theme(self) -> None:
        """Alterna entre tema oscuro y claro."""
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Light" if current == "Dark" else "Dark")

    def _on_close(self) -> None:
        """Maneja el cierre de la ventana."""
        self._handle_logout()
