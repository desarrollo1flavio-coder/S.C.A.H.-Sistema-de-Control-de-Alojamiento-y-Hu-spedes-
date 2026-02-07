"""Campos de formulario con validación visual para S.C.A.H.

Componentes reutilizables: entrada validada, combo con autocompletado,
selector de fecha y checkbox condicional.
"""

from datetime import date
from typing import Callable, Optional

import customtkinter as ctk

from utils.logger import get_logger

logger = get_logger("components.form_fields")


class ValidatedEntry(ctk.CTkFrame):
    """Campo de texto con validación visual (borde rojo si hay error)."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        label: str,
        required: bool = False,
        validator: Optional[Callable[[str], tuple[bool, str]]] = None,
        placeholder: str = "",
        **kwargs,
    ) -> None:
        """Inicializa el campo validado.

        Args:
            master: Widget padre.
            label: Etiqueta del campo.
            required: Si True, marca el campo como obligatorio (*).
            validator: Función de validación que retorna (válido, error).
            placeholder: Texto placeholder.
        """
        super().__init__(master, fg_color="transparent", **kwargs)

        self._validator = validator
        self._required = required
        self._is_valid = True

        # Label
        label_text = f"{label} *" if required else label
        self._label = ctk.CTkLabel(
            self,
            text=label_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        )
        self._label.pack(fill="x")

        # Entry
        self._entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            height=32,
            font=ctk.CTkFont(size=12),
        )
        self._entry.pack(fill="x", pady=(2, 0))

        # Error label
        self._error_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="red",
            anchor="w",
            height=16,
        )
        self._error_label.pack(fill="x")

        # Validar al perder foco
        self._entry.bind("<FocusOut>", lambda e: self.validate())

    def get(self) -> str:
        """Obtiene el valor actual del campo."""
        return self._entry.get().strip()

    def set(self, value: str) -> None:
        """Establece el valor del campo.

        Args:
            value: Valor a establecer.
        """
        self._entry.delete(0, "end")
        if value:
            self._entry.insert(0, value)

    def clear(self) -> None:
        """Limpia el campo y resetea el estado de validación."""
        self._entry.delete(0, "end")
        self._error_label.configure(text="")
        self._entry.configure(border_color=("gray50", "gray30"))
        self._is_valid = True

    def validate(self) -> bool:
        """Ejecuta la validación del campo.

        Returns:
            True si el campo es válido.
        """
        value = self.get()

        # Validar campo obligatorio
        if self._required and not value:
            self._show_error("Este campo es obligatorio")
            return False

        # Validar con función personalizada
        if self._validator and value:
            is_valid, error_msg = self._validator(value)
            if not is_valid:
                self._show_error(error_msg)
                return False

        # Campo válido
        self._clear_error()
        return True

    def _show_error(self, message: str) -> None:
        """Muestra un mensaje de error visual.

        Args:
            message: Mensaje de error.
        """
        self._error_label.configure(text=message)
        self._entry.configure(border_color="red")
        self._is_valid = False

    def _clear_error(self) -> None:
        """Limpia el error visual."""
        self._error_label.configure(text="")
        self._entry.configure(border_color=("gray50", "gray30"))
        self._is_valid = True

    @property
    def is_valid(self) -> bool:
        """Retorna si el campo es válido."""
        return self._is_valid

    def focus(self) -> None:
        """Establece el foco en el entry."""
        self._entry.focus_set()

    def configure_state(self, state: str) -> None:
        """Cambia el estado del entry (normal/disabled).

        Args:
            state: 'normal' o 'disabled'.
        """
        self._entry.configure(state=state)


class ValidatedComboBox(ctk.CTkFrame):
    """ComboBox con autocompletado y validación visual."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        label: str,
        values: list[str],
        required: bool = False,
        **kwargs,
    ) -> None:
        """Inicializa el combo validado.

        Args:
            master: Widget padre.
            label: Etiqueta del campo.
            values: Lista de valores disponibles.
            required: Si True, marca como obligatorio.
        """
        super().__init__(master, fg_color="transparent", **kwargs)

        self._required = required
        self._values = values
        self._is_valid = True

        label_text = f"{label} *" if required else label
        self._label = ctk.CTkLabel(
            self,
            text=label_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        )
        self._label.pack(fill="x")

        self._combo = ctk.CTkComboBox(
            self,
            values=values,
            height=32,
            font=ctk.CTkFont(size=12),
            state="normal",
        )
        self._combo.pack(fill="x", pady=(2, 0))
        self._combo.set("")

        self._error_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="red",
            anchor="w",
            height=16,
        )
        self._error_label.pack(fill="x")

    def get(self) -> str:
        """Obtiene el valor seleccionado."""
        return self._combo.get().strip()

    def set(self, value: str) -> None:
        """Establece el valor del combo.

        Args:
            value: Valor a establecer.
        """
        self._combo.set(value)

    def clear(self) -> None:
        """Limpia el combo."""
        self._combo.set("")
        self._error_label.configure(text="")
        self._is_valid = True

    def validate(self) -> bool:
        """Valida el campo.

        Returns:
            True si es válido.
        """
        value = self.get()
        if self._required and not value:
            self._error_label.configure(text="Este campo es obligatorio")
            self._is_valid = False
            return False
        self._error_label.configure(text="")
        self._is_valid = True
        return True

    @property
    def is_valid(self) -> bool:
        """Retorna si el campo es válido."""
        return self._is_valid


class DatePickerField(ctk.CTkFrame):
    """Campo selector de fecha con formato visual."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        label: str,
        required: bool = False,
        **kwargs,
    ) -> None:
        """Inicializa el selector de fecha.

        Args:
            master: Widget padre.
            label: Etiqueta del campo.
            required: Si True, marca como obligatorio.
        """
        super().__init__(master, fg_color="transparent", **kwargs)

        self._required = required
        self._is_valid = True

        label_text = f"{label} *" if required else label
        self._label = ctk.CTkLabel(
            self,
            text=label_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        )
        self._label.pack(fill="x")

        self._entry = ctk.CTkEntry(
            self,
            placeholder_text="AAAA-MM-DD",
            height=32,
            font=ctk.CTkFont(size=12),
        )
        self._entry.pack(fill="x", pady=(2, 0))

        self._error_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="red",
            anchor="w",
            height=16,
        )
        self._error_label.pack(fill="x")

        # Intentar usar DateEntry de tkcalendar como mejora
        self._try_calendar_widget()

    def _try_calendar_widget(self) -> None:
        """Intenta reemplazar el entry con DateEntry de tkcalendar."""
        try:
            from tkcalendar import DateEntry

            self._entry.destroy()
            self._date_entry = DateEntry(
                self,
                date_pattern="yyyy-mm-dd",
                font=("Segoe UI", 11),
                width=18,
                locale="es_AR",
            )
            self._date_entry.pack(fill="x", pady=(2, 0), before=self._error_label)
            self._date_entry.delete(0, "end")
            self._use_calendar = True
        except ImportError:
            self._use_calendar = False
            logger.debug("tkcalendar no disponible, usando entry de texto para fechas")

    def get(self) -> str:
        """Obtiene la fecha como string YYYY-MM-DD."""
        if hasattr(self, "_use_calendar") and self._use_calendar:
            val = self._date_entry.get()
            return val.strip() if val else ""
        return self._entry.get().strip()

    def set(self, value: str) -> None:
        """Establece la fecha.

        Args:
            value: Fecha en formato YYYY-MM-DD.
        """
        if hasattr(self, "_use_calendar") and self._use_calendar:
            self._date_entry.delete(0, "end")
            if value:
                self._date_entry.insert(0, value)
        else:
            self._entry.delete(0, "end")
            if value:
                self._entry.insert(0, value)

    def clear(self) -> None:
        """Limpia el campo."""
        if hasattr(self, "_use_calendar") and self._use_calendar:
            self._date_entry.delete(0, "end")
        else:
            self._entry.delete(0, "end")
        self._error_label.configure(text="")
        self._is_valid = True

    def validate(self) -> bool:
        """Valida la fecha.

        Returns:
            True si es válida.
        """
        value = self.get()
        if self._required and not value:
            self._error_label.configure(text="Este campo es obligatorio")
            self._is_valid = False
            return False
        if value:
            try:
                from datetime import datetime
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                self._error_label.configure(text="Formato inválido. Use AAAA-MM-DD")
                self._is_valid = False
                return False
        self._error_label.configure(text="")
        self._is_valid = True
        return True

    @property
    def is_valid(self) -> bool:
        """Retorna si el campo es válido."""
        return self._is_valid


class CheckboxWithEntry(ctk.CTkFrame):
    """Checkbox que habilita/deshabilita un campo de texto asociado."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        label: str,
        entry_label: str = "Detalles",
        entry_placeholder: str = "",
        **kwargs,
    ) -> None:
        """Inicializa el checkbox con entry condicional.

        Args:
            master: Widget padre.
            label: Texto del checkbox.
            entry_label: Etiqueta del campo de texto.
            entry_placeholder: Placeholder del campo.
        """
        super().__init__(master, fg_color="transparent", **kwargs)

        self._var = ctk.BooleanVar(value=False)

        self._checkbox = ctk.CTkCheckBox(
            self,
            text=label,
            variable=self._var,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_toggle,
        )
        self._checkbox.pack(fill="x", pady=(0, 2))

        self._entry = ctk.CTkEntry(
            self,
            placeholder_text=entry_placeholder,
            height=32,
            font=ctk.CTkFont(size=12),
            state="disabled",
        )
        self._entry.pack(fill="x", pady=(2, 0))

    def _on_toggle(self) -> None:
        """Habilita/deshabilita el entry según el checkbox."""
        if self._var.get():
            self._entry.configure(state="normal")
        else:
            self._entry.delete(0, "end")
            self._entry.configure(state="disabled")

    def get_checked(self) -> bool:
        """Retorna si el checkbox está marcado."""
        return self._var.get()

    def get_entry_value(self) -> str:
        """Retorna el valor del campo de texto."""
        return self._entry.get().strip()

    def set(self, checked: bool, value: str = "") -> None:
        """Establece el estado del checkbox y valor del entry.

        Args:
            checked: Estado del checkbox.
            value: Valor del entry.
        """
        self._var.set(checked)
        self._on_toggle()
        if checked and value:
            self._entry.delete(0, "end")
            self._entry.insert(0, value)

    def clear(self) -> None:
        """Resetea el checkbox y el entry."""
        self._var.set(False)
        self._entry.delete(0, "end")
        self._entry.configure(state="disabled")
