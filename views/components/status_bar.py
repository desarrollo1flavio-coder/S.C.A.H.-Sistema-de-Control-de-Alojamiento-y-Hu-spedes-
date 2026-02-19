"""Barra de estado inferior para S.C.A.H. v2."""

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
