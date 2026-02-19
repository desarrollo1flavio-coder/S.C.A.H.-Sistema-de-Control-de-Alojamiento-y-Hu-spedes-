"""Controlador de reportes para S.C.A.H. v2."""

from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from models.estadia import EstadiaDAO
from config.settings import APP_ORGANIZATION, APP_SUBTITLE
from utils.logger import get_logger

logger = get_logger("report_controller")


class ReportController:
    """Genera exportaciones en Excel y PDF."""

    def __init__(self, usuario: str = "sistema"):
        self.usuario = usuario

    def exportar_excel(
        self,
        filepath: str,
        filtros: dict | None = None,
        termino: str = "",
    ) -> str:
        """Exporta resultados de búsqueda a Excel."""
        registros, total = EstadiaDAO.buscar_completa(
            termino=termino,
            filtros=filtros,
            pagina=1,
            por_pagina=10000,
        )
        if not registros:
            raise ValueError("No hay datos para exportar")

        df = pd.DataFrame(registros)

        # Renombrar columnas para legibilidad
        columnas_rename = {
            "establecimiento": "HOTEL",
            "nacionalidad": "NACIONALIDAD",
            "procedencia": "PROCEDENCIA",
            "apellido": "APELLIDO",
            "nombre": "NOMBRE",
            "dni": "D.N.I.",
            "pasaporte": "PASAPORTE",
            "fecha_nacimiento": "FECHA NAC.",
            "edad": "EDAD",
            "profesion": "PROFESIÓN",
            "fecha_entrada": "ENTRADA",
            "fecha_salida": "SALIDA",
            "habitacion": "HABITACIÓN",
        }
        cols_presentes = {k: v for k, v in columnas_rename.items() if k in df.columns}
        df = df[list(cols_presentes.keys())].rename(columns=cols_presentes)

        df.to_excel(filepath, index=False, engine="openpyxl")
        logger.info("Exportación Excel: %s (%d registros)", filepath, len(df))
        return filepath

    def exportar_pdf(
        self,
        filepath: str,
        filtros: dict | None = None,
        termino: str = "",
    ) -> str:
        """Exporta resultados a PDF con formato institucional."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except ImportError:
            raise ImportError("ReportLab no está instalado. Ejecute: pip install reportlab")

        registros, total = EstadiaDAO.buscar_completa(
            termino=termino,
            filtros=filtros,
            pagina=1,
            por_pagina=10000,
        )
        if not registros:
            raise ValueError("No hay datos para exportar")

        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(A4),
            rightMargin=10*mm, leftMargin=10*mm,
            topMargin=15*mm, bottomMargin=15*mm,
        )
        styles = getSampleStyleSheet()
        elements = []

        # Header institucional
        elements.append(Paragraph(APP_ORGANIZATION, styles["Title"]))
        elements.append(Paragraph(APP_SUBTITLE, styles["Heading2"]))
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph(
            f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Total: {len(registros)} registros",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 5*mm))

        # Tabla de datos
        headers = ["HOTEL", "APELLIDO", "NOMBRE", "DNI", "NACIONALIDAD", "ENTRADA", "SALIDA"]
        table_data = [headers]
        for reg in registros:
            table_data.append([
                str(reg.get("establecimiento", "")),
                str(reg.get("apellido", "")),
                str(reg.get("nombre", "")),
                str(reg.get("dni", "") or reg.get("pasaporte", "")),
                str(reg.get("nacionalidad", "")),
                str(reg.get("fecha_entrada", "")),
                str(reg.get("fecha_salida", "")),
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f538d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
        ]))
        elements.append(table)

        doc.build(elements)
        logger.info("Exportación PDF: %s (%d registros)", filepath, len(registros))
        return filepath
