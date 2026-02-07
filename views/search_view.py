"""Vista de búsqueda de huéspedes para S.C.A.H.

Búsqueda rápida con debounce y búsqueda avanzada con filtros múltiples.
"""

from datetime import date, datetime
from typing import Optional

import customtkinter as ctk

from config.settings import DEBOUNCE_MS, NACIONALIDADES, PAGINATION_SIZE
from controllers.auth_controller import SessionInfo
from controllers.huesped_controller import HuespedController
from utils.logger import get_logger
from views.components.data_table import DataTable

logger = get_logger("views.search")


class SearchView(ctk.CTkFrame):
    """Módulo de búsqueda de huéspedes."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        session: SessionInfo,
    ) -> None:
        """Inicializa la vista de búsqueda.

        Args:
            parent: Frame contenedor.
            session: Sesión del usuario.
        """
        super().__init__(parent, fg_color="transparent")

        self._session = session
        self._controller = HuespedController(session)
        self._debounce_id: Optional[str] = None
        self._advanced_visible = False
        self._current_page = 1
        self._total_results = 0

        self._build_ui()

    def _build_ui(self) -> None:
        """Construye la interfaz de búsqueda."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            header, text="🔍  Búsqueda de Huéspedes",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        self._result_count = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray50"),
        )
        self._result_count.pack(side="right")

        # Quick search
        self._build_quick_search()

        # Advanced search (collapsible)
        self._build_advanced_search()

        # Results table
        self._build_results()

        # Status
        self._msg_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12),
        )
        self._msg_label.pack(fill="x", padx=30, pady=(5, 15))

    def _build_quick_search(self) -> None:
        """Barra de búsqueda rápida."""
        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.pack(fill="x", padx=30, pady=(0, 5))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            inner, text="🔍", font=ctk.CTkFont(size=16),
        ).pack(side="left", padx=(0, 8))

        self._search_entry = ctk.CTkEntry(
            inner, placeholder_text="Buscar por DNI, pasaporte, apellido o nombre...",
            height=38, font=ctk.CTkFont(size=13),
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._search_entry.bind("<KeyRelease>", self._on_key_release)
        self._search_entry.bind("<Return>", lambda e: self._do_quick_search())

        ctk.CTkButton(
            inner, text="Buscar", width=100, height=38,
            command=self._do_quick_search,
        ).pack(side="left", padx=(0, 5))

        self._advanced_toggle = ctk.CTkButton(
            inner, text="▼ Avanzada", width=110, height=38,
            fg_color="transparent", border_width=1,
            hover_color=("gray80", "gray30"),
            command=self._toggle_advanced,
        )
        self._advanced_toggle.pack(side="left")

    def _build_advanced_search(self) -> None:
        """Panel de búsqueda avanzada (colapsable)."""
        self._advanced_frame = ctk.CTkFrame(self, corner_radius=10)
        # No se empaqueta hasta que se active

        inner = ctk.CTkFrame(self._advanced_frame, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            inner, text="Búsqueda Avanzada",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(fill="x", pady=(0, 10))

        # Row 1: Nombre + Apellido
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        row1.columnconfigure((0, 1, 2, 3), weight=1)

        self._adv_apellido = self._adv_field(row1, "Apellido", 0, 0)
        self._adv_nombre = self._adv_field(row1, "Nombre", 0, 1)
        self._adv_dni = self._adv_field(row1, "DNI", 0, 2)
        self._adv_pasaporte = self._adv_field(row1, "Pasaporte", 0, 3)

        # Row 2: Nacionalidad + Habitación + Fechas
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        row2.columnconfigure((0, 1, 2, 3), weight=1)

        # Nacionalidad combo
        nac_frame = ctk.CTkFrame(row2, fg_color="transparent")
        nac_frame.grid(row=0, column=0, sticky="ew", padx=5)
        ctk.CTkLabel(nac_frame, text="Nacionalidad", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self._adv_nacionalidad = ctk.CTkComboBox(nac_frame, values=[""] + NACIONALIDADES)
        self._adv_nacionalidad.pack(fill="x", pady=(2, 5))
        self._adv_nacionalidad.set("")

        self._adv_habitacion = self._adv_field(row2, "Habitación", 0, 1)

        # Fecha desde
        fd_frame = ctk.CTkFrame(row2, fg_color="transparent")
        fd_frame.grid(row=0, column=2, sticky="ew", padx=5)
        ctk.CTkLabel(fd_frame, text="Fecha desde", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self._adv_fecha_desde = ctk.CTkEntry(fd_frame, placeholder_text="DD/MM/AAAA")
        self._adv_fecha_desde.pack(fill="x", pady=(2, 5))

        # Fecha hasta
        fh_frame = ctk.CTkFrame(row2, fg_color="transparent")
        fh_frame.grid(row=0, column=3, sticky="ew", padx=5)
        ctk.CTkLabel(fh_frame, text="Fecha hasta", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self._adv_fecha_hasta = ctk.CTkEntry(fh_frame, placeholder_text="DD/MM/AAAA")
        self._adv_fecha_hasta.pack(fill="x", pady=(2, 5))

        # Row 3: Operador + Botones
        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(row3, text="Operador:", font=ctk.CTkFont(size=12)).pack(side="left")

        self._adv_operator = ctk.CTkSegmentedButton(
            row3, values=["AND", "OR"], width=120, height=30,
        )
        self._adv_operator.pack(side="left", padx=(5, 20))
        self._adv_operator.set("AND")

        ctk.CTkButton(
            row3, text="Limpiar", width=80,
            fg_color="transparent", border_width=1,
            hover_color=("gray80", "gray30"),
            command=self._clear_advanced,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            row3, text="🔍 Buscar", width=100,
            command=self._do_advanced_search,
        ).pack(side="right", padx=5)

    def _build_results(self) -> None:
        """Tabla de resultados."""
        columns = [
            ("id", "ID", 50),
            ("apellido", "Apellido", 130),
            ("nombre", "Nombre", 130),
            ("dni", "DNI", 90),
            ("pasaporte", "Pasaporte", 100),
            ("nacionalidad", "Nacionalidad", 110),
            ("habitacion", "Hab.", 60),
            ("fecha_entrada", "Entrada", 100),
            ("fecha_salida", "Salida", 100),
            ("telefono", "Teléfono", 110),
        ]

        self._table = DataTable(
            self, columns=columns, page_size=PAGINATION_SIZE,
        )
        self._table.pack(fill="both", expand=True, padx=30, pady=(5, 5))

        # Action bar
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=30, pady=(0, 5))

        self._view_btn = ctk.CTkButton(
            action_bar, text="👁 Ver Detalle", width=120,
            command=self._view_detail, state="disabled",
        )
        self._view_btn.pack(side="left", padx=(0, 5))

        self._edit_btn = ctk.CTkButton(
            action_bar, text="✏️ Editar", width=100,
            command=self._edit_record, state="disabled",
        )
        self._edit_btn.pack(side="left", padx=(0, 5))

        if self._session.tiene_permiso("eliminar"):
            self._delete_btn = ctk.CTkButton(
                action_bar, text="🗑 Eliminar", width=100,
                fg_color=("#D32F2F", "#B71C1C"),
                hover_color=("#B71C1C", "#8B0000"),
                command=self._delete_record, state="disabled",
            )
            self._delete_btn.pack(side="left", padx=(0, 5))

        # Bind table selection
        if hasattr(self._table, "_tree"):
            self._table._tree.bind("<<TreeviewSelect>>", self._on_select)

    # ── Helpers ──────────────────────────────────────────────────

    def _adv_field(
        self, parent: ctk.CTkFrame, label: str, row: int, col: int,
    ) -> ctk.CTkEntry:
        """Campo de búsqueda avanzada.

        Args:
            parent: Frame contenedor.
            label: Etiqueta.
            row: Fila.
            col: Columna.

        Returns:
            Entry creado.
        """
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="ew", padx=5)
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11)).pack(anchor="w")
        entry = ctk.CTkEntry(frame, placeholder_text=label)
        entry.pack(fill="x", pady=(2, 5))
        return entry

    def _toggle_advanced(self) -> None:
        """Muestra/oculta búsqueda avanzada."""
        if self._advanced_visible:
            self._advanced_frame.pack_forget()
            self._advanced_toggle.configure(text="▼ Avanzada")
        else:
            self._advanced_frame.pack(fill="x", padx=30, pady=(0, 5),
                                       after=self._advanced_toggle.master.master)
            self._advanced_toggle.configure(text="▲ Avanzada")
        self._advanced_visible = not self._advanced_visible

    def _clear_advanced(self) -> None:
        """Limpia campos avanzados."""
        for entry in (self._adv_apellido, self._adv_nombre, self._adv_dni,
                      self._adv_pasaporte, self._adv_habitacion,
                      self._adv_fecha_desde, self._adv_fecha_hasta):
            entry.delete(0, "end")
        self._adv_nacionalidad.set("")
        self._adv_operator.set("AND")

    # ── Debounce ─────────────────────────────────────────────────

    def _on_key_release(self, event) -> None:
        """Maneja keyrelease con debounce.

        Args:
            event: Evento de teclado.
        """
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(DEBOUNCE_MS, self._do_quick_search)

    # ── Quick Search ─────────────────────────────────────────────

    def _do_quick_search(self) -> None:
        """Ejecuta la búsqueda rápida."""
        query = self._search_entry.get().strip()
        if not query:
            self._table.load_data([])
            self._result_count.configure(text="")
            self._update_action_buttons(False)
            return

        try:
            results = self._controller.buscar_rapida(query)
            self._display_results(results)
        except Exception as e:
            logger.error("Error en búsqueda rápida: %s", e)
            self._show_msg(f"❌ Error: {e}")

    # ── Advanced Search ──────────────────────────────────────────

    def _do_advanced_search(self) -> None:
        """Ejecuta la búsqueda avanzada."""
        filtros: dict = {}

        for key, entry in [
            ("apellido", self._adv_apellido),
            ("nombre", self._adv_nombre),
            ("dni", self._adv_dni),
            ("pasaporte", self._adv_pasaporte),
            ("habitacion", self._adv_habitacion),
        ]:
            val = entry.get().strip()
            if val:
                filtros[key] = val

        nac = self._adv_nacionalidad.get().strip()
        if nac:
            filtros["nacionalidad"] = nac

        # Fechas
        for key, entry in [
            ("fecha_desde", self._adv_fecha_desde),
            ("fecha_hasta", self._adv_fecha_hasta),
        ]:
            val = entry.get().strip()
            if val:
                try:
                    filtros[key] = datetime.strptime(val, "%d/%m/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    self._show_msg(f"⚠️ Formato de fecha inválido: {val}. Use DD/MM/AAAA")
                    return

        if not filtros:
            self._show_msg("⚠️ Ingrese al menos un criterio de búsqueda")
            return

        operador = self._adv_operator.get()

        try:
            results, total = self._controller.buscar_avanzada(
                filtros=filtros,
                operador=operador,
                pagina=1,
                por_pagina=PAGINATION_SIZE,
            )
            self._display_results(results)
        except Exception as e:
            logger.error("Error en búsqueda avanzada: %s", e)
            self._show_msg(f"❌ Error: {e}")

    # ── Display Results ──────────────────────────────────────────

    def _display_results(self, results: list[dict]) -> None:
        """Muestra resultados en la tabla.

        Args:
            results: Lista de registros.
        """
        self._total_results = len(results)
        self._table.load_data(results)
        self._result_count.configure(text=f"{self._total_results} resultado(s)")
        self._update_action_buttons(False)

        if not results:
            self._show_msg("No se encontraron resultados", error=False)
        else:
            self._show_msg("")

    # ── Actions ──────────────────────────────────────────────────

    def _on_select(self, event) -> None:
        """Maneja selección en la tabla.

        Args:
            event: Evento de selección.
        """
        selected = self._table.get_selected()
        self._update_action_buttons(selected is not None)

    def _update_action_buttons(self, enabled: bool) -> None:
        """Actualiza estado de botones de acción.

        Args:
            enabled: True para habilitar.
        """
        state = "normal" if enabled else "disabled"
        self._view_btn.configure(state=state)
        self._edit_btn.configure(state=state)
        if hasattr(self, "_delete_btn"):
            self._delete_btn.configure(state=state)

    def _get_selected_id(self) -> Optional[int]:
        """Obtiene el ID del registro seleccionado.

        Returns:
            ID del huésped o None.
        """
        selected = self._table.get_selected()
        if selected and "id" in selected:
            try:
                return int(selected["id"])
            except (ValueError, TypeError):
                return None
        return None

    def _view_detail(self) -> None:
        """Muestra detalle del huésped seleccionado."""
        huesped_id = self._get_selected_id()
        if not huesped_id:
            return

        try:
            data = self._controller.obtener(huesped_id)
            if not data:
                self._show_msg("⚠️ Registro no encontrado")
                return
            self._show_detail_dialog(data)
        except Exception as e:
            self._show_msg(f"❌ Error: {e}")

    def _show_detail_dialog(self, data: dict) -> None:
        """Muestra diálogo con detalle del huésped.

        Args:
            data: Datos del huésped.
        """
        dialog = ctk.CTkToplevel(self)
        dialog.title("Detalle del Huésped")
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            scroll,
            text=f"{data.get('apellido', '')} {data.get('nombre', '')}",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(fill="x", pady=(0, 15))

        fields = [
            ("ID", "id"),
            ("Nacionalidad", "nacionalidad"),
            ("Procedencia", "procedencia"),
            ("DNI", "dni"),
            ("Pasaporte", "pasaporte"),
            ("Edad", "edad"),
            ("Profesión", "profesion"),
            ("Habitación", "habitacion"),
            ("Destino", "destino"),
            ("Teléfono", "telefono"),
            ("Vehículo", "vehiculo_tiene"),
            ("Datos Vehículo", "vehiculo_datos"),
            ("Fecha Entrada", "fecha_entrada"),
            ("Fecha Salida", "fecha_salida"),
            ("Cargado por", "usuario_carga"),
            ("Fecha Creación", "created_at"),
        ]

        for label, key in fields:
            val = data.get(key, "—")
            if val is None or val == "":
                val = "—"
            if key == "vehiculo_tiene":
                val = "Sí" if val else "No"

            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row, text=f"{label}:", font=ctk.CTkFont(size=12, weight="bold"),
                width=140, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=str(val), font=ctk.CTkFont(size=12),
            ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            scroll, text="Cerrar", width=100, command=dialog.destroy,
        ).pack(pady=(20, 0))

    def _edit_record(self) -> None:
        """Abre diálogo de edición (placeholder)."""
        huesped_id = self._get_selected_id()
        if not huesped_id:
            return
        self._show_msg(f"Función de edición para ID {huesped_id} — En desarrollo")

    def _delete_record(self) -> None:
        """Elimina el registro seleccionado."""
        huesped_id = self._get_selected_id()
        if not huesped_id:
            return

        from tkinter import messagebox

        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar el huésped ID {huesped_id}?\n"
            "El registro será desactivado (soft-delete).",
            parent=self,
        )
        if not confirm:
            return

        try:
            result = self._controller.eliminar(huesped_id)
            if result:
                self._show_msg(f"✅ Huésped ID {huesped_id} eliminado", error=False)
                self._do_quick_search()  # Refrescar
            else:
                self._show_msg("⚠️ No se pudo eliminar el registro")
        except Exception as e:
            self._show_msg(f"❌ Error: {e}")

    def _show_msg(self, msg: str, error: bool = True) -> None:
        """Muestra mensaje.

        Args:
            msg: Texto.
            error: True=rojo, False=verde.
        """
        color = ("red", "#FF6B6B") if error else ("green", "#4ECB71")
        self._msg_label.configure(text=msg, text_color=color)
