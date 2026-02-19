"""Vista de búsqueda de huéspedes para S.C.A.H. v2."""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Optional

from controllers.estadia_controller import EstadiaController
from controllers.persona_controller import PersonaController
from controllers.report_controller import ReportController
from models.estadia import EstadiaDAO
from views.components.data_table import DataTable
from views.components.form_fields import LabeledEntry, LabeledComboBox
from config.settings import NACIONALIDADES, DEBOUNCE_MS
from utils.logger import get_logger

logger = get_logger("views.search")


class SearchView(ctk.CTkFrame):
    """Vista de búsqueda con filtros avanzados y resultados en tabla."""

    def __init__(self, parent, app_controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app_controller
        self._debounce_id = None
        self._current_page = 1
        self._total_results = 0
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="Buscar Huéspedes", font=("", 24, "bold")).pack(side="left")

        # Búsqueda rápida
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=20, pady=5)

        self._search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Buscar por nombre, DNI, pasaporte...",
            height=38, font=("", 13),
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(15, 5), pady=10)
        self._search_entry.bind("<KeyRelease>", self._on_search_change)

        self._search_field = ctk.CTkComboBox(
            search_frame,
            values=["Todos los campos", "DNI", "Pasaporte", "Apellido", "Nombre", "Nacionalidad", "Establecimiento"],
            width=160,
        )
        self._search_field.set("Todos los campos")
        self._search_field.pack(side="left", padx=5, pady=10)

        self._btn_search = ctk.CTkButton(
            search_frame, text="Buscar", width=100,
            command=self._do_search,
        )
        self._btn_search.pack(side="left", padx=(5, 15), pady=10)

        # Filtros avanzados (colapsable)
        self._filters_visible = False
        self._btn_toggle_filters = ctk.CTkButton(
            self, text="Mostrar Filtros Avanzados",
            fg_color="gray40", height=30, font=("", 12),
            command=self._toggle_filters,
        )
        self._btn_toggle_filters.pack(padx=20, pady=2, anchor="w")

        self._filters_frame = ctk.CTkFrame(self)

        filters_row = ctk.CTkFrame(self._filters_frame, fg_color="transparent")
        filters_row.pack(fill="x", padx=10, pady=5)
        filters_row.columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._f_nacionalidad = LabeledComboBox(filters_row, "Nacionalidad", [""] + NACIONALIDADES)
        self._f_nacionalidad.grid(row=0, column=0, sticky="ew", padx=3)

        self._f_establecimiento = LabeledEntry(filters_row, "Establecimiento")
        self._f_establecimiento.grid(row=0, column=1, sticky="ew", padx=3)

        self._f_fecha_desde = LabeledEntry(filters_row, "Desde", placeholder="DD/MM/AAAA")
        self._f_fecha_desde.grid(row=0, column=2, sticky="ew", padx=3)

        self._f_fecha_hasta = LabeledEntry(filters_row, "Hasta", placeholder="DD/MM/AAAA")
        self._f_fecha_hasta.grid(row=0, column=3, sticky="ew", padx=3)

        ctk.CTkButton(
            filters_row, text="Aplicar Filtros", command=self._do_search,
        ).grid(row=0, column=4, sticky="ew", padx=3, pady=(22, 0))

        # Tabla de resultados
        table_columns = [
            {"key": "id", "text": "ID", "width": 50},
            {"key": "establecimiento", "text": "HOTEL", "width": 130},
            {"key": "apellido", "text": "APELLIDO", "width": 120},
            {"key": "nombre", "text": "NOMBRE", "width": 100},
            {"key": "dni", "text": "D.N.I.", "width": 90},
            {"key": "pasaporte", "text": "PASAPORTE", "width": 90},
            {"key": "nacionalidad", "text": "NACIONALIDAD", "width": 100},
            {"key": "procedencia", "text": "PROCEDENCIA", "width": 100},
            {"key": "edad", "text": "EDAD", "width": 50},
            {"key": "profesion", "text": "PROFESIÓN", "width": 90},
            {"key": "fecha_entrada", "text": "ENTRADA", "width": 90},
            {"key": "fecha_salida", "text": "SALIDA", "width": 90},
        ]
        self._table = DataTable(
            self, columns=table_columns,
            on_double_click=self._on_row_double_click,
        )
        self._table.pack(fill="both", expand=True, padx=20, pady=5)

        # Footer con paginación y exportar
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(5, 10))

        self._results_label = ctk.CTkLabel(footer, text="0 resultados", font=("", 12))
        self._results_label.pack(side="left")

        self._btn_next = ctk.CTkButton(
            footer, text=">", width=30, command=lambda: self._change_page(1),
        )
        self._btn_next.pack(side="right", padx=2)

        self._page_label = ctk.CTkLabel(footer, text="Pág. 1", font=("", 12))
        self._page_label.pack(side="right", padx=5)

        self._btn_prev = ctk.CTkButton(
            footer, text="<", width=30, command=lambda: self._change_page(-1),
        )
        self._btn_prev.pack(side="right", padx=2)

        ctk.CTkButton(
            footer, text="Exportar Excel", width=120,
            fg_color="gray40", command=self._export_excel,
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            footer, text="Exportar PDF", width=120,
            fg_color="gray40", command=self._export_pdf,
        ).pack(side="right", padx=2)

    def _toggle_filters(self):
        self._filters_visible = not self._filters_visible
        if self._filters_visible:
            self._filters_frame.pack(fill="x", padx=20, pady=2, after=self._btn_toggle_filters)
            self._btn_toggle_filters.configure(text="Ocultar Filtros Avanzados")
        else:
            self._filters_frame.pack_forget()
            self._btn_toggle_filters.configure(text="Mostrar Filtros Avanzados")

    def _on_search_change(self, event=None):
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(DEBOUNCE_MS, self._do_search)

    def _get_field_name(self) -> str | None:
        field = self._search_field.get()
        field_map = {
            "DNI": "dni", "Pasaporte": "pasaporte",
            "Apellido": "apellido", "Nombre": "nombre",
            "Nacionalidad": "nacionalidad", "Establecimiento": "establecimiento",
        }
        return field_map.get(field)

    def _build_filters(self) -> dict | None:
        filtros = {}
        nac = self._f_nacionalidad.get() if self._filters_visible else ""
        if nac:
            filtros["nacionalidad"] = nac
        est = self._f_establecimiento.get() if self._filters_visible else ""
        if est:
            filtros["establecimiento"] = est
        # Parse dates
        from datetime import datetime
        for key, field in [("fecha_desde", self._f_fecha_desde), ("fecha_hasta", self._f_fecha_hasta)]:
            if self._filters_visible and field.get():
                for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
                    try:
                        filtros[key] = datetime.strptime(field.get(), fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
        return filtros if filtros else None

    def _do_search(self):
        termino = self._search_entry.get().strip()
        campo = self._get_field_name()
        filtros = self._build_filters()

        try:
            ctrl = EstadiaController()
            resultados, total = ctrl.buscar(
                termino=termino,
                campo=campo,
                filtros=filtros,
                pagina=self._current_page,
            )
            self._total_results = total
            self._table.load_data(resultados)
            self._results_label.configure(text=f"{total} resultados")
            max_pages = max(1, (total + 49) // 50)
            self._page_label.configure(text=f"Pág. {self._current_page}/{max_pages}")

        except Exception as e:
            logger.error("Error en búsqueda: %s", e)
            messagebox.showerror("Error", str(e))

    def _change_page(self, delta: int):
        new_page = self._current_page + delta
        if new_page < 1:
            return
        max_pages = max(1, (self._total_results + 49) // 50)
        if new_page > max_pages:
            return
        self._current_page = new_page
        self._do_search()

    def _on_row_double_click(self, row: dict):
        """Abre un diálogo de detalle/edición al hacer doble click."""
        if not row:
            return
        self._show_detail_dialog(row)

    def _show_detail_dialog(self, data: dict):
        """Muestra diálogo con detalle de la estadía y opción de editar."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Detalle de Estadía")
        dialog.geometry("600x500")
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        fields = [
            ("ID Estadía", "id"), ("Hotel", "establecimiento"),
            ("Apellido", "apellido"), ("Nombre", "nombre"),
            ("D.N.I.", "dni"), ("Pasaporte", "pasaporte"),
            ("Nacionalidad", "nacionalidad"), ("Procedencia", "procedencia"),
            ("Edad", "edad"), ("Profesión", "profesion"),
            ("Fecha Nac.", "fecha_nacimiento"),
            ("Entrada", "fecha_entrada"), ("Salida", "fecha_salida"),
        ]

        for label, key in fields:
            row_f = ctk.CTkFrame(scroll, fg_color="transparent")
            row_f.pack(fill="x", pady=2)
            ctk.CTkLabel(row_f, text=f"{label}:", font=("", 12, "bold"), width=120, anchor="e").pack(side="left", padx=5)
            ctk.CTkLabel(row_f, text=str(data.get(key, "")), font=("", 12), anchor="w").pack(side="left", padx=5)

        # Historial de la persona
        persona_id = data.get("persona_id")
        if persona_id:
            ctk.CTkLabel(scroll, text="Historial de Estadías", font=("", 14, "bold")).pack(
                anchor="w", pady=(15, 5),
            )
            try:
                estadias = EstadiaDAO.obtener_por_persona(persona_id)
                for est in estadias:
                    info = f"  {est.get('fecha_entrada', '')} al {est.get('fecha_salida', 'presente')} - {est.get('establecimiento', 'S/D')}"
                    ctk.CTkLabel(scroll, text=info, font=("", 11)).pack(anchor="w", padx=10)
            except Exception:
                pass

        ctk.CTkButton(dialog, text="Cerrar", command=dialog.destroy).pack(pady=10)

    def _export_excel(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            title="Exportar a Excel",
        )
        if not filepath:
            return
        try:
            ctrl = ReportController()
            ctrl.exportar_excel(
                filepath,
                filtros=self._build_filters(),
                termino=self._search_entry.get().strip(),
            )
            messagebox.showinfo("Éxito", f"Archivo exportado:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_pdf(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Exportar a PDF",
        )
        if not filepath:
            return
        try:
            ctrl = ReportController()
            ctrl.exportar_pdf(
                filepath,
                filtros=self._build_filters(),
                termino=self._search_entry.get().strip(),
            )
            messagebox.showinfo("Éxito", f"Archivo exportado:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
