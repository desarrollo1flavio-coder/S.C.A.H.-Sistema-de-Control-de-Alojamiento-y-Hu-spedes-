"""Vista de carga manual de huéspedes para S.C.A.H.

Formulario completo con validación en tiempo real para registrar huéspedes.
"""

from datetime import date
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from config.settings import NACIONALIDADES, PROVINCIAS_ARGENTINA
from controllers.auth_controller import SessionInfo
from controllers.huesped_controller import HuespedController
from utils.exceptions import DuplicateRecordError, PermissionDeniedError, ValidationError
from utils.logger import get_logger
from views.components.form_fields import (
    CheckboxWithEntry,
    DatePickerField,
    ValidatedComboBox,
    ValidatedEntry,
)

logger = get_logger("views.manual")


class ManualView(ctk.CTkFrame):
    """Módulo de carga manual de huéspedes."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        session: SessionInfo,
    ) -> None:
        """Inicializa la vista de carga manual.

        Args:
            parent: Frame contenedor.
            session: Sesión del usuario.
        """
        super().__init__(parent, fg_color="transparent")

        self._session = session
        self._controller = HuespedController(session)
        self._fields: dict[str, object] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        """Construye la interfaz del formulario."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            header, text="📋  Carga Manual de Huéspedes",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        # Scrollable form
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        self._build_section_personal(scroll)
        self._build_section_estadia(scroll)
        self._build_section_adicional(scroll)
        self._build_buttons()

    # ── Sección: Datos Personales ────────────────────────────────

    def _build_section_personal(self, parent: ctk.CTkFrame) -> None:
        """Sección de datos personales.

        Args:
            parent: Frame contenedor.
        """
        section = self._section(parent, "Datos Personales")

        row1 = ctk.CTkFrame(section, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        row1.columnconfigure((0, 1), weight=1)

        self._fields["apellido"] = self._add_field(
            row1, "Apellido *", ValidatedEntry, 0, 0,
            placeholder="Ej: González",
        )
        self._fields["nombre"] = self._add_field(
            row1, "Nombre *", ValidatedEntry, 0, 1,
            placeholder="Ej: Juan Carlos",
        )

        row2 = ctk.CTkFrame(section, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        row2.columnconfigure((0, 1, 2), weight=1)

        self._fields["dni"] = self._add_field(
            row2, "DNI", ValidatedEntry, 0, 0,
            placeholder="Ej: 35123456",
        )
        self._fields["pasaporte"] = self._add_field(
            row2, "Pasaporte", ValidatedEntry, 0, 1,
            placeholder="Ej: AAA123456",
        )
        self._fields["edad"] = self._add_field(
            row2, "Edad", ValidatedEntry, 0, 2,
            placeholder="Ej: 30", width=80,
        )

        row2b = ctk.CTkFrame(section, fg_color="transparent")
        row2b.pack(fill="x", pady=2)
        row2b.columnconfigure(0, weight=1)

        self._fields["fecha_nacimiento"] = self._add_field(
            row2b, "Fecha Nacimiento", ValidatedEntry, 0, 0,
            placeholder="DD/MM/AAAA", width=140,
        )

        row3 = ctk.CTkFrame(section, fg_color="transparent")
        row3.pack(fill="x", pady=2)
        row3.columnconfigure((0, 1), weight=1)

        self._fields["nacionalidad"] = self._add_combo(
            row3, "Nacionalidad *", NACIONALIDADES, 0, 0,
        )
        self._fields["procedencia"] = self._add_combo(
            row3, "Procedencia *", PROVINCIAS_ARGENTINA + ["Otro"], 0, 1,
        )

    # ── Sección: Datos de Estadía ────────────────────────────────

    def _build_section_estadia(self, parent: ctk.CTkFrame) -> None:
        """Sección de datos de estadía.

        Args:
            parent: Frame contenedor.
        """
        section = self._section(parent, "Datos de Estadía")

        row1 = ctk.CTkFrame(section, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        row1.columnconfigure((0, 1, 2), weight=1)

        self._fields["habitacion"] = self._add_field(
            row1, "Habitación *", ValidatedEntry, 0, 0,
            placeholder="Ej: 201",
        )
        self._fields["fecha_entrada"] = self._add_date(
            row1, "Fecha Entrada *", 0, 1,
        )
        self._fields["fecha_salida"] = self._add_date(
            row1, "Fecha Salida", 0, 2,
        )

        row2 = ctk.CTkFrame(section, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        row2.columnconfigure((0, 1), weight=1)

        self._fields["destino"] = self._add_field(
            row2, "Destino", ValidatedEntry, 0, 0,
            placeholder="Ej: Buenos Aires",
        )
        self._fields["profesion"] = self._add_field(
            row2, "Profesión", ValidatedEntry, 0, 1,
            placeholder="Ej: Comerciante",
        )

    # ── Sección: Info Adicional ──────────────────────────────────

    def _build_section_adicional(self, parent: ctk.CTkFrame) -> None:
        """Sección de información adicional.

        Args:
            parent: Frame contenedor.
        """
        section = self._section(parent, "Información Adicional")

        row1 = ctk.CTkFrame(section, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        row1.columnconfigure((0, 1), weight=1)

        self._fields["telefono"] = self._add_field(
            row1, "Teléfono", ValidatedEntry, 0, 0,
            placeholder="Ej: 3814567890",
        )

        # Vehículo
        vehiculo_frame = ctk.CTkFrame(row1, fg_color="transparent")
        vehiculo_frame.grid(row=0, column=1, sticky="ew", padx=5)

        ctk.CTkLabel(
            vehiculo_frame, text="Vehículo",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        ).pack(fill="x")

        self._fields["vehiculo"] = CheckboxWithEntry(
            vehiculo_frame, label="Posee vehículo",
            entry_placeholder="Marca, modelo, patente",
        )
        self._fields["vehiculo"].pack(fill="x", pady=(2, 5))

    # ── Botones de Acción ────────────────────────────────────────

    def _build_buttons(self) -> None:
        """Barra de botones."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=30, pady=(5, 20))

        self._msg_label = ctk.CTkLabel(
            bar, text="", font=ctk.CTkFont(size=12),
        )
        self._msg_label.pack(side="left", padx=(0, 20))

        ctk.CTkButton(
            bar, text="Cancelar", width=100, fg_color="transparent",
            border_width=1, hover_color=("gray80", "gray30"),
            command=self._clear_form,
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(
            bar, text="Limpiar", width=100, fg_color="gray50",
            hover_color="gray40", command=self._clear_form,
        ).pack(side="right", padx=(5, 0))

        self._save_btn = ctk.CTkButton(
            bar, text="💾  Guardar", width=140, height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._handle_save,
        )
        self._save_btn.pack(side="right", padx=(5, 0))

    # ── Helpers ──────────────────────────────────────────────────

    def _section(self, parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
        """Crea una sección con título.

        Args:
            parent: Frame contenedor.
            title: Título de la sección.

        Returns:
            Frame de la sección.
        """
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.pack(fill="x", pady=(10, 5))

        ctk.CTkLabel(
            frame, text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(fill="x", padx=15, pady=(10, 5))

        return frame

    def _add_field(
        self, parent: ctk.CTkFrame, label: str, field_cls: type,
        row: int, col: int, *, placeholder: str = "",
        validator: Optional[object] = None, width: Optional[int] = None,
    ) -> ValidatedEntry:
        """Agrega un campo de texto al formulario.

        Args:
            parent: Frame contenedor.
            label: Etiqueta del campo.
            field_cls: Clase del widget.
            row: Fila del grid.
            col: Columna del grid.
            placeholder: Texto placeholder.
            validator: Función validadora.
            width: Ancho del campo.

        Returns:
            Widget creado.
        """
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="ew", padx=5)

        # Detectar si es campo obligatorio (*)
        required = label.endswith(" *")
        label_clean = label.rstrip(" *") if required else label

        entry = field_cls(
            frame,
            label=label_clean,
            required=required,
            placeholder=placeholder,
            validator=validator,
        )
        entry.pack(fill="x", pady=(0, 5))
        return entry

    def _add_combo(
        self, parent: ctk.CTkFrame, label: str, values: list[str],
        row: int, col: int, *, validator: Optional[object] = None,
    ) -> ValidatedComboBox:
        """Agrega un combo box al formulario.

        Args:
            parent: Frame contenedor.
            label: Etiqueta.
            values: Valores posibles.
            row: Fila.
            col: Columna.
            validator: Validador.

        Returns:
            Widget creado.
        """
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="ew", padx=5)

        # Detectar si es campo obligatorio (*)
        required = label.endswith(" *")
        label_clean = label.rstrip(" *") if required else label

        combo = ValidatedComboBox(
            frame,
            label=label_clean,
            values=values,
            required=required,
        )
        combo.pack(fill="x", pady=(0, 5))
        return combo

    def _add_date(
        self, parent: ctk.CTkFrame, label: str, row: int, col: int,
    ) -> DatePickerField:
        """Agrega un campo de fecha.

        Args:
            parent: Frame contenedor.
            label: Etiqueta.
            row: Fila.
            col: Columna.

        Returns:
            Widget de fecha.
        """
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="ew", padx=5)

        # Detectar si es campo obligatorio (*)
        required = label.endswith(" *")
        label_clean = label.rstrip(" *") if required else label

        picker = DatePickerField(
            frame,
            label=label_clean,
            required=required,
        )
        picker.pack(fill="x", pady=(0, 5))
        return picker

    # ── Actions ──────────────────────────────────────────────────

    def _collect_data(self) -> dict:
        """Recolecta datos del formulario.

        Returns:
            Diccionario con los datos del formulario.
        """
        data: dict = {}

        for key in ("apellido", "nombre", "dni", "pasaporte", "edad",
                     "fecha_nacimiento", "habitacion", "destino",
                     "profesion", "telefono"):
            field = self._fields.get(key)
            if field and hasattr(field, "get"):
                val = field.get().strip()
                if val:
                    data[key] = val

        for key in ("nacionalidad", "procedencia"):
            field = self._fields.get(key)
            if field and hasattr(field, "get"):
                val = field.get().strip()
                if val:
                    data[key] = val

        # Edad como entero
        if "edad" in data:
            try:
                data["edad"] = int(data["edad"])
            except ValueError:
                data["edad"] = None

        # Fecha de nacimiento
        if "fecha_nacimiento" in data:
            from utils.excel_parser import ExcelParser
            parsed = ExcelParser._parse_date(data["fecha_nacimiento"])
            if parsed:
                data["fecha_nacimiento"] = parsed
            else:
                data.pop("fecha_nacimiento", None)

        # Fechas
        fecha_entrada = self._fields.get("fecha_entrada")
        if fecha_entrada:
            val = fecha_entrada.get_date()
            data["fecha_entrada"] = val if val else date.today()

        fecha_salida = self._fields.get("fecha_salida")
        if fecha_salida:
            val = fecha_salida.get_date()
            if val:
                data["fecha_salida"] = val

        # Vehículo
        vehiculo = self._fields.get("vehiculo")
        if vehiculo:
            data["vehiculo_tiene"] = vehiculo.is_checked()
            if vehiculo.is_checked():
                data["vehiculo_datos"] = vehiculo.get_text()

        return data

    def _handle_save(self) -> None:
        """Guarda el huésped."""
        data = self._collect_data()

        # Validaciones básicas en la UI
        missing = []
        for field in ("apellido", "nombre", "nacionalidad", "procedencia", "habitacion"):
            if field not in data or not data.get(field):
                missing.append(field.capitalize())

        if not data.get("dni") and not data.get("pasaporte"):
            missing.append("DNI o Pasaporte")

        if missing:
            self._show_msg(f"Campos obligatorios faltantes: {', '.join(missing)}")
            return

        try:
            huesped_id = self._controller.crear(data)
            self._show_msg(
                f"✅ Huésped registrado exitosamente (ID: {huesped_id})",
                error=False,
            )
            self.after(1500, self._clear_form)

        except DuplicateRecordError as e:
            self._show_msg(f"⚠️ {e.message}")
        except ValidationError as e:
            self._show_msg(f"⚠️ Error de validación: {e.message}")
        except PermissionDeniedError:
            self._show_msg("🔒 Sin permisos para registrar huéspedes")
        except Exception as e:
            logger.error("Error al guardar huésped: %s", e)
            self._show_msg(f"❌ Error interno: {e}")

    def _clear_form(self) -> None:
        """Limpia todos los campos del formulario."""
        for key, field in self._fields.items():
            if hasattr(field, "delete"):
                field.delete(0, "end")
            elif hasattr(field, "set"):
                field.set("")
            elif isinstance(field, CheckboxWithEntry):
                field._checkbox.deselect()
                field._entry.delete(0, "end")
                field._entry.configure(state="disabled")
            elif isinstance(field, DatePickerField):
                if hasattr(field, "_entry") and hasattr(field._entry, "delete"):
                    try:
                        field._entry.configure(state="normal")
                        field._entry.delete(0, "end")
                    except Exception:
                        pass

        self._msg_label.configure(text="")

    def _show_msg(self, msg: str, error: bool = True) -> None:
        """Muestra un mensaje.

        Args:
            msg: Texto del mensaje.
            error: True=rojo, False=verde.
        """
        color = ("red", "#FF6B6B") if error else ("green", "#4ECB71")
        self._msg_label.configure(text=msg, text_color=color)
