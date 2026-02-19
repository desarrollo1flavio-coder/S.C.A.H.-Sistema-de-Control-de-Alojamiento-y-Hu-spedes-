"""Vista de carga manual de huéspedes para S.C.A.H. v2."""

import customtkinter as ctk
from datetime import date, datetime
from tkinter import messagebox

from controllers.persona_controller import PersonaController
from controllers.estadia_controller import EstadiaController
from views.components.form_fields import LabeledEntry, LabeledComboBox
from config.settings import NACIONALIDADES
from utils.logger import get_logger

logger = get_logger("views.manual")


class ManualView(ctk.CTkFrame):
    """Formulario de carga manual de persona + estadía."""

    def __init__(self, parent, app_controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app_controller
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="Carga Manual de Huésped", font=("", 24, "bold")).pack(side="left")

        # Scrollable form
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        # Sección: Datos Personales
        ctk.CTkLabel(scroll, text="Datos Personales", font=("", 16, "bold")).pack(
            anchor="w", pady=(10, 5),
        )

        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        row1.columnconfigure((0, 1, 2, 3), weight=1)

        self._f_apellido = LabeledEntry(row1, "Apellido", required=True)
        self._f_apellido.grid(row=0, column=0, sticky="ew", padx=5)

        self._f_nombre = LabeledEntry(row1, "Nombre", required=True)
        self._f_nombre.grid(row=0, column=1, sticky="ew", padx=5)

        self._f_dni = LabeledEntry(row1, "D.N.I.", placeholder="Sin puntos")
        self._f_dni.grid(row=0, column=2, sticky="ew", padx=5)

        self._f_pasaporte = LabeledEntry(row1, "Pasaporte")
        self._f_pasaporte.grid(row=0, column=3, sticky="ew", padx=5)

        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        row2.columnconfigure((0, 1, 2, 3), weight=1)

        self._f_nacionalidad = LabeledComboBox(row2, "Nacionalidad", NACIONALIDADES, "Argentina")
        self._f_nacionalidad.grid(row=0, column=0, sticky="ew", padx=5)

        self._f_procedencia = LabeledEntry(row2, "Procedencia")
        self._f_procedencia.grid(row=0, column=1, sticky="ew", padx=5)

        self._f_fecha_nac = LabeledEntry(row2, "Fecha Nacimiento", placeholder="DD/MM/AAAA")
        self._f_fecha_nac.grid(row=0, column=2, sticky="ew", padx=5)

        self._f_edad = LabeledEntry(row2, "Edad")
        self._f_edad.grid(row=0, column=3, sticky="ew", padx=5)

        row3 = ctk.CTkFrame(scroll, fg_color="transparent")
        row3.pack(fill="x", pady=2)
        row3.columnconfigure((0, 1), weight=1)

        self._f_profesion = LabeledEntry(row3, "Profesión")
        self._f_profesion.grid(row=0, column=0, sticky="ew", padx=5)

        self._f_telefono = LabeledEntry(row3, "Teléfono")
        self._f_telefono.grid(row=0, column=1, sticky="ew", padx=5)

        # Sección: Datos de Estadía
        ctk.CTkLabel(scroll, text="Datos de Estadía", font=("", 16, "bold")).pack(
            anchor="w", pady=(20, 5),
        )

        row4 = ctk.CTkFrame(scroll, fg_color="transparent")
        row4.pack(fill="x", pady=2)
        row4.columnconfigure((0, 1, 2, 3), weight=1)

        self._f_establecimiento = LabeledEntry(row4, "Hotel / Establecimiento", required=True)
        self._f_establecimiento.grid(row=0, column=0, sticky="ew", padx=5)

        self._f_habitacion = LabeledEntry(row4, "Habitación")
        self._f_habitacion.grid(row=0, column=1, sticky="ew", padx=5)

        self._f_entrada = LabeledEntry(row4, "Fecha Entrada", required=True, placeholder="DD/MM/AAAA")
        self._f_entrada.grid(row=0, column=2, sticky="ew", padx=5)

        self._f_salida = LabeledEntry(row4, "Fecha Salida", placeholder="DD/MM/AAAA")
        self._f_salida.grid(row=0, column=3, sticky="ew", padx=5)

        row5 = ctk.CTkFrame(scroll, fg_color="transparent")
        row5.pack(fill="x", pady=2)
        row5.columnconfigure((0, 1), weight=1)

        self._f_destino = LabeledEntry(row5, "Destino")
        self._f_destino.grid(row=0, column=0, sticky="ew", padx=5)

        self._f_vehiculo = LabeledEntry(row5, "Datos Vehículo (opcional)")
        self._f_vehiculo.grid(row=0, column=1, sticky="ew", padx=5)

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(
            btn_frame, text="Guardar Huésped",
            font=("", 14, "bold"), height=40, width=200,
            command=self._save,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame, text="Limpiar Formulario",
            font=("", 14), height=40, width=160,
            fg_color="gray40",
            command=self._clear_form,
        ).pack(side="right", padx=10)

    def _parse_fecha(self, texto: str) -> str | None:
        """Convierte DD/MM/AAAA a AAAA-MM-DD."""
        if not texto.strip():
            return None
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def _save(self):
        usuario = "sistema"
        if self._app and hasattr(self._app, "auth_controller"):
            usuario = self._app.auth_controller.current_user

        # Validar campos requeridos
        apellido = self._f_apellido.get()
        nombre = self._f_nombre.get()
        if not apellido or not nombre:
            messagebox.showerror("Error", "Apellido y Nombre son obligatorios")
            return

        dni = self._f_dni.get() or None
        pasaporte = self._f_pasaporte.get() or None
        if not dni and not pasaporte:
            messagebox.showerror("Error", "Debe ingresar al menos DNI o Pasaporte")
            return

        fecha_entrada = self._parse_fecha(self._f_entrada.get())
        if not fecha_entrada:
            messagebox.showerror("Error", "La fecha de entrada es obligatoria (DD/MM/AAAA)")
            return

        fecha_salida = self._parse_fecha(self._f_salida.get())
        fecha_nac = self._parse_fecha(self._f_fecha_nac.get())

        edad = None
        if self._f_edad.get():
            try:
                edad = int(float(self._f_edad.get()))
            except ValueError:
                pass

        vehiculo_datos = self._f_vehiculo.get() or None

        try:
            persona_ctrl = PersonaController(usuario)
            estadia_ctrl = EstadiaController(usuario)

            # Crear o encontrar persona
            datos_persona = {
                "nacionalidad": self._f_nacionalidad.get() or "Argentina",
                "procedencia": self._f_procedencia.get() or "S/D",
                "apellido": apellido,
                "nombre": nombre,
                "dni": dni,
                "pasaporte": pasaporte,
                "fecha_nacimiento": fecha_nac,
                "profesion": self._f_profesion.get() or None,
                "telefono": self._f_telefono.get() or None,
            }
            persona_id = persona_ctrl.obtener_o_crear(datos_persona)

            # Crear estadía
            datos_estadia = {
                "persona_id": persona_id,
                "establecimiento": self._f_establecimiento.get() or None,
                "habitacion": self._f_habitacion.get() or "S/N",
                "edad": edad,
                "fecha_entrada": fecha_entrada,
                "fecha_salida": fecha_salida,
                "destino": self._f_destino.get() or None,
                "vehiculo_tiene": bool(vehiculo_datos),
                "vehiculo_datos": vehiculo_datos,
                "usuario_carga": usuario,
            }
            estadia_ctrl.crear(datos_estadia)

            messagebox.showinfo("Éxito", f"Huésped {apellido}, {nombre} registrado correctamente")
            self._clear_form()

            if self._app and hasattr(self._app, "status_bar"):
                self._app.status_bar.set_success(f"Huésped registrado: {apellido}, {nombre}")
            if self._app and hasattr(self._app, "refresh_dashboard"):
                self._app.refresh_dashboard()

        except Exception as e:
            logger.error("Error al guardar huésped: %s", e)
            messagebox.showerror("Error", str(e))

    def _clear_form(self):
        for field in [
            self._f_apellido, self._f_nombre, self._f_dni, self._f_pasaporte,
            self._f_procedencia, self._f_fecha_nac, self._f_edad,
            self._f_profesion, self._f_telefono, self._f_establecimiento,
            self._f_habitacion, self._f_entrada, self._f_salida,
            self._f_destino, self._f_vehiculo,
        ]:
            field.clear()
        self._f_nacionalidad.set("Argentina")
