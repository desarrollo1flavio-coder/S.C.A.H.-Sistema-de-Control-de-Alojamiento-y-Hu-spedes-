"""Vista de importación de archivos Excel para S.C.A.H.

Permite seleccionar, previsualizar e importar datos de huéspedes desde Excel.
"""

import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from config.settings import ALLOWED_EXTENSIONS, PREVIEW_ROWS
from controllers.auth_controller import SessionInfo
from utils.logger import get_logger
from views.components.data_table import DataTable

logger = get_logger("views.import")


class ImportView(ctk.CTkFrame):
    """Módulo de importación de archivos Excel."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        session: SessionInfo,
    ) -> None:
        """Inicializa la vista de importación.

        Args:
            parent: Frame contenedor.
            session: Sesión del usuario.
        """
        super().__init__(parent, fg_color="transparent")

        self._session = session
        self._file_path: Optional[Path] = None
        self._preview_data: list[dict] = []
        self._all_data: list[dict] = []
        self._import_summary: dict = {}
        self._is_importing = False

        self._build_ui()

    def _build_ui(self) -> None:
        """Construye la interfaz de importación."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            header, text="📂  Importar Archivo Excel",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        # File selector
        file_frame = ctk.CTkFrame(self, corner_radius=10)
        file_frame.pack(fill="x", padx=30, pady=(0, 10))

        inner = ctk.CTkFrame(file_frame, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            inner, text="Archivo:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        self._file_label = ctk.CTkLabel(
            inner, text="Ningún archivo seleccionado",
            font=ctk.CTkFont(size=12), text_color=("gray50", "gray50"),
        )
        self._file_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            inner, text="📁 Seleccionar Archivo", width=180,
            command=self._select_file,
        ).pack(side="right")

        # Content area (preview + summary)
        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        self._show_placeholder()

        # Bottom bar
        self._build_bottom_bar()

    def _show_placeholder(self) -> None:
        """Muestra placeholder cuando no hay archivo seleccionado."""
        for w in self._content_frame.winfo_children():
            w.destroy()

        placeholder = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        placeholder.pack(fill="both", expand=True)

        center = ctk.CTkFrame(placeholder, fg_color="transparent")
        center.place(relx=0.5, rely=0.4, anchor="center")

        ctk.CTkLabel(
            center, text="📄", font=ctk.CTkFont(size=48),
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            center, text="Seleccione un archivo Excel (.xlsx, .xls)",
            font=ctk.CTkFont(size=16),
            text_color=("gray50", "gray50"),
        ).pack()

        ctk.CTkLabel(
            center,
            text="El sistema mapeará automáticamente las columnas\n"
                 "e identificará los registros válidos.",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40"),
        ).pack(pady=(10, 0))

    def _build_bottom_bar(self) -> None:
        """Barra inferior con progreso y botones."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=30, pady=(5, 20))

        self._msg_label = ctk.CTkLabel(
            bar, text="", font=ctk.CTkFont(size=12),
        )
        self._msg_label.pack(side="left")

        self._import_btn = ctk.CTkButton(
            bar, text="🚀  Importar Datos", width=160, height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._handle_import, state="disabled",
        )
        self._import_btn.pack(side="right")

        self._progress = ctk.CTkProgressBar(bar, height=4)
        self._progress.pack(fill="x", side="bottom", pady=(10, 0))
        self._progress.set(0)

    # ── File Selection ───────────────────────────────────────────

    def _select_file(self) -> None:
        """Abre diálogo para seleccionar archivo Excel."""
        filetypes = [
            ("Archivos Excel", "*.xlsx *.xls"),
            ("Todos los archivos", "*.*"),
        ]
        path = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=filetypes,
            parent=self,
        )
        if not path:
            return

        path_obj = Path(path)
        if path_obj.suffix.lower() not in ALLOWED_EXTENSIONS:
            self._show_msg("⚠️ Formato no soportado. Use .xlsx o .xls")
            return

        self._file_path = path_obj
        self._file_label.configure(
            text=f"📄 {path_obj.name}",
            text_color=("gray10", "gray90"),
        )
        self._show_msg("")

        # Precargar en hilo
        thread = threading.Thread(target=self._load_preview, daemon=True)
        thread.start()

    def _load_preview(self) -> None:
        """Carga datos del archivo en hilo separado."""
        self.after(0, lambda: self._show_msg("Leyendo archivo..."))
        self.after(0, lambda: self._progress.configure(mode="indeterminate"))
        self.after(0, lambda: self._progress.start())

        try:
            from utils.excel_parser import ExcelParser

            parser = ExcelParser(self._file_path)
            result = parser.parse()

            self._all_data = result.get("valid_rows", [])
            self._preview_data = self._all_data[:PREVIEW_ROWS]
            self._import_summary = {
                "total_rows": result.get("total_rows", 0),
                "valid": len(self._all_data),
                "errors": len(result.get("errors", [])),
                "duplicates": len(result.get("duplicates", [])),
                "skipped": result.get("skipped", 0),
                "error_details": result.get("errors", []),
                "sheet_count": result.get("sheet_count", 1),
                "sheet_names": result.get("sheet_names", []),
            }

            self.after(0, self._display_preview)

        except ImportError:
            self.after(0, lambda: self._show_msg(
                "⚠️ Módulo de importación no disponible. "
                "Verificar utils/excel_parser.py"
            ))
        except Exception as e:
            logger.error("Error al leer archivo: %s", e)
            msg = f"❌ Error al leer: {e}"
            self.after(0, lambda msg=msg: self._show_msg(msg))
        finally:
            self.after(0, lambda: self._progress.stop())
            self.after(0, lambda: self._progress.configure(mode="determinate"))
            self.after(0, lambda: self._progress.set(0))

    def _display_preview(self) -> None:
        """Muestra la previsualización y resumen."""
        for w in self._content_frame.winfo_children():
            w.destroy()

        # Split: left (preview) + right (summary)
        self._content_frame.columnconfigure(0, weight=3)
        self._content_frame.columnconfigure(1, weight=1)
        self._content_frame.rowconfigure(0, weight=1)

        # Preview table
        preview_frame = ctk.CTkFrame(self._content_frame, corner_radius=10)
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        ctk.CTkLabel(
            preview_frame,
            text=f"Vista previa ({min(PREVIEW_ROWS, len(self._all_data))} de {len(self._all_data)} registros)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(fill="x", padx=15, pady=(10, 5))

        if self._preview_data:
            # Unificar DNI y Pasaporte en columna "Documento"
            for rec in self._preview_data:
                dni = rec.pop("dni", None) or ""
                pas = rec.pop("pasaporte", None) or ""
                if dni and pas:
                    rec["documento"] = f"DNI: {dni} / PAS: {pas}"
                elif dni:
                    rec["documento"] = f"DNI: {dni}"
                elif pas:
                    rec["documento"] = f"PAS: {pas}"
                else:
                    rec["documento"] = "S/N"

            columns = [c for c in self._preview_data[0].keys() if not c.startswith("_")]
            col_defs = [(col, col.replace("_", " ").title(), 120) for col in columns]

            table = DataTable(preview_frame, columns=col_defs, page_size=PREVIEW_ROWS)
            table.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            table.load_data(self._preview_data)

        # Summary panel
        summary_frame = ctk.CTkFrame(self._content_frame, corner_radius=10)
        summary_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        ctk.CTkLabel(
            summary_frame, text="Resumen",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(fill="x", padx=15, pady=(15, 10))

        s = self._import_summary
        stats = [
            ("📋 Hojas leídas:", str(s.get("sheet_count", 1)), "#64B5F6"),
            ("Total filas leídas:", str(s.get("total_rows", 0)), "gray90"),
            ("✅ Válidos:", str(s.get("valid", 0)), "#4ECB71"),
            ("❌ Errores:", str(s.get("errors", 0)), "#FF6B6B"),
            ("⚠️ Duplicados:", str(s.get("duplicates", 0)), "#FFA500"),
            ("⏭️ Omitidas:", str(s.get("skipped", 0)), "gray60"),
        ]

        for label, value, color in stats:
            row = ctk.CTkFrame(summary_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)

            ctk.CTkLabel(
                row, text=label, font=ctk.CTkFont(size=12), anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                row, text=value,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=color,
            ).pack(side="right")

        # Error log
        if s.get("error_details"):
            ctk.CTkLabel(
                summary_frame, text="Errores detectados:",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(fill="x", padx=15, pady=(15, 5))

            error_text = ctk.CTkTextbox(summary_frame, height=150, font=ctk.CTkFont(size=10))
            error_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))

            for err in s["error_details"][:50]:
                if isinstance(err, dict):
                    error_text.insert("end", f"Fila {err.get('row', '?')}: {err.get('error', '')}\n")
                else:
                    error_text.insert("end", f"{err}\n")
            error_text.configure(state="disabled")

        # Enable import button
        if s.get("valid", 0) > 0:
            self._import_btn.configure(state="normal")
            self._show_msg(
                f"✅ {s['valid']} registros listos para importar",
                error=False,
            )
        else:
            self._show_msg("⚠️ No hay registros válidos para importar")

    # ── Import ───────────────────────────────────────────────────

    def _handle_import(self) -> None:
        """Inicia la importación de datos."""
        if self._is_importing or not self._all_data:
            return

        valid_count = len(self._all_data)
        confirm = messagebox.askyesno(
            "Confirmar Importación",
            f"¿Importar {valid_count} registros a la base de datos?\n\n"
            "Los registros duplicados serán omitidos.",
            parent=self,
        )
        if not confirm:
            return

        self._is_importing = True
        self._import_btn.configure(state="disabled", text="Importando...")

        thread = threading.Thread(target=self._import_thread, daemon=True)
        thread.start()

    def _import_thread(self) -> None:
        """Hilo de importación."""
        from controllers.huesped_controller import HuespedController

        controller = HuespedController(self._session)
        total = len(self._all_data)
        ok, errors = 0, 0

        for i, row in enumerate(self._all_data, 1):
            try:
                row["usuario_carga"] = self._session.username
                controller.crear(row)
                ok += 1
            except Exception as e:
                errors += 1
                logger.warning("Error al importar fila %d: %s", i, e)

            # Actualizar progreso
            progress = i / total
            self.after(0, lambda p=progress: self._progress.set(p))
            self.after(
                0,
                lambda o=ok, e=errors, i_=i: self._show_msg(
                    f"Importando... {i_}/{total} — ✅ {o} — ❌ {e}",
                    error=False,
                ),
            )

        # Finalizar
        self.after(0, lambda: self._import_complete(ok, errors))

    def _import_complete(self, ok: int, errors: int) -> None:
        """Completa la importación.

        Args:
            ok: Registros importados.
            errors: Registros con error.
        """
        self._is_importing = False
        self._import_btn.configure(text="🚀  Importar Datos")
        self._progress.set(1)

        if errors == 0:
            self._show_msg(
                f"✅ Importación completa: {ok} registros importados",
                error=False,
            )
        else:
            self._show_msg(
                f"⚠️ Importación finalizada: {ok} importados, {errors} errores",
            )

        logger.info(
            "Importación completada: %d OK, %d errores — usuario: %s",
            ok, errors, self._session.username,
        )

    def _show_msg(self, msg: str, error: bool = True) -> None:
        """Muestra mensaje.

        Args:
            msg: Texto.
            error: True=rojo, False=verde.
        """
        color = ("red", "#FF6B6B") if error else ("green", "#4ECB71")
        self._msg_label.configure(text=msg, text_color=color)
