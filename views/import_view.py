"""Vista de importación de Excel para S.C.A.H. v2."""

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
                    f"No se detectaron las siguientes columnas obligatorias:\n\n{faltantes}\n\n"
                    "La importación podría tener errores.",
                )
        except Exception as e:
            logger.error("Error al cargar preview: %s", e)
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
            self._btn_import.configure(state="disabled")

    def _show_preview(self):
        if not self._preview_data:
            return

        # Mostrar mapeo
        self._mapeo_text.configure(state="normal")
        self._mapeo_text.delete("1.0", "end")
        for col_excel, campo_interno in self._preview_data["mapeo"].items():
            self._mapeo_text.insert("end", f"  {col_excel}  ->  {campo_interno}\n")
        if self._preview_data["columnas_faltantes"]:
            self._mapeo_text.insert("end", f"\n  FALTANTES: {self._preview_data['columnas_faltantes']}\n")
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
            f"Se importarán {self._preview_data['total_filas']} filas.\n\n"
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
            f"Importación completada:\n\n"
            f"  Estadías creadas: {stats['estadias_creadas']}\n"
            f"  Total filas: {stats['total_filas']}\n"
            f"  Errores: {errores}"
        )

        if errores > 0:
            msg += f"\n\nPrimeros errores:"
            for err in stats["errores"][:5]:
                msg += f"\n  Fila {err.get('fila', '?')}: {err.get('errores', ['?'])[0]}"
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
