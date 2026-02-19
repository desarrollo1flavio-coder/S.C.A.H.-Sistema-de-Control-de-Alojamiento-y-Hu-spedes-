"""Script de reconstrucción S.C.A.H. v2 - Fase 3b.

Views: Import + Manual + Search
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = {}

# ============================================================
# views/import_view.py  — REESCRITURA COMPLETA
# ============================================================
FILES["views/import_view.py"] = '''"""Vista de importación de Excel para S.C.A.H. v2."""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional

from controllers.import_controller import ImportController
from utils.excel_parser import preview_archivo
from views.components.data_table import DataTable
from utils.logger import get_logger

logger = get_logger("views.import")


class ImportView(ctk.CTkFrame):
    """Vista completa de importación de archivos Excel."""

    def __init__(self, parent, app_controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app_controller
        self._filepath: Optional[str] = None
        self._preview_data: Optional[dict] = None
        self._import_running = False
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="Importar Excel", font=("", 24, "bold")).pack(side="left")

        # Panel de selección de archivo
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(file_frame, text="Archivo:", font=("", 13)).pack(
            side="left", padx=(15, 5), pady=10,
        )
        self._file_label = ctk.CTkLabel(
            file_frame, text="Ningún archivo seleccionado",
            font=("", 12), text_color="gray",
        )
        self._file_label.pack(side="left", padx=5, pady=10, fill="x", expand=True)

        self._btn_select = ctk.CTkButton(
            file_frame, text="Seleccionar Archivo",
            width=160, command=self._select_file,
        )
        self._btn_select.pack(side="right", padx=15, pady=10)

        # Panel de mapeo de columnas
        mapeo_frame = ctk.CTkFrame(self)
        mapeo_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(mapeo_frame, text="Mapeo de Columnas Detectado", font=("", 14, "bold")).pack(
            anchor="w", padx=15, pady=(10, 5),
        )
        self._mapeo_text = ctk.CTkTextbox(mapeo_frame, height=100, state="disabled")
        self._mapeo_text.pack(fill="x", padx=15, pady=(0, 10))

        # Preview de datos
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(fill="both", expand=True, padx=20, pady=5)

        ctk.CTkLabel(preview_frame, text="Vista Previa", font=("", 14, "bold")).pack(
            anchor="w", padx=15, pady=(10, 5),
        )

        preview_columns = [
            {"key": "establecimiento", "text": "HOTEL", "width": 120},
            {"key": "apellido", "text": "APELLIDO", "width": 120},
            {"key": "nombre", "text": "NOMBRE", "width": 100},
            {"key": "dni", "text": "DNI/PAS.", "width": 90},
            {"key": "nacionalidad", "text": "NACIONALIDAD", "width": 100},
            {"key": "procedencia", "text": "PROCEDENCIA", "width": 100},
            {"key": "edad", "text": "EDAD", "width": 50},
            {"key": "fecha_entrada", "text": "ENTRADA", "width": 90},
            {"key": "fecha_salida", "text": "SALIDA", "width": 90},
            {"key": "profesion", "text": "PROFESIÓN", "width": 90},
        ]
        self._preview_table = DataTable(preview_frame, columns=preview_columns)
        self._preview_table.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Panel de importación
        import_frame = ctk.CTkFrame(self)
        import_frame.pack(fill="x", padx=20, pady=(5, 10))

        self._progress_bar = ctk.CTkProgressBar(import_frame)
        self._progress_bar.pack(fill="x", padx=15, pady=(10, 5))
        self._progress_bar.set(0)

        self._progress_label = ctk.CTkLabel(
            import_frame, text="Seleccione un archivo para comenzar",
            font=("", 12), text_color="gray",
        )
        self._progress_label.pack(padx=15, pady=2)

        btn_frame = ctk.CTkFrame(import_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(5, 10))

        self._btn_import = ctk.CTkButton(
            btn_frame, text="Importar Datos",
            font=("", 14, "bold"), height=40, width=200,
            state="disabled",
            command=self._start_import,
        )
        self._btn_import.pack(side="right")

        self._btn_cancel = ctk.CTkButton(
            btn_frame, text="Cancelar",
            font=("", 14), height=40, width=120,
            fg_color="gray40",
            state="disabled",
            command=self._cancel_import,
        )
        self._btn_cancel.pack(side="right", padx=10)

    def _select_file(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if not filepath:
            return

        self._filepath = filepath
        self._file_label.configure(
            text=os.path.basename(filepath),
            text_color=("gray10", "gray90"),
        )

        try:
            self._preview_data = preview_archivo(filepath)
            self._show_preview()
            self._btn_import.configure(state="normal")

            if self._preview_data["columnas_faltantes"]:
                faltantes = ", ".join(self._preview_data["columnas_faltantes"])
                messagebox.showwarning(
                    "Columnas Faltantes",
                    f"No se detectaron las siguientes columnas obligatorias:\\n\\n{faltantes}\\n\\n"
                    "La importación podría tener errores.",
                )
        except Exception as e:
            logger.error("Error al cargar preview: %s", e)
            messagebox.showerror("Error", f"No se pudo leer el archivo:\\n{e}")
            self._btn_import.configure(state="disabled")

    def _show_preview(self):
        if not self._preview_data:
            return

        # Mostrar mapeo
        self._mapeo_text.configure(state="normal")
        self._mapeo_text.delete("1.0", "end")
        for col_excel, campo_interno in self._preview_data["mapeo"].items():
            self._mapeo_text.insert("end", f"  {col_excel}  ->  {campo_interno}\\n")
        if self._preview_data["columnas_faltantes"]:
            self._mapeo_text.insert("end", f"\\n  FALTANTES: {self._preview_data['columnas_faltantes']}\\n")
        self._mapeo_text.configure(state="disabled")

        # Mostrar preview en tabla
        self._preview_table.load_data(self._preview_data["filas_preview"])

        self._progress_label.configure(
            text=f"Archivo cargado: {self._preview_data['total_filas']} filas detectadas",
            text_color=("gray10", "gray90"),
        )

    def _start_import(self):
        if not self._filepath or self._import_running:
            return

        result = messagebox.askyesno(
            "Confirmar Importación",
            f"Se importarán {self._preview_data['total_filas']} filas.\\n\\n"
            "¿Desea continuar?",
        )
        if not result:
            return

        self._import_running = True
        self._btn_import.configure(state="disabled")
        self._btn_select.configure(state="disabled")
        self._btn_cancel.configure(state="normal")

        thread = threading.Thread(target=self._run_import, daemon=True)
        thread.start()

    def _run_import(self):
        try:
            usuario = "sistema"
            if self._app and hasattr(self._app, "auth_controller"):
                usuario = self._app.auth_controller.current_user

            ctrl = ImportController(usuario=usuario)
            stats = ctrl.importar(
                filepath=self._filepath,
                on_progress=self._update_progress,
            )

            self.after(0, lambda: self._import_complete(stats))

        except Exception as e:
            self.after(0, lambda: self._import_error(str(e)))

    def _update_progress(self, current: int, total: int, msg: str):
        def update():
            self._progress_bar.set(current / max(total, 1))
            self._progress_label.configure(text=msg)
        self.after(0, update)

    def _import_complete(self, stats: dict):
        self._import_running = False
        self._btn_import.configure(state="normal")
        self._btn_select.configure(state="normal")
        self._btn_cancel.configure(state="disabled")
        self._progress_bar.set(1.0)

        errores = len(stats.get("errores", []))
        msg = (
            f"Importación completada:\\n\\n"
            f"  Estadías creadas: {stats['estadias_creadas']}\\n"
            f"  Total filas: {stats['total_filas']}\\n"
            f"  Errores: {errores}"
        )

        if errores > 0:
            msg += f"\\n\\nPrimeros errores:"
            for err in stats["errores"][:5]:
                msg += f"\\n  Fila {err.get('fila', '?')}: {err.get('errores', ['?'])[0]}"
            messagebox.showwarning("Importación con Errores", msg)
        else:
            messagebox.showinfo("Importación Exitosa", msg)

        if self._app and hasattr(self._app, "status_bar"):
            self._app.status_bar.set_success(
                f"Importación: {stats['estadias_creadas']} estadías creadas"
            )
        if self._app and hasattr(self._app, "refresh_dashboard"):
            self._app.refresh_dashboard()

    def _import_error(self, error_msg: str):
        self._import_running = False
        self._btn_import.configure(state="normal")
        self._btn_select.configure(state="normal")
        self._btn_cancel.configure(state="disabled")
        self._progress_bar.set(0)

        messagebox.showerror("Error de Importación", error_msg)
        if self._app and hasattr(self._app, "status_bar"):
            self._app.status_bar.set_error(f"Error: {error_msg[:80]}")

    def _cancel_import(self):
        self._import_running = False
        self._progress_label.configure(text="Importación cancelada")
        self._btn_cancel.configure(state="disabled")
'''

# ============================================================
# views/manual_view.py
# ============================================================
FILES["views/manual_view.py"] = '''"""Vista de carga manual de huéspedes para S.C.A.H. v2."""

import customtkinter as ctk
from datetime import date, datetime
from tkinter import messagebox

from controllers.persona_controller import PersonaController
from controllers.estadia_controller import EstadiaController
from views.components.form_fields import LabeledEntry, LabeledComboBox
from config.settings import NACIONALIDADES
from utils.logger import get_logger

logger = get_logger("views.manual")


class ManualView(ctk.CTkFrame):
    """Formulario de carga manual de persona + estadía."""

    def __init__(self, parent, app_controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app_controller
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="Carga Manual de Huésped", font=("", 24, "bold")).pack(side="left")

        # Scrollable form
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        # Sección: Datos Personales
        ctk.CTkLabel(scroll, text="Datos Personales", font=("", 16, "bold")).pack(
            anchor="w", pady=(10, 5),
        )

        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        row1.columnconfigure((0, 1, 2, 3), weight=1)

        self._f_apellido = LabeledEntry(row1, "Apellido", required=True)
        self._f_apellido.grid(row=0, column=0, sticky="ew", padx=5)

        self._f_nombre = LabeledEntry(row1, "Nombre", required=True)
        self._f_nombre.grid(row=0, column=1, sticky="ew", padx=5)

        self._f_dni = LabeledEntry(row1, "D.N.I.", placeholder="Sin puntos")
        self._f_dni.grid(row=0, column=2, sticky="ew", padx=5)

        self._f_pasaporte = LabeledEntry(row1, "Pasaporte")
        self._f_pasaporte.grid(row=0, column=3, sticky="ew", padx=5)

        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        row2.columnconfigure((0, 1, 2, 3), weight=1)

        self._f_nacionalidad = LabeledComboBox(row2, "Nacionalidad", NACIONALIDADES, "Argentina")
        self._f_nacionalidad.grid(row=0, column=0, sticky="ew", padx=5)

        self._f_procedencia = LabeledEntry(row2, "Procedencia")
        self._f_procedencia.grid(row=0, column=1, sticky="ew", padx=5)

        self._f_fecha_nac = LabeledEntry(row2, "Fecha Nacimiento", placeholder="DD/MM/AAAA")
        self._f_fecha_nac.grid(row=0, column=2, sticky="ew", padx=5)

        self._f_edad = LabeledEntry(row2, "Edad")
        self._f_edad.grid(row=0, column=3, sticky="ew", padx=5)

        row3 = ctk.CTkFrame(scroll, fg_color="transparent")
        row3.pack(fill="x", pady=2)
        row3.columnconfigure((0, 1), weight=1)

        self._f_profesion = LabeledEntry(row3, "Profesión")
        self._f_profesion.grid(row=0, column=0, sticky="ew", padx=5)

        self._f_telefono = LabeledEntry(row3, "Teléfono")
        self._f_telefono.grid(row=0, column=1, sticky="ew", padx=5)

        # Sección: Datos de Estadía
        ctk.CTkLabel(scroll, text="Datos de Estadía", font=("", 16, "bold")).pack(
            anchor="w", pady=(20, 5),
        )

        row4 = ctk.CTkFrame(scroll, fg_color="transparent")
        row4.pack(fill="x", pady=2)
        row4.columnconfigure((0, 1, 2, 3), weight=1)

        self._f_establecimiento = LabeledEntry(row4, "Hotel / Establecimiento", required=True)
        self._f_establecimiento.grid(row=0, column=0, sticky="ew", padx=5)

        self._f_habitacion = LabeledEntry(row4, "Habitación")
        self._f_habitacion.grid(row=0, column=1, sticky="ew", padx=5)

        self._f_entrada = LabeledEntry(row4, "Fecha Entrada", required=True, placeholder="DD/MM/AAAA")
        self._f_entrada.grid(row=0, column=2, sticky="ew", padx=5)

        self._f_salida = LabeledEntry(row4, "Fecha Salida", placeholder="DD/MM/AAAA")
        self._f_salida.grid(row=0, column=3, sticky="ew", padx=5)

        row5 = ctk.CTkFrame(scroll, fg_color="transparent")
        row5.pack(fill="x", pady=2)
        row5.columnconfigure((0, 1), weight=1)

        self._f_destino = LabeledEntry(row5, "Destino")
        self._f_destino.grid(row=0, column=0, sticky="ew", padx=5)

        self._f_vehiculo = LabeledEntry(row5, "Datos Vehículo (opcional)")
        self._f_vehiculo.grid(row=0, column=1, sticky="ew", padx=5)

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(
            btn_frame, text="Guardar Huésped",
            font=("", 14, "bold"), height=40, width=200,
            command=self._save,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame, text="Limpiar Formulario",
            font=("", 14), height=40, width=160,
            fg_color="gray40",
            command=self._clear_form,
        ).pack(side="right", padx=10)

    def _parse_fecha(self, texto: str) -> str | None:
        """Convierte DD/MM/AAAA a AAAA-MM-DD."""
        if not texto.strip():
            return None
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def _save(self):
        usuario = "sistema"
        if self._app and hasattr(self._app, "auth_controller"):
            usuario = self._app.auth_controller.current_user

        # Validar campos requeridos
        apellido = self._f_apellido.get()
        nombre = self._f_nombre.get()
        if not apellido or not nombre:
            messagebox.showerror("Error", "Apellido y Nombre son obligatorios")
            return

        dni = self._f_dni.get() or None
        pasaporte = self._f_pasaporte.get() or None
        if not dni and not pasaporte:
            messagebox.showerror("Error", "Debe ingresar al menos DNI o Pasaporte")
            return

        fecha_entrada = self._parse_fecha(self._f_entrada.get())
        if not fecha_entrada:
            messagebox.showerror("Error", "La fecha de entrada es obligatoria (DD/MM/AAAA)")
            return

        fecha_salida = self._parse_fecha(self._f_salida.get())
        fecha_nac = self._parse_fecha(self._f_fecha_nac.get())

        edad = None
        if self._f_edad.get():
            try:
                edad = int(float(self._f_edad.get()))
            except ValueError:
                pass

        vehiculo_datos = self._f_vehiculo.get() or None

        try:
            persona_ctrl = PersonaController(usuario)
            estadia_ctrl = EstadiaController(usuario)

            # Crear o encontrar persona
            datos_persona = {
                "nacionalidad": self._f_nacionalidad.get() or "Argentina",
                "procedencia": self._f_procedencia.get() or "S/D",
                "apellido": apellido,
                "nombre": nombre,
                "dni": dni,
                "pasaporte": pasaporte,
                "fecha_nacimiento": fecha_nac,
                "profesion": self._f_profesion.get() or None,
                "telefono": self._f_telefono.get() or None,
            }
            persona_id = persona_ctrl.obtener_o_crear(datos_persona)

            # Crear estadía
            datos_estadia = {
                "persona_id": persona_id,
                "establecimiento": self._f_establecimiento.get() or None,
                "habitacion": self._f_habitacion.get() or "S/N",
                "edad": edad,
                "fecha_entrada": fecha_entrada,
                "fecha_salida": fecha_salida,
                "destino": self._f_destino.get() or None,
                "vehiculo_tiene": bool(vehiculo_datos),
                "vehiculo_datos": vehiculo_datos,
                "usuario_carga": usuario,
            }
            estadia_ctrl.crear(datos_estadia)

            messagebox.showinfo("Éxito", f"Huésped {apellido}, {nombre} registrado correctamente")
            self._clear_form()

            if self._app and hasattr(self._app, "status_bar"):
                self._app.status_bar.set_success(f"Huésped registrado: {apellido}, {nombre}")
            if self._app and hasattr(self._app, "refresh_dashboard"):
                self._app.refresh_dashboard()

        except Exception as e:
            logger.error("Error al guardar huésped: %s", e)
            messagebox.showerror("Error", str(e))

    def _clear_form(self):
        for field in [
            self._f_apellido, self._f_nombre, self._f_dni, self._f_pasaporte,
            self._f_procedencia, self._f_fecha_nac, self._f_edad,
            self._f_profesion, self._f_telefono, self._f_establecimiento,
            self._f_habitacion, self._f_entrada, self._f_salida,
            self._f_destino, self._f_vehiculo,
        ]:
            field.clear()
        self._f_nacionalidad.set("Argentina")
'''

# ============================================================
# views/search_view.py
# ============================================================
FILES["views/search_view.py"] = '''"""Vista de búsqueda de huéspedes para S.C.A.H. v2."""

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
            messagebox.showinfo("Éxito", f"Archivo exportado:\\n{filepath}")
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
            messagebox.showinfo("Éxito", f"Archivo exportado:\\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
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
    print("S.C.A.H. v2 - Fase 3b: Import + Manual + Search")
    print("=" * 60)
    write_all()
    print("\nFase 3b completada.")
