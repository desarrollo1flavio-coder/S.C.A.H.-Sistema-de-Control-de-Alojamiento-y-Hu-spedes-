"""Vista del dashboard principal para S.C.A.H. v2."""

import customtkinter as ctk
from typing import Optional

from models.estadia import EstadiaDAO
from models.persona import PersonaDAO
from config.settings import APP_VERSION
from utils.logger import get_logger

logger = get_logger("views.dashboard")


class DashboardView(ctk.CTkFrame):
    """Panel principal con estadísticas y accesos rápidos."""

    def __init__(self, parent, app_controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app_controller
        self._build_ui()

    def _build_ui(self):
        # Título
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="Dashboard",
            font=("", 24, "bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"v{APP_VERSION}",
            font=("", 12),
            text_color="gray",
        ).pack(side="right")

        # Tarjetas de estadísticas
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=10)
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self._card_total_personas = self._create_card(cards_frame, "Total Personas", "0", 0)
        self._card_total_estadias = self._create_card(cards_frame, "Total Estadías", "0", 1)
        self._card_hospedados_hoy = self._create_card(cards_frame, "Hospedados Hoy", "0", 2)
        self._card_importaciones = self._create_card(cards_frame, "Importaciones", "0", 3)

        # Acciones rápidas
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(actions_frame, text="Acciones Rápidas", font=("", 16, "bold")).pack(
            anchor="w", pady=(5, 10),
        )

        btns_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btns_frame.pack(fill="x")

        self._btn_import = ctk.CTkButton(
            btns_frame, text="Importar Excel",
            font=("", 14), height=45, width=180,
            command=lambda: self._navigate("import"),
        )
        self._btn_import.pack(side="left", padx=5)

        self._btn_manual = ctk.CTkButton(
            btns_frame, text="Carga Manual",
            font=("", 14), height=45, width=180,
            command=lambda: self._navigate("manual"),
        )
        self._btn_manual.pack(side="left", padx=5)

        self._btn_search = ctk.CTkButton(
            btns_frame, text="Buscar",
            font=("", 14), height=45, width=180,
            command=lambda: self._navigate("search"),
        )
        self._btn_search.pack(side="left", padx=5)

        self._btn_backup = ctk.CTkButton(
            btns_frame, text="Crear Backup",
            font=("", 14), height=45, width=180,
            fg_color="gray40",
            command=self._do_backup,
        )
        self._btn_backup.pack(side="left", padx=5)

        # Top nacionalidades
        stats_container = ctk.CTkFrame(self, fg_color="transparent")
        stats_container.pack(fill="both", expand=True, padx=20, pady=10)
        stats_container.columnconfigure((0, 1), weight=1)

        nac_frame = ctk.CTkFrame(stats_container)
        nac_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        ctk.CTkLabel(nac_frame, text="Top Nacionalidades", font=("", 14, "bold")).pack(
            anchor="w", padx=10, pady=10,
        )
        self._nac_list = ctk.CTkTextbox(nac_frame, height=200, state="disabled")
        self._nac_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        est_frame = ctk.CTkFrame(stats_container)
        est_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        ctk.CTkLabel(est_frame, text="Top Establecimientos", font=("", 14, "bold")).pack(
            anchor="w", padx=10, pady=10,
        )
        self._est_list = ctk.CTkTextbox(est_frame, height=200, state="disabled")
        self._est_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _create_card(self, parent, title: str, value: str, col: int) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)

        ctk.CTkLabel(card, text=title, font=("", 12), text_color="gray").pack(
            padx=15, pady=(10, 0),
        )
        val_label = ctk.CTkLabel(card, text=value, font=("", 28, "bold"))
        val_label.pack(padx=15, pady=(0, 10))
        return val_label

    def refresh_stats(self):
        """Actualiza las estadísticas del dashboard."""
        try:
            total_personas = PersonaDAO.contar_total()
            total_estadias = EstadiaDAO.contar_total()
            hospedados = EstadiaDAO.contar_activas_hoy()

            self._card_total_personas.configure(text=str(total_personas))
            self._card_total_estadias.configure(text=str(total_estadias))
            self._card_hospedados_hoy.configure(text=str(hospedados))

            # Top nacionalidades
            nacs = EstadiaDAO.estadisticas_nacionalidades(8)
            self._nac_list.configure(state="normal")
            self._nac_list.delete("1.0", "end")
            for nac in nacs:
                self._nac_list.insert(
                    "end", f"  {nac['nacionalidad']}: {nac['cantidad']}\n",
                )
            self._nac_list.configure(state="disabled")

            # Top establecimientos
            ests = EstadiaDAO.estadisticas_establecimientos(8)
            self._est_list.configure(state="normal")
            self._est_list.delete("1.0", "end")
            for est in ests:
                self._est_list.insert(
                    "end", f"  {est['establecimiento']}: {est['cantidad']}\n",
                )
            self._est_list.configure(state="disabled")

        except Exception as e:
            logger.error("Error al refrescar stats: %s", e)

    def _navigate(self, view_name: str):
        if self._app and hasattr(self._app, "show_view"):
            self._app.show_view(view_name)

    def _do_backup(self):
        try:
            from config.database import create_backup
            path = create_backup()
            if self._app and hasattr(self._app, "status_bar"):
                self._app.status_bar.set_success(f"Backup creado: {path.name}")
        except Exception as e:
            logger.error("Error al crear backup: %s", e)
            if self._app and hasattr(self._app, "status_bar"):
                self._app.status_bar.set_error(f"Error al crear backup: {e}")
