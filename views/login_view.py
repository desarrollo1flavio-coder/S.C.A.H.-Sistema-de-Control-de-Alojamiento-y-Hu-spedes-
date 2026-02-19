"""Vista de login para S.C.A.H. v2."""

import customtkinter as ctk
from typing import Callable, Optional

from config.settings import APP_TITLE, APP_VERSION, LOGIN_WINDOW_SIZE, LOGIN_WINDOW_RESIZABLE
from utils.logger import get_logger

logger = get_logger("views.login")


class LoginView(ctk.CTkToplevel):
    """Ventana de inicio de sesión."""

    def __init__(self, parent, on_login: Callable[[str, str], bool], **kwargs):
        super().__init__(parent, **kwargs)

        self.title(f"{APP_TITLE} - Iniciar Sesión")
        self.geometry(LOGIN_WINDOW_SIZE)
        self.resizable(LOGIN_WINDOW_RESIZABLE, LOGIN_WINDOW_RESIZABLE)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.grab_set()

        self._on_login = on_login
        self._parent = parent
        self._login_success = False

        self._build_ui()
        self._username_entry.focus_set()

    def _build_ui(self):
        # Contenedor principal
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=30)

        # Logo / Título
        ctk.CTkLabel(
            main_frame,
            text="S.C.A.H.",
            font=("", 36, "bold"),
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            main_frame,
            text="Sistema de Control de Alojamiento\ny Huéspedes",
            font=("", 14),
            justify="center",
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            main_frame,
            text=f"v{APP_VERSION}",
            font=("", 11),
            text_color="gray",
        ).pack(pady=(0, 30))

        # Formulario
        form = ctk.CTkFrame(main_frame)
        form.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(form, text="Usuario", font=("", 13)).pack(anchor="w", padx=15, pady=(15, 2))
        self._username_entry = ctk.CTkEntry(form, placeholder_text="Ingrese su usuario", height=38)
        self._username_entry.pack(fill="x", padx=15)

        ctk.CTkLabel(form, text="Contraseña", font=("", 13)).pack(anchor="w", padx=15, pady=(10, 2))
        self._password_entry = ctk.CTkEntry(
            form, placeholder_text="Ingrese su contraseña", show="\u2022", height=38,
        )
        self._password_entry.pack(fill="x", padx=15)

        # Botón login
        self._login_btn = ctk.CTkButton(
            form, text="Iniciar Sesión", height=40,
            font=("", 14, "bold"),
            command=self._do_login,
        )
        self._login_btn.pack(fill="x", padx=15, pady=(20, 15))

        # Mensaje de error
        self._error_label = ctk.CTkLabel(
            main_frame, text="", text_color="red", font=("", 12),
        )
        self._error_label.pack(pady=5)

        # Enter para login
        self._password_entry.bind("<Return>", lambda e: self._do_login())
        self._username_entry.bind("<Return>", lambda e: self._password_entry.focus_set())

    def _do_login(self):
        username = self._username_entry.get().strip()
        password = self._password_entry.get().strip()

        if not username or not password:
            self._show_error("Ingrese usuario y contraseña")
            return

        self._login_btn.configure(state="disabled", text="Verificando...")
        self._error_label.configure(text="")
        self.update_idletasks()

        try:
            success = self._on_login(username, password)
            if success:
                self._login_success = True
                self.grab_release()
                self.destroy()
            else:
                self._show_error("Credenciales inválidas")
        except Exception as e:
            self._show_error(str(e))
        finally:
            if self.winfo_exists():
                self._login_btn.configure(state="normal", text="Iniciar Sesión")

    def _show_error(self, msg: str):
        self._error_label.configure(text=msg)

    def _on_close(self):
        if not self._login_success:
            self._parent.destroy()
        else:
            self.destroy()
