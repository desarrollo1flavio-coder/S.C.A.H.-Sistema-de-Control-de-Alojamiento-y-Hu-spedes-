"""Vista de gestión de establecimientos para S.C.A.H. v2."""

import customtkinter as ctk
from tkinter import messagebox

from models.establecimiento import EstablecimientoDAO
from models.habitacion import HabitacionDAO
from views.components.data_table import DataTable
from config.settings import TIPOS_HABITACION, ESTADOS_HABITACION
from utils.logger import get_logger

logger = get_logger("views.establecimientos")


class EstablecimientosView(ctk.CTkFrame):
    """ABM de establecimientos y habitaciones."""

    def __init__(self, parent, app_controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app_controller
        self._selected_estab_id = None
        self._build_ui()
        self._load_establecimientos()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="Establecimientos", font=("", 24, "bold")).pack(side="left")
        ctk.CTkButton(
            header, text="+ Nuevo Establecimiento",
            width=200, command=self._new_estab_dialog,
        ).pack(side="right")

        # Panel dividido: izquierda establecimientos, derecha habitaciones
        paned = ctk.CTkFrame(self, fg_color="transparent")
        paned.pack(fill="both", expand=True, padx=20, pady=5)
        paned.columnconfigure(0, weight=1)
        paned.columnconfigure(1, weight=1)
        paned.rowconfigure(0, weight=1)

        # Establecimientos (izquierda)
        left = ctk.CTkFrame(paned)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        ctk.CTkLabel(left, text="Establecimientos", font=("", 14, "bold")).pack(
            anchor="w", padx=15, pady=(10, 5),
        )

        estab_cols = [
            {"key": "id", "text": "ID", "width": 40},
            {"key": "nombre", "text": "NOMBRE", "width": 180},
            {"key": "direccion", "text": "DIRECCIÓN", "width": 150},
            {"key": "activo", "text": "ACTIVO", "width": 60},
        ]
        self._estab_table = DataTable(left, columns=estab_cols, on_select=self._on_estab_select)
        self._estab_table.pack(fill="both", expand=True, padx=10, pady=5)

        estab_btns = ctk.CTkFrame(left, fg_color="transparent")
        estab_btns.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(estab_btns, text="Editar", width=80, command=self._edit_estab).pack(side="left", padx=3)
        ctk.CTkButton(estab_btns, text="Desactivar", width=100, fg_color="red",
                       hover_color="darkred", command=self._toggle_estab).pack(side="left", padx=3)

        # Habitaciones (derecha)
        right = ctk.CTkFrame(paned)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        hab_header = ctk.CTkFrame(right, fg_color="transparent")
        hab_header.pack(fill="x", padx=15, pady=(10, 5))

        self._hab_title = ctk.CTkLabel(hab_header, text="Habitaciones", font=("", 14, "bold"))
        self._hab_title.pack(side="left")

        ctk.CTkButton(hab_header, text="+ Habitación", width=120, command=self._new_hab_dialog).pack(side="right")

        hab_cols = [
            {"key": "id", "text": "ID", "width": 40},
            {"key": "numero", "text": "N°", "width": 60},
            {"key": "tipo", "text": "TIPO", "width": 100},
            {"key": "capacidad", "text": "CAPAC.", "width": 60},
            {"key": "estado", "text": "ESTADO", "width": 100},
        ]
        self._hab_table = DataTable(right, columns=hab_cols)
        self._hab_table.pack(fill="both", expand=True, padx=10, pady=5)

        hab_btns = ctk.CTkFrame(right, fg_color="transparent")
        hab_btns.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(hab_btns, text="Editar", width=80, command=self._edit_hab).pack(side="left", padx=3)
        ctk.CTkButton(hab_btns, text="Eliminar", width=80, fg_color="red",
                       hover_color="darkred", command=self._delete_hab).pack(side="left", padx=3)

    def _load_establecimientos(self):
        try:
            data = EstablecimientoDAO.listar()
            for d in data:
                d["activo"] = "Sí" if d.get("activo") else "No"
            self._estab_table.load_data(data)
        except Exception as e:
            logger.error("Error cargando establecimientos: %s", e)

    def _load_habitaciones(self, establecimiento_id: int):
        try:
            data = HabitacionDAO.listar_por_establecimiento(establecimiento_id)
            self._hab_table.load_data(data)
        except Exception as e:
            logger.error("Error cargando habitaciones: %s", e)

    def _on_estab_select(self, row: dict):
        if row and row.get("id"):
            self._selected_estab_id = row["id"]
            self._hab_title.configure(text=f"Habitaciones de {row.get('nombre', '')}")
            self._load_habitaciones(row["id"])

    def _new_estab_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nuevo Establecimiento")
        dialog.geometry("400x300")
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Nombre:").pack(anchor="w", pady=(0, 2))
        e_nombre = ctk.CTkEntry(frame, width=300)
        e_nombre.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Dirección:").pack(anchor="w", pady=(0, 2))
        e_dir = ctk.CTkEntry(frame, width=300)
        e_dir.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Teléfono:").pack(anchor="w", pady=(0, 2))
        e_tel = ctk.CTkEntry(frame, width=300)
        e_tel.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Email:").pack(anchor="w", pady=(0, 2))
        e_email = ctk.CTkEntry(frame, width=300)
        e_email.pack(pady=(0, 8))

        def create():
            if not e_nombre.get():
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            try:
                EstablecimientoDAO.crear(
                    nombre=e_nombre.get(),
                    direccion=e_dir.get() or None,
                    telefono=e_tel.get() or None,
                    email=e_email.get() or None,
                )
                dialog.destroy()
                self._load_establecimientos()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        ctk.CTkButton(frame, text="Crear", command=create).pack(pady=10)

    def _edit_estab(self):
        selected = self._estab_table.get_selected()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione un establecimiento")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Establecimiento")
        dialog.geometry("400x300")
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Nombre:").pack(anchor="w", pady=(0, 2))
        e_nombre = ctk.CTkEntry(frame, width=300)
        e_nombre.insert(0, selected.get("nombre", ""))
        e_nombre.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Dirección:").pack(anchor="w", pady=(0, 2))
        e_dir = ctk.CTkEntry(frame, width=300)
        e_dir.insert(0, selected.get("direccion", "") or "")
        e_dir.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Teléfono:").pack(anchor="w", pady=(0, 2))
        e_tel = ctk.CTkEntry(frame, width=300)
        e_tel.insert(0, selected.get("telefono", "") or "")
        e_tel.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Email:").pack(anchor="w", pady=(0, 2))
        e_email = ctk.CTkEntry(frame, width=300)
        e_email.insert(0, selected.get("email", "") or "")
        e_email.pack(pady=(0, 8))

        def save():
            try:
                EstablecimientoDAO.actualizar(
                    selected["id"],
                    nombre=e_nombre.get(),
                    direccion=e_dir.get() or None,
                    telefono=e_tel.get() or None,
                    email=e_email.get() or None,
                )
                dialog.destroy()
                self._load_establecimientos()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        ctk.CTkButton(frame, text="Guardar", command=save).pack(pady=10)

    def _toggle_estab(self):
        selected = self._estab_table.get_selected()
        if not selected:
            return
        current = selected.get("activo") == "Sí"
        action = "desactivar" if current else "activar"
        if messagebox.askyesno("Confirmar", f"¿Desea {action} '{selected['nombre']}'?"):
            try:
                EstablecimientoDAO.set_activo(selected["id"], not current)
                self._load_establecimientos()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _new_hab_dialog(self):
        if not self._selected_estab_id:
            messagebox.showwarning("Aviso", "Seleccione un establecimiento primero")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Nueva Habitación")
        dialog.geometry("350x280")
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Número/Nombre:").pack(anchor="w", pady=(0, 2))
        e_num = ctk.CTkEntry(frame, width=250)
        e_num.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Tipo:").pack(anchor="w", pady=(0, 2))
        cb_tipo = ctk.CTkComboBox(frame, values=TIPOS_HABITACION, width=250)
        cb_tipo.set(TIPOS_HABITACION[0] if TIPOS_HABITACION else "simple")
        cb_tipo.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Capacidad:").pack(anchor="w", pady=(0, 2))
        e_cap = ctk.CTkEntry(frame, width=250)
        e_cap.insert(0, "2")
        e_cap.pack(pady=(0, 8))

        def create():
            if not e_num.get():
                messagebox.showerror("Error", "El número es obligatorio")
                return
            try:
                cap = int(e_cap.get()) if e_cap.get() else 2
                HabitacionDAO.crear(
                    establecimiento_id=self._selected_estab_id,
                    numero=e_num.get(),
                    tipo=cb_tipo.get(),
                    capacidad=cap,
                )
                dialog.destroy()
                self._load_habitaciones(self._selected_estab_id)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        ctk.CTkButton(frame, text="Crear", command=create).pack(pady=10)

    def _edit_hab(self):
        selected = self._hab_table.get_selected()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione una habitación")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Habitación")
        dialog.geometry("350x300")
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Número/Nombre:").pack(anchor="w", pady=(0, 2))
        e_num = ctk.CTkEntry(frame, width=250)
        e_num.insert(0, selected.get("numero", ""))
        e_num.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Tipo:").pack(anchor="w", pady=(0, 2))
        cb_tipo = ctk.CTkComboBox(frame, values=TIPOS_HABITACION, width=250)
        cb_tipo.set(selected.get("tipo", "simple"))
        cb_tipo.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Capacidad:").pack(anchor="w", pady=(0, 2))
        e_cap = ctk.CTkEntry(frame, width=250)
        e_cap.insert(0, str(selected.get("capacidad", 2)))
        e_cap.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Estado:").pack(anchor="w", pady=(0, 2))
        cb_estado = ctk.CTkComboBox(frame, values=ESTADOS_HABITACION, width=250)
        cb_estado.set(selected.get("estado", "disponible"))
        cb_estado.pack(pady=(0, 8))

        def save():
            try:
                cap = int(e_cap.get()) if e_cap.get() else 2
                HabitacionDAO.actualizar(
                    selected["id"],
                    numero=e_num.get(),
                    tipo=cb_tipo.get(),
                    capacidad=cap,
                    estado=cb_estado.get(),
                )
                dialog.destroy()
                self._load_habitaciones(self._selected_estab_id)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        ctk.CTkButton(frame, text="Guardar", command=save).pack(pady=10)

    def _delete_hab(self):
        selected = self._hab_table.get_selected()
        if not selected:
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar habitación {selected.get('numero')}?"):
            try:
                HabitacionDAO.eliminar(selected["id"])
                self._load_habitaciones(self._selected_estab_id)
            except Exception as e:
                messagebox.showerror("Error", str(e))
