"""Script de reconstrucción S.C.A.H. v2 - Fase 3d.

Views: User Management + Establishment Management
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = {}

# ============================================================
# views/usuarios_view.py
# ============================================================
FILES["views/usuarios_view.py"] = '''"""Vista de gestión de usuarios para S.C.A.H. v2."""

import customtkinter as ctk
from tkinter import messagebox

from controllers.auth_controller import AuthController
from models.usuario import UsuarioDAO
from views.components.data_table import DataTable
from config.settings import ROLES_USUARIO
from utils.logger import get_logger

logger = get_logger("views.usuarios")


class UsuariosView(ctk.CTkFrame):
    """ABM de usuarios del sistema."""

    def __init__(self, parent, app_controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app_controller
        self._build_ui()
        self._load_users()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="Gestión de Usuarios", font=("", 24, "bold")).pack(side="left")
        ctk.CTkButton(
            header, text="+ Nuevo Usuario", width=160,
            command=self._new_user_dialog,
        ).pack(side="right")

        # Tabla
        cols = [
            {"key": "id", "text": "ID", "width": 50},
            {"key": "username", "text": "USUARIO", "width": 150},
            {"key": "nombre_completo", "text": "NOMBRE COMPLETO", "width": 200},
            {"key": "rol", "text": "ROL", "width": 100},
            {"key": "activo", "text": "ACTIVO", "width": 80},
            {"key": "created_at", "text": "CREADO", "width": 150},
        ]
        self._table = DataTable(self, columns=cols, on_double_click=self._on_row_click)
        self._table.pack(fill="both", expand=True, padx=20, pady=5)

        # Botones de acción
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 10))

        ctk.CTkButton(
            btn_frame, text="Editar Seleccionado", width=160,
            command=self._edit_selected,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Desactivar", width=120,
            fg_color="red", hover_color="darkred",
            command=self._toggle_active,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Cambiar Contraseña", width=160,
            fg_color="gray40",
            command=self._change_password_dialog,
        ).pack(side="left", padx=5)

    def _load_users(self):
        try:
            users = UsuarioDAO.listar_todos()
            for u in users:
                u["activo"] = "Sí" if u.get("activo") else "No"
            self._table.load_data(users)
        except Exception as e:
            logger.error("Error listando usuarios: %s", e)

    def _new_user_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nuevo Usuario")
        dialog.geometry("400x380")
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Nombre de usuario:").pack(anchor="w", pady=(0, 2))
        e_user = ctk.CTkEntry(frame, width=300)
        e_user.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Nombre completo:").pack(anchor="w", pady=(0, 2))
        e_nombre = ctk.CTkEntry(frame, width=300)
        e_nombre.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Contraseña:").pack(anchor="w", pady=(0, 2))
        e_pass = ctk.CTkEntry(frame, width=300, show="*")
        e_pass.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Confirmar contraseña:").pack(anchor="w", pady=(0, 2))
        e_pass2 = ctk.CTkEntry(frame, width=300, show="*")
        e_pass2.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Rol:").pack(anchor="w", pady=(0, 2))
        cb_rol = ctk.CTkComboBox(frame, values=ROLES_USUARIO, width=300)
        cb_rol.set("operador")
        cb_rol.pack(pady=(0, 10))

        def create():
            if not e_user.get() or not e_pass.get():
                messagebox.showerror("Error", "Usuario y contraseña son obligatorios")
                return
            if e_pass.get() != e_pass2.get():
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            try:
                auth = AuthController()
                auth.registrar_usuario(
                    username=e_user.get(),
                    password=e_pass.get(),
                    nombre_completo=e_nombre.get() or e_user.get(),
                    rol=cb_rol.get(),
                )
                messagebox.showinfo("Éxito", f"Usuario '{e_user.get()}' creado")
                dialog.destroy()
                self._load_users()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        ctk.CTkButton(frame, text="Crear Usuario", command=create).pack(pady=10)

    def _edit_selected(self):
        selected = self._table.get_selected()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione un usuario")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Usuario")
        dialog.geometry("400x250")
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=f"Editando: {selected['username']}", font=("", 14, "bold")).pack(pady=(0, 10))

        ctk.CTkLabel(frame, text="Nombre completo:").pack(anchor="w", pady=(0, 2))
        e_nombre = ctk.CTkEntry(frame, width=300)
        e_nombre.insert(0, selected.get("nombre_completo", ""))
        e_nombre.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Rol:").pack(anchor="w", pady=(0, 2))
        cb_rol = ctk.CTkComboBox(frame, values=ROLES_USUARIO, width=300)
        cb_rol.set(selected.get("rol", "operador"))
        cb_rol.pack(pady=(0, 10))

        def save():
            try:
                UsuarioDAO.actualizar(
                    selected["id"],
                    nombre_completo=e_nombre.get(),
                    rol=cb_rol.get(),
                )
                messagebox.showinfo("Éxito", "Usuario actualizado")
                dialog.destroy()
                self._load_users()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        ctk.CTkButton(frame, text="Guardar", command=save).pack(pady=5)

    def _toggle_active(self):
        selected = self._table.get_selected()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione un usuario")
            return

        current = selected.get("activo") == "Sí"
        action = "desactivar" if current else "activar"
        if not messagebox.askyesno("Confirmar", f"¿Desea {action} al usuario {selected['username']}?"):
            return
        try:
            UsuarioDAO.set_activo(selected["id"], not current)
            self._load_users()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _change_password_dialog(self):
        selected = self._table.get_selected()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione un usuario")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Cambiar Contraseña")
        dialog.geometry("350x220")
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=f"Usuario: {selected['username']}", font=("", 14, "bold")).pack(pady=(0, 10))

        ctk.CTkLabel(frame, text="Nueva contraseña:").pack(anchor="w", pady=(0, 2))
        e_pass = ctk.CTkEntry(frame, show="*", width=260)
        e_pass.pack(pady=(0, 8))

        ctk.CTkLabel(frame, text="Confirmar:").pack(anchor="w", pady=(0, 2))
        e_pass2 = ctk.CTkEntry(frame, show="*", width=260)
        e_pass2.pack(pady=(0, 8))

        def change():
            if e_pass.get() != e_pass2.get():
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            if len(e_pass.get()) < 4:
                messagebox.showerror("Error", "Mínimo 4 caracteres")
                return
            try:
                auth = AuthController()
                auth.cambiar_password(selected["username"], e_pass.get())
                messagebox.showinfo("Éxito", "Contraseña actualizada")
                dialog.destroy()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        ctk.CTkButton(frame, text="Cambiar", command=change).pack(pady=5)

    def _on_row_click(self, row: dict):
        self._edit_selected()
'''

# ============================================================
# views/establecimientos_view.py
# ============================================================
FILES["views/establecimientos_view.py"] = '''"""Vista de gestión de establecimientos para S.C.A.H. v2."""

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
    print("S.C.A.H. v2 - Fase 3d: User Mgmt + Establishments")
    print("=" * 60)
    write_all()
    print("\nFase 3d completada.")
