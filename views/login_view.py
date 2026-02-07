"""Vista de login para S.C.A.H.

Pantalla de autenticación con interfaz moderna usando CustomTkinter.
"""

import threading
from typing import Callable, Optional

import customtkinter as ctk

from config.settings import (
    APP_ORGANIZATION,
    APP_SUBTITLE,
    APP_VERSION,
    DEFAULT_APPEARANCE_MODE,
    DEFAULT_COLOR_THEME,
    LOGIN_WINDOW_RESIZABLE,
    LOGIN_WINDOW_SIZE,
)
from controllers.auth_controller import AuthController, SessionInfo
from utils.exceptions import (
    AccountDisabledError,
    AccountLockedError,
    AuthenticationError,
    InvalidCredentialsError,
)
from utils.logger import get_logger

logger = get_logger("views.login")


class LoginView(ctk.CTk):
    """Ventana de inicio de sesión del sistema S.C.A.H."""

    def __init__(
        self,
        auth_controller: AuthController,
        on_login_success: Optional[Callable[[SessionInfo], None]] = None,
    ) -> None:
        """Inicializa la ventana de login.

        Args:
            auth_controller: Controlador de autenticación.
            on_login_success: Callback al autenticar exitosamente.
        """
        super().__init__()

        self._auth = auth_controller
        self._on_login_success = on_login_success
        self._is_authenticating = False

        ctk.set_appearance_mode(DEFAULT_APPEARANCE_MODE)
        ctk.set_default_color_theme(DEFAULT_COLOR_THEME)

        self.title("Login - S.C.A.H.")
        self.geometry(LOGIN_WINDOW_SIZE)
        self.resizable(LOGIN_WINDOW_RESIZABLE, LOGIN_WINDOW_RESIZABLE)
        self._center_window()
        self._build_ui()

        self.bind("<Return>", lambda e: self._handle_login())
        self.bind("<Escape>", lambda e: self.destroy())
        self.after(100, lambda: self._username_entry.focus_set())

    def _center_window(self) -> None:
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        w, h = map(int, LOGIN_WINDOW_SIZE.split("x"))
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        """Construye la interfaz de login."""
        main = ctk.CTkFrame(self, corner_radius=0)
        main.pack(fill="both", expand=True)

        # Header
        header = ctk.CTkFrame(main, corner_radius=0, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(40, 10))

        ctk.CTkLabel(header, text="🛡️", font=ctk.CTkFont(size=48)).pack(pady=(0, 5))
        ctk.CTkLabel(
            header, text=APP_ORGANIZATION,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray40", "gray60"), wraplength=350,
        ).pack()
        ctk.CTkLabel(
            header, text=APP_SUBTITLE,
            font=ctk.CTkFont(size=10), text_color=("gray50", "gray50"),
        ).pack()
        ctk.CTkLabel(
            header, text="S.C.A.H.",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(pady=(15, 2))
        ctk.CTkLabel(
            header, text="Sistema de Control de Alojamiento y Huéspedes",
            font=ctk.CTkFont(size=12), text_color=("gray40", "gray60"),
        ).pack()

        # Form
        form = ctk.CTkFrame(main, corner_radius=10)
        form.pack(fill="x", padx=40, pady=(25, 10))

        ctk.CTkLabel(
            form, text="Usuario",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).pack(fill="x", padx=20, pady=(20, 5))

        self._username_entry = ctk.CTkEntry(
            form, placeholder_text="Ingrese su usuario",
            height=40, font=ctk.CTkFont(size=13),
        )
        self._username_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            form, text="Contraseña",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).pack(fill="x", padx=20, pady=(5, 5))

        pw_frame = ctk.CTkFrame(form, fg_color="transparent")
        pw_frame.pack(fill="x", padx=20, pady=(0, 5))

        self._password_entry = ctk.CTkEntry(
            pw_frame, placeholder_text="Ingrese su contraseña",
            show="●", height=40, font=ctk.CTkFont(size=13),
        )
        self._password_entry.pack(side="left", fill="x", expand=True)

        self._show_pw = False
        self._toggle_btn = ctk.CTkButton(
            pw_frame, text="👁", width=40, height=40,
            command=self._toggle_pw, fg_color="transparent",
            hover_color=("gray80", "gray30"),
        )
        self._toggle_btn.pack(side="right", padx=(5, 0))

        self._login_btn = ctk.CTkButton(
            form, text="Iniciar Sesión", height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._handle_login,
        )
        self._login_btn.pack(fill="x", padx=20, pady=(15, 20))

        # Messages
        self._msg_label = ctk.CTkLabel(
            main, text="", font=ctk.CTkFont(size=12),
            text_color="red", wraplength=350,
        )
        self._msg_label.pack(fill="x", padx=40, pady=(5, 5))

        self._loading = ctk.CTkProgressBar(main, mode="indeterminate", height=3)
        self._loading.pack(fill="x", padx=40, pady=(0, 5))
        self._loading.pack_forget()

        # Footer
        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=40, pady=(0, 15))

        ctk.CTkLabel(
            footer, text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=10), text_color=("gray60", "gray40"),
        ).pack()

        ctk.CTkButton(
            footer, text="🌙 / ☀️", width=60, height=25,
            font=ctk.CTkFont(size=10), fg_color="transparent",
            hover_color=("gray80", "gray30"), command=self._toggle_theme,
        ).pack(pady=(5, 0))

    def _toggle_pw(self) -> None:
        """Alterna visibilidad de la contraseña."""
        self._show_pw = not self._show_pw
        self._password_entry.configure(show="" if self._show_pw else "●")
        self._toggle_btn.configure(text="🔒" if self._show_pw else "👁")

    def _toggle_theme(self) -> None:
        """Alterna entre tema oscuro y claro."""
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Light" if current == "Dark" else "Dark")

    def _show_msg(self, msg: str, error: bool = True) -> None:
        """Muestra un mensaje.

        Args:
            msg: Texto del mensaje.
            error: True=rojo, False=verde.
        """
        color = ("red", "#FF6B6B") if error else ("green", "#4ECB71")
        self._msg_label.configure(text=msg, text_color=color)

    def _set_loading(self, loading: bool) -> None:
        """Activa/desactiva indicador de carga.

        Args:
            loading: True para activar.
        """
        if loading:
            self._loading.pack(fill="x", padx=40, pady=(0, 5))
            self._loading.start()
            self._login_btn.configure(state="disabled", text="Verificando...")
            self._username_entry.configure(state="disabled")
            self._password_entry.configure(state="disabled")
        else:
            self._loading.stop()
            self._loading.pack_forget()
            self._login_btn.configure(state="normal", text="Iniciar Sesión")
            self._username_entry.configure(state="normal")
            self._password_entry.configure(state="normal")

    def _handle_login(self) -> None:
        """Maneja el evento de login."""
        if self._is_authenticating:
            return

        username = self._username_entry.get().strip()
        password = self._password_entry.get()

        if not username:
            self._show_msg("Ingrese su nombre de usuario")
            self._username_entry.focus_set()
            return
        if not password:
            self._show_msg("Ingrese su contraseña")
            self._password_entry.focus_set()
            return

        self._msg_label.configure(text="")
        self._is_authenticating = True
        self._set_loading(True)

        thread = threading.Thread(
            target=self._auth_thread, args=(username, password), daemon=True,
        )
        thread.start()

    def _auth_thread(self, username: str, password: str) -> None:
        """Hilo de autenticación.

        Args:
            username: Nombre de usuario.
            password: Contraseña.
        """
        try:
            session = self._auth.login(username, password)
            self.after(0, lambda: self._on_success(session))
        except (AccountLockedError, AccountDisabledError, InvalidCredentialsError) as e:
            self.after(0, lambda: self._on_error(e.message))
        except AuthenticationError as e:
            self.after(0, lambda: self._on_error(e.message))
        except Exception as e:
            logger.error("Error inesperado en login: %s", e)
            self.after(0, lambda: self._on_error("Error interno del sistema"))
        finally:
            self.after(0, self._finish_auth)

    def _on_success(self, session: SessionInfo) -> None:
        """Login exitoso.

        Args:
            session: Sesión creada.
        """
        self._show_msg(f"¡Bienvenido, {session.nombre_completo}!", error=False)
        if self._on_login_success:
            self.after(800, lambda: self._on_login_success(session))

    def _on_error(self, msg: str) -> None:
        """Error de login.

        Args:
            msg: Mensaje de error.
        """
        self._show_msg(msg)
        self._password_entry.delete(0, "end")
        self._password_entry.focus_set()

    def _finish_auth(self) -> None:
        """Finaliza el proceso de autenticación."""
        self._is_authenticating = False
        self._set_loading(False)
