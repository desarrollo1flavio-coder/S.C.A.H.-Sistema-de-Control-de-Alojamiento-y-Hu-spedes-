"""Campos de formulario reutilizables para S.C.A.H. v2."""

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
