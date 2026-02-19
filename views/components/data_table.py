"""Tabla de datos scrollable para S.C.A.H. v2."""

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
