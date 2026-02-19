"""Script de reconstrucción S.C.A.H. v2 - Fase 4.

main.py + requirements.txt + views/__init__.py update
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = {}

# ============================================================
# main.py — ORQUESTADOR PRINCIPAL
# ============================================================
FILES["main.py"] = '''"""S.C.A.H. - Sistema de Control de Alojamiento y Huéspedes v2.

Punto de entrada principal de la aplicación.
"""

import sys
import os
import threading
import customtkinter as ctk

from config.settings import (
    APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    THEME_MODE, THEME_COLOR, BACKUP_ENABLED, BACKUP_INTERVAL_HOURS,
)
from config.database import initialize_database, create_backup
from controllers.auth_controller import AuthController
from utils.logger import get_logger

logger = get_logger("main")


class SCAHApp(ctk.CTk):
    """Ventana principal de la aplicación S.C.A.H."""

    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1280x800")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        ctk.set_appearance_mode(THEME_MODE)
        ctk.set_default_color_theme(THEME_COLOR)

        self.auth_controller = AuthController()
        self.current_user: str | None = None
        self.current_role: str | None = None

        self._sidebar: ctk.CTkFrame | None = None
        self._content_frame: ctk.CTkFrame | None = None
        self._current_view = None
        self._status_bar = None

        self._init_database()
        self._show_login()

    def _init_database(self):
        """Inicializa la base de datos y aplica migraciones."""
        try:
            initialize_database()
            logger.info("Base de datos inicializada correctamente")
        except Exception as e:
            logger.error("Error al inicializar BD: %s", e)
            from tkinter import messagebox
            messagebox.showerror(
                "Error de Base de Datos",
                f"No se pudo inicializar la base de datos:\\n{e}\\n\\n"
                "La aplicación se cerrará.",
            )
            sys.exit(1)

    def _show_login(self):
        """Muestra la ventana de login."""
        from views.login_view import LoginView
        LoginView(self, on_success=self._on_login_success)

    def _on_login_success(self, username: str, role: str):
        """Callback al loguearse con éxito."""
        self.current_user = username
        self.current_role = role
        self.auth_controller.current_user = username
        self.auth_controller.current_role = role
        logger.info("Login exitoso: %s (rol: %s)", username, role)
        self._build_main_ui()
        self._start_backup_scheduler()

    def _build_main_ui(self):
        """Construye la interfaz principal con sidebar + content."""
        # Limpiar contenido previo
        for widget in self.winfo_children():
            widget.destroy()

        # Status bar (abajo)
        from views.components.status_bar import StatusBar
        self._status_bar = StatusBar(self)
        self._status_bar.pack(side="bottom", fill="x")
        self._status_bar.set_message(f"Sesión: {self.current_user} ({self.current_role})")

        # Sidebar (izquierda)
        self._sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Logo / titulo en sidebar
        ctk.CTkLabel(
            self._sidebar, text="S.C.A.H.",
            font=("", 22, "bold"),
        ).pack(pady=(20, 5))
        ctk.CTkLabel(
            self._sidebar, text=f"v{APP_VERSION}",
            font=("", 11), text_color="gray",
        ).pack(pady=(0, 20))

        # Botones de navegación
        nav_items = [
            ("Dashboard", self._show_dashboard),
            ("Importar Excel", self._show_import),
            ("Carga Manual", self._show_manual),
            ("Buscar", self._show_search),
        ]

        # Solo admin ve estos
        if self.current_role == "admin":
            nav_items.extend([
                ("Establecimientos", self._show_establecimientos),
                ("Usuarios", self._show_usuarios),
            ])

        for text, command in nav_items:
            btn = ctk.CTkButton(
                self._sidebar, text=text,
                font=("", 13), height=38,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                command=command,
            )
            btn.pack(fill="x", padx=10, pady=2)

        # Separador y logout
        ctk.CTkFrame(self._sidebar, height=1, fg_color="gray50").pack(fill="x", padx=15, pady=20)

        user_label = ctk.CTkLabel(
            self._sidebar, text=f"Usuario: {self.current_user}",
            font=("", 11), text_color="gray",
        )
        user_label.pack(padx=10, pady=2)

        ctk.CTkButton(
            self._sidebar, text="Cerrar Sesión",
            font=("", 12), height=32,
            fg_color="red", hover_color="darkred",
            command=self._logout,
        ).pack(fill="x", padx=10, pady=10, side="bottom")

        ctk.CTkButton(
            self._sidebar, text="Backup Manual",
            font=("", 11), height=28,
            fg_color="gray40",
            command=self._manual_backup,
        ).pack(fill="x", padx=10, pady=(0, 5), side="bottom")

        # Content frame (derecha)
        self._content_frame = ctk.CTkFrame(self, corner_radius=0)
        self._content_frame.pack(side="right", fill="both", expand=True)

        self._show_dashboard()

    @property
    def status_bar(self):
        return self._status_bar

    def refresh_dashboard(self):
        """Refresca el dashboard si está activo."""
        if self._current_view and hasattr(self._current_view, "refresh"):
            self._current_view.refresh()

    def _switch_view(self, view_class, **kwargs):
        """Cambia la vista activa en el content frame."""
        if self._current_view:
            self._current_view.destroy()

        self._current_view = view_class(
            self._content_frame,
            app_controller=self,
            **kwargs,
        )
        self._current_view.pack(fill="both", expand=True)

    def _show_dashboard(self):
        from views.dashboard_view import DashboardView
        self._switch_view(DashboardView)

    def _show_import(self):
        from views.import_view import ImportView
        self._switch_view(ImportView)

    def _show_manual(self):
        from views.manual_view import ManualView
        self._switch_view(ManualView)

    def _show_search(self):
        from views.search_view import SearchView
        self._switch_view(SearchView)

    def _show_establecimientos(self):
        from views.establecimientos_view import EstablecimientosView
        self._switch_view(EstablecimientosView)

    def _show_usuarios(self):
        from views.usuarios_view import UsuariosView
        self._switch_view(UsuariosView)

    def _logout(self):
        self.current_user = None
        self.current_role = None
        for widget in self.winfo_children():
            widget.destroy()
        self._show_login()

    def _manual_backup(self):
        try:
            path = create_backup()
            from tkinter import messagebox
            messagebox.showinfo("Backup", f"Backup creado:\\n{path}")
            if self._status_bar:
                self._status_bar.set_success("Backup creado exitosamente")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Error al crear backup:\\n{e}")

    def _start_backup_scheduler(self):
        """Inicia un timer periódico para backups automáticos."""
        if not BACKUP_ENABLED:
            return

        def do_backup():
            try:
                create_backup()
                logger.info("Backup automático completado")
            except Exception as e:
                logger.error("Error en backup automático: %s", e)

            interval_ms = int(BACKUP_INTERVAL_HOURS * 3600 * 1000)
            self.after(interval_ms, do_backup)

        initial_delay = int(BACKUP_INTERVAL_HOURS * 3600 * 1000)
        self.after(initial_delay, do_backup)


def main():
    """Punto de entrada."""
    logger.info("Iniciando %s v%s", APP_NAME, APP_VERSION)

    try:
        app = SCAHApp()
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("Aplicación cerrada por el usuario")
    except Exception as e:
        logger.critical("Error fatal: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()
'''

# ============================================================
# requirements.txt
# ============================================================
FILES["requirements.txt"] = '''# S.C.A.H. v2 - Dependencias
customtkinter>=5.2.0
pydantic>=2.0.0
pandas>=2.0.0
openpyxl>=3.1.0
xlrd>=2.0.0
bcrypt>=4.0.0
reportlab>=4.0.0
Pillow>=10.0.0
'''

# ============================================================
# views/__init__.py (update)
# ============================================================
FILES["views/__init__.py"] = '''"""Vistas de S.C.A.H. v2."""
'''

# ============================================================
# WRITE ALL FILES
# ============================================================
def write_all():
    written = 0
    for rel_path, content in FILES.items():
        full_path = os.path.join(BASE, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        written += 1
        print(f"  [OK] {rel_path}")
    print(f"\n  Total: {written} archivos escritos")


if __name__ == "__main__":
    print("=" * 60)
    print("S.C.A.H. v2 - Fase 4: main.py + requirements.txt")
    print("=" * 60)
    write_all()
    print("\nFase 4 completada.")
