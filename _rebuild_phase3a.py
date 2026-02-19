"""Script de reconstrucción S.C.A.H. v2 - Fase 3a.

Views: Components + Login + Dashboard
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = {}

# ============================================================
# views/__init__.py
# ============================================================
FILES["views/__init__.py"] = '''"""Módulo de vistas de S.C.A.H. v2."""
'''

# ============================================================
# views/components/__init__.py
# ============================================================
FILES["views/components/__init__.py"] = '''"""Componentes reutilizables de UI."""
'''

# ============================================================
# views/components/status_bar.py
# ============================================================
FILES["views/components/status_bar.py"] = '''"""Barra de estado inferior para S.C.A.H. v2."""

import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    """Barra de estado inferior con mensaje y estadísticas."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=30, **kwargs)
        self.pack_propagate(False)

        self._msg_label = ctk.CTkLabel(self, text="Listo", anchor="w", font=("", 12))
        self._msg_label.pack(side="left", padx=10, fill="x", expand=True)

        self._stats_label = ctk.CTkLabel(self, text="", anchor="e", font=("", 12))
        self._stats_label.pack(side="right", padx=10)

    def set_message(self, text: str, color: str = "gray"):
        self._msg_label.configure(text=text, text_color=color)

    def set_stats(self, text: str):
        self._stats_label.configure(text=text)

    def set_success(self, text: str):
        self.set_message(text, color="green")

    def set_error(self, text: str):
        self.set_message(text, color="red")

    def set_warning(self, text: str):
        self.set_message(text, color="orange")
'''

# ============================================================
# views/components/form_fields.py
# ============================================================
FILES["views/components/form_fields.py"] = '''"""Campos de formulario reutilizables para S.C.A.H. v2."""

import customtkinter as ctk
from typing import Optional, Callable


class LabeledEntry(ctk.CTkFrame):
    """Campo de texto con etiqueta."""

    def __init__(
        self, parent,
        label: str,
        placeholder: str = "",
        required: bool = False,
        width: int = 200,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent")
        label_text = f"{label} *" if required else label
        self._label = ctk.CTkLabel(self, text=label_text, anchor="w", font=("", 13))
        self._label.pack(anchor="w", padx=2)
        self._entry = ctk.CTkEntry(self, placeholder_text=placeholder, width=width, **kwargs)
        self._entry.pack(fill="x", padx=2, pady=(0, 5))
        self._error_label = ctk.CTkLabel(self, text="", text_color="red", font=("", 11), anchor="w")
        self._error_label.pack(anchor="w", padx=2)
        self._error_label.pack_forget()

    def get(self) -> str:
        return self._entry.get().strip()

    def set(self, value: str):
        self._entry.delete(0, "end")
        self._entry.insert(0, value)

    def clear(self):
        self._entry.delete(0, "end")
        self.clear_error()

    def show_error(self, msg: str):
        self._error_label.configure(text=msg)
        self._error_label.pack(anchor="w", padx=2)
        self._entry.configure(border_color="red")

    def clear_error(self):
        self._error_label.pack_forget()
        self._entry.configure(border_color=("gray50", "gray30"))

    def bind_change(self, callback: Callable):
        self._entry.bind("<KeyRelease>", callback)

    def set_state(self, state: str):
        self._entry.configure(state=state)


class LabeledComboBox(ctk.CTkFrame):
    """ComboBox con etiqueta."""

    def __init__(
        self, parent,
        label: str,
        values: list[str],
        default: str = "",
        required: bool = False,
        command: Optional[Callable] = None,
        width: int = 200,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent")
        label_text = f"{label} *" if required else label
        self._label = ctk.CTkLabel(self, text=label_text, anchor="w", font=("", 13))
        self._label.pack(anchor="w", padx=2)
        self._combo = ctk.CTkComboBox(
            self, values=values, width=width, command=command, **kwargs,
        )
        if default:
            self._combo.set(default)
        self._combo.pack(fill="x", padx=2, pady=(0, 5))

    def get(self) -> str:
        return self._combo.get().strip()

    def set(self, value: str):
        self._combo.set(value)

    def clear(self):
        self._combo.set("")

    def update_values(self, values: list[str]):
        self._combo.configure(values=values)


class LabeledDateEntry(ctk.CTkFrame):
    """Campo de fecha con etiqueta."""

    def __init__(
        self, parent,
        label: str,
        required: bool = False,
        width: int = 200,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent")
        label_text = f"{label} *" if required else label
        self._label = ctk.CTkLabel(self, text=label_text, anchor="w", font=("", 13))
        self._label.pack(anchor="w", padx=2)
        self._entry = ctk.CTkEntry(
            self, placeholder_text="DD/MM/AAAA", width=width,
        )
        self._entry.pack(fill="x", padx=2, pady=(0, 5))

    def get(self) -> str:
        return self._entry.get().strip()

    def set(self, value: str):
        self._entry.delete(0, "end")
        self._entry.insert(0, value)

    def clear(self):
        self._entry.delete(0, "end")
'''

# ============================================================
# views/components/data_table.py
# ============================================================
FILES["views/components/data_table.py"] = '''"""Tabla de datos scrollable para S.C.A.H. v2."""

import customtkinter as ctk
from tkinter import ttk
from typing import Optional, Callable


class DataTable(ctk.CTkFrame):
    """Tabla de datos basada en ttk.Treeview con estilo moderno."""

    def __init__(
        self,
        parent,
        columns: list[dict],
        on_select: Optional[Callable] = None,
        on_double_click: Optional[Callable] = None,
        show_scrollbar: bool = True,
        **kwargs,
    ):
        """
        Args:
            columns: Lista de dicts con 'key', 'text', 'width', 'anchor'.
            on_select: Callback al seleccionar una fila.
            on_double_click: Callback al hacer doble click en una fila.
        """
        super().__init__(parent, **kwargs)

        self._columns = columns
        self._on_select = on_select
        self._on_double_click = on_double_click
        self._data: list[dict] = []

        # Configurar estilo
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("DataTable.Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            rowheight=28,
            font=("", 11),
        )
        style.configure("DataTable.Treeview.Heading",
            background="#1f538d",
            foreground="white",
            font=("", 11, "bold"),
        )
        style.map("DataTable.Treeview",
            background=[("selected", "#1f538d")],
            foreground=[("selected", "white")],
        )

        # Crear Treeview
        col_keys = [c["key"] for c in columns]
        self._tree = ttk.Treeview(
            self,
            columns=col_keys,
            show="headings",
            style="DataTable.Treeview",
            selectmode="extended",
        )

        for col_def in columns:
            self._tree.heading(
                col_def["key"],
                text=col_def.get("text", col_def["key"]),
                anchor=col_def.get("anchor", "w"),
            )
            self._tree.column(
                col_def["key"],
                width=col_def.get("width", 100),
                minwidth=50,
                anchor=col_def.get("anchor", "w"),
            )

        # Scrollbars
        if show_scrollbar:
            y_scroll = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
            x_scroll = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
            self._tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
            y_scroll.pack(side="right", fill="y")
            x_scroll.pack(side="bottom", fill="x")

        self._tree.pack(fill="both", expand=True)

        # Bindings
        if on_select:
            self._tree.bind("<<TreeviewSelect>>", self._handle_select)
        if on_double_click:
            self._tree.bind("<Double-1>", self._handle_double_click)

        # Tags para filas alternas
        self._tree.tag_configure("odd", background="#333333")
        self._tree.tag_configure("even", background="#2b2b2b")

    def load_data(self, data: list[dict]):
        """Carga datos en la tabla, reemplazando los existentes."""
        self._tree.delete(*self._tree.get_children())
        self._data = data
        for i, row in enumerate(data):
            tag = "odd" if i % 2 else "even"
            values = [str(row.get(c["key"], "")) for c in self._columns]
            self._tree.insert("", "end", values=values, tags=(tag,))

    def clear(self):
        """Limpia todos los datos de la tabla."""
        self._tree.delete(*self._tree.get_children())
        self._data = []

    def get_selected(self) -> list[dict]:
        """Retorna los registros seleccionados."""
        selected = []
        for item_id in self._tree.selection():
            idx = self._tree.index(item_id)
            if idx < len(self._data):
                selected.append(self._data[idx])
        return selected

    def get_selected_indices(self) -> list[int]:
        """Retorna los índices de filas seleccionadas."""
        return [self._tree.index(item_id) for item_id in self._tree.selection()]

    @property
    def row_count(self) -> int:
        return len(self._data)

    def _handle_select(self, event):
        if self._on_select:
            selected = self.get_selected()
            self._on_select(selected)

    def _handle_double_click(self, event):
        if self._on_double_click:
            selected = self.get_selected()
            if selected:
                self._on_double_click(selected[0])
'''

# ============================================================
# views/login_view.py
# ============================================================
FILES["views/login_view.py"] = '''"""Vista de login para S.C.A.H. v2."""

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
            text="Sistema de Control de Alojamiento\\ny Huéspedes",
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
            form, placeholder_text="Ingrese su contraseña", show="\\u2022", height=38,
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
'''

# ============================================================
# views/dashboard_view.py
# ============================================================
FILES["views/dashboard_view.py"] = '''"""Vista del dashboard principal para S.C.A.H. v2."""

import customtkinter as ctk
from typing import Optional

from models.estadia import EstadiaDAO
from models.persona import PersonaDAO
from config.settings import APP_VERSION
from utils.logger import get_logger

logger = get_logger("views.dashboard")


class DashboardView(ctk.CTkFrame):
    """Panel principal con estadísticas y accesos rápidos."""

    def __init__(self, parent, app_controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app_controller
        self._build_ui()

    def _build_ui(self):
        # Título
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="Dashboard",
            font=("", 24, "bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"v{APP_VERSION}",
            font=("", 12),
            text_color="gray",
        ).pack(side="right")

        # Tarjetas de estadísticas
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=10)
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self._card_total_personas = self._create_card(cards_frame, "Total Personas", "0", 0)
        self._card_total_estadias = self._create_card(cards_frame, "Total Estadías", "0", 1)
        self._card_hospedados_hoy = self._create_card(cards_frame, "Hospedados Hoy", "0", 2)
        self._card_importaciones = self._create_card(cards_frame, "Importaciones", "0", 3)

        # Acciones rápidas
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(actions_frame, text="Acciones Rápidas", font=("", 16, "bold")).pack(
            anchor="w", pady=(5, 10),
        )

        btns_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btns_frame.pack(fill="x")

        self._btn_import = ctk.CTkButton(
            btns_frame, text="Importar Excel",
            font=("", 14), height=45, width=180,
            command=lambda: self._navigate("import"),
        )
        self._btn_import.pack(side="left", padx=5)

        self._btn_manual = ctk.CTkButton(
            btns_frame, text="Carga Manual",
            font=("", 14), height=45, width=180,
            command=lambda: self._navigate("manual"),
        )
        self._btn_manual.pack(side="left", padx=5)

        self._btn_search = ctk.CTkButton(
            btns_frame, text="Buscar",
            font=("", 14), height=45, width=180,
            command=lambda: self._navigate("search"),
        )
        self._btn_search.pack(side="left", padx=5)

        self._btn_backup = ctk.CTkButton(
            btns_frame, text="Crear Backup",
            font=("", 14), height=45, width=180,
            fg_color="gray40",
            command=self._do_backup,
        )
        self._btn_backup.pack(side="left", padx=5)

        # Top nacionalidades
        stats_container = ctk.CTkFrame(self, fg_color="transparent")
        stats_container.pack(fill="both", expand=True, padx=20, pady=10)
        stats_container.columnconfigure((0, 1), weight=1)

        nac_frame = ctk.CTkFrame(stats_container)
        nac_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        ctk.CTkLabel(nac_frame, text="Top Nacionalidades", font=("", 14, "bold")).pack(
            anchor="w", padx=10, pady=10,
        )
        self._nac_list = ctk.CTkTextbox(nac_frame, height=200, state="disabled")
        self._nac_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        est_frame = ctk.CTkFrame(stats_container)
        est_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        ctk.CTkLabel(est_frame, text="Top Establecimientos", font=("", 14, "bold")).pack(
            anchor="w", padx=10, pady=10,
        )
        self._est_list = ctk.CTkTextbox(est_frame, height=200, state="disabled")
        self._est_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _create_card(self, parent, title: str, value: str, col: int) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)

        ctk.CTkLabel(card, text=title, font=("", 12), text_color="gray").pack(
            padx=15, pady=(10, 0),
        )
        val_label = ctk.CTkLabel(card, text=value, font=("", 28, "bold"))
        val_label.pack(padx=15, pady=(0, 10))
        return val_label

    def refresh_stats(self):
        """Actualiza las estadísticas del dashboard."""
        try:
            total_personas = PersonaDAO.contar_total()
            total_estadias = EstadiaDAO.contar_total()
            hospedados = EstadiaDAO.contar_activas_hoy()

            self._card_total_personas.configure(text=str(total_personas))
            self._card_total_estadias.configure(text=str(total_estadias))
            self._card_hospedados_hoy.configure(text=str(hospedados))

            # Top nacionalidades
            nacs = EstadiaDAO.estadisticas_nacionalidades(8)
            self._nac_list.configure(state="normal")
            self._nac_list.delete("1.0", "end")
            for nac in nacs:
                self._nac_list.insert(
                    "end", f"  {nac['nacionalidad']}: {nac['cantidad']}\\n",
                )
            self._nac_list.configure(state="disabled")

            # Top establecimientos
            ests = EstadiaDAO.estadisticas_establecimientos(8)
            self._est_list.configure(state="normal")
            self._est_list.delete("1.0", "end")
            for est in ests:
                self._est_list.insert(
                    "end", f"  {est['establecimiento']}: {est['cantidad']}\\n",
                )
            self._est_list.configure(state="disabled")

        except Exception as e:
            logger.error("Error al refrescar stats: %s", e)

    def _navigate(self, view_name: str):
        if self._app and hasattr(self._app, "show_view"):
            self._app.show_view(view_name)

    def _do_backup(self):
        try:
            from config.database import create_backup
            path = create_backup()
            if self._app and hasattr(self._app, "status_bar"):
                self._app.status_bar.set_success(f"Backup creado: {path.name}")
        except Exception as e:
            logger.error("Error al crear backup: %s", e)
            if self._app and hasattr(self._app, "status_bar"):
                self._app.status_bar.set_error(f"Error al crear backup: {e}")
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
    print("S.C.A.H. v2 - Fase 3a: Components + Login + Dashboard")
    print("=" * 60)
    write_all()
    print("\nFase 3a completada.")
