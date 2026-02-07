"""Tabla de datos reutilizable para S.C.A.H.

Wrapper de ttk.Treeview con soporte para ordenamiento por columna,
paginación, selección y scroll.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

import customtkinter as ctk

from config.settings import PAGINATION_SIZE
from utils.logger import get_logger

logger = get_logger("components.data_table")


class DataTable(ctk.CTkFrame):
    """Tabla de datos con ordenamiento, paginación y selección."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        columns: list[dict],
        on_select: Optional[Callable[[dict], None]] = None,
        on_double_click: Optional[Callable[[dict], None]] = None,
        page_size: int = PAGINATION_SIZE,
        show_pagination: bool = True,
        **kwargs,
    ) -> None:
        """Inicializa la tabla de datos.

        Args:
            master: Widget padre.
            columns: Lista de dicts con keys 'key', 'label', 'width', 'anchor'.
                     Ejemplo: [{'key': 'nombre', 'label': 'Nombre', 'width': 150}]
            on_select: Callback al seleccionar una fila.
            on_double_click: Callback al hacer doble click en una fila.
            page_size: Registros por página.
            show_pagination: Si True, muestra controles de paginación.
        """
        super().__init__(master, **kwargs)

        self._columns = columns
        self._on_select = on_select
        self._on_double_click = on_double_click
        self._page_size = page_size
        self._current_page = 1
        self._total_records = 0
        self._all_data: list[dict] = []
        self._sort_column: str = ""
        self._sort_reverse: bool = False

        self._build_table()
        if show_pagination:
            self._build_pagination()

    def _build_table(self) -> None:
        """Construye el Treeview con columnas y scrollbars."""
        # Frame para tabla + scrollbars
        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        col_keys = [col["key"] for col in self._columns]

        # Estilo del Treeview
        style = ttk.Style()
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self._tree = ttk.Treeview(
            table_frame,
            columns=col_keys,
            show="headings",
            selectmode="browse",
        )

        # Configurar columnas
        for col in self._columns:
            self._tree.heading(
                col["key"],
                text=col["label"],
                command=lambda c=col["key"]: self._sort_by_column(c),
            )
            self._tree.column(
                col["key"],
                width=col.get("width", 120),
                anchor=col.get("anchor", "w"),
                minwidth=50,
            )

        # Scrollbars
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Eventos
        self._tree.bind("<<TreeviewSelect>>", self._on_row_select)
        self._tree.bind("<Double-1>", self._on_row_double_click)

        # Colores alternos
        self._tree.tag_configure("odd", background="#f0f0f0")
        self._tree.tag_configure("even", background="#ffffff")

    def _build_pagination(self) -> None:
        """Construye los controles de paginación."""
        self._pagination_frame = ctk.CTkFrame(self, fg_color="transparent", height=35)
        self._pagination_frame.pack(fill="x", padx=10, pady=(0, 5))

        self._prev_btn = ctk.CTkButton(
            self._pagination_frame,
            text="◀ Anterior",
            width=100,
            height=28,
            font=ctk.CTkFont(size=11),
            command=self._prev_page,
        )
        self._prev_btn.pack(side="left")

        self._page_label = ctk.CTkLabel(
            self._pagination_frame,
            text="Página 1 de 1  |  0 registros",
            font=ctk.CTkFont(size=11),
        )
        self._page_label.pack(side="left", expand=True)

        self._next_btn = ctk.CTkButton(
            self._pagination_frame,
            text="Siguiente ▶",
            width=100,
            height=28,
            font=ctk.CTkFont(size=11),
            command=self._next_page,
        )
        self._next_btn.pack(side="right")

    def load_data(self, data: list[dict], total: int | None = None) -> None:
        """Carga datos en la tabla.

        Args:
            data: Lista de diccionarios con los datos.
            total: Total de registros (para paginación externa).
        """
        self._all_data = data
        self._total_records = total if total is not None else len(data)
        self._current_page = 1
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresca la tabla mostrando la página actual."""
        # Limpiar tabla
        for item in self._tree.get_children():
            self._tree.delete(item)

        # Calcular rango de datos para la página
        start = (self._current_page - 1) * self._page_size
        end = start + self._page_size
        page_data = self._all_data[start:end]

        # Insertar filas
        col_keys = [col["key"] for col in self._columns]
        for i, row_data in enumerate(page_data):
            values = [row_data.get(key, "") for key in col_keys]
            tag = "odd" if i % 2 else "even"
            self._tree.insert("", "end", values=values, tags=(tag,))

        # Actualizar paginación
        self._update_pagination()

    def _update_pagination(self) -> None:
        """Actualiza los controles de paginación."""
        if not hasattr(self, "_pagination_frame"):
            return

        total_pages = max(1, (self._total_records + self._page_size - 1) // self._page_size)
        self._page_label.configure(
            text=f"Página {self._current_page} de {total_pages}  |  "
            f"{self._total_records} registros"
        )
        self._prev_btn.configure(state="normal" if self._current_page > 1 else "disabled")
        self._next_btn.configure(state="normal" if self._current_page < total_pages else "disabled")

    def _prev_page(self) -> None:
        """Navega a la página anterior."""
        if self._current_page > 1:
            self._current_page -= 1
            self._refresh_display()

    def _next_page(self) -> None:
        """Navega a la página siguiente."""
        total_pages = max(1, (self._total_records + self._page_size - 1) // self._page_size)
        if self._current_page < total_pages:
            self._current_page += 1
            self._refresh_display()

    def _sort_by_column(self, col_key: str) -> None:
        """Ordena la tabla por una columna.

        Args:
            col_key: Key de la columna por la que ordenar.
        """
        if self._sort_column == col_key:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = col_key
            self._sort_reverse = False

        self._all_data.sort(
            key=lambda x: str(x.get(col_key, "")).lower(),
            reverse=self._sort_reverse,
        )
        self._current_page = 1
        self._refresh_display()

    def _on_row_select(self, event: tk.Event) -> None:
        """Maneja la selección de una fila."""
        if self._on_select:
            selected = self.get_selected()
            if selected:
                self._on_select(selected)

    def _on_row_double_click(self, event: tk.Event) -> None:
        """Maneja el doble click en una fila."""
        if self._on_double_click:
            selected = self.get_selected()
            if selected:
                self._on_double_click(selected)

    def get_selected(self) -> Optional[dict]:
        """Obtiene los datos de la fila seleccionada.

        Returns:
            Diccionario con los datos de la fila o None.
        """
        selection = self._tree.selection()
        if not selection:
            return None

        item = self._tree.item(selection[0])
        values = item["values"]
        col_keys = [col["key"] for col in self._columns]
        return dict(zip(col_keys, values))

    def clear(self) -> None:
        """Limpia todos los datos de la tabla."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._all_data = []
        self._total_records = 0
        self._current_page = 1
        if hasattr(self, "_pagination_frame"):
            self._update_pagination()
