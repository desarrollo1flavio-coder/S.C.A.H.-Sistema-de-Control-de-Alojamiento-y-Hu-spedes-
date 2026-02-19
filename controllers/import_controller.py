"""Controlador de importación Excel para S.C.A.H. v2.

Orquesta: lectura del Excel -> detección de columnas -> procesamiento ->
creación de personas y estadías en la BD.
"""

from pathlib import Path
from typing import Callable, Optional

from controllers.persona_controller import PersonaController
from controllers.estadia_controller import EstadiaController
from models.auditoria import AuditoriaDAO
from utils.excel_parser import (
    leer_archivo,
    detectar_mapeo,
    obtener_columnas_faltantes,
    procesar_dataframe,
    preview_archivo,
)
from utils.exceptions import ImportFileError, MissingColumnsError
from utils.logger import get_logger

logger = get_logger("import_controller")


class ImportController:
    """Orquesta la importación de datos desde archivos Excel."""

    def __init__(self, usuario: str = "sistema"):
        self.usuario = usuario
        self.persona_ctrl = PersonaController(usuario)
        self.estadia_ctrl = EstadiaController(usuario)

    def preview(self, filepath: str) -> dict:
        """Genera un preview del archivo para confirmación."""
        return preview_archivo(filepath)

    def importar(
        self,
        filepath: str,
        mapeo_override: dict[str, str] | None = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict:
        """Importa datos desde un archivo Excel.

        Args:
            filepath: Ruta al archivo Excel
            mapeo_override: Mapeo manual (opcional, sobreescribe autodetección)
            on_progress: Callback (actual, total, mensaje) para progreso

        Returns:
            dict con estadísticas de la importación
        """
        stats = {
            "archivo": str(filepath),
            "total_filas": 0,
            "personas_creadas": 0,
            "personas_existentes": 0,
            "estadias_creadas": 0,
            "errores": [],
            "warnings": [],
        }

        try:
            # 1. Leer archivo
            if on_progress:
                on_progress(0, 100, "Leyendo archivo Excel...")
            df = leer_archivo(filepath)
            stats["total_filas"] = len(df)

            # 2. Detectar mapeo
            if on_progress:
                on_progress(5, 100, "Detectando columnas...")
            mapeo = mapeo_override or detectar_mapeo(df)
            faltantes = obtener_columnas_faltantes(mapeo)
            if faltantes:
                raise MissingColumnsError(missing=faltantes)

            # 3. Procesar filas
            if on_progress:
                on_progress(10, 100, "Procesando datos...")
            registros, errores_parse = procesar_dataframe(df, mapeo)
            stats["errores"].extend(errores_parse)

            # 4. Insertar en BD
            total = len(registros)
            for i, reg in enumerate(registros):
                try:
                    # Crear o encontrar persona
                    datos_persona = {
                        k: reg[k] for k in (
                            "nacionalidad", "procedencia", "apellido", "nombre",
                            "dni", "pasaporte", "fecha_nacimiento", "profesion", "telefono",
                        ) if reg.get(k) is not None
                    }
                    persona_id = self.persona_ctrl.obtener_o_crear(datos_persona)

                    # Verificar si es persona nueva o existente
                    from models.persona import PersonaDAO
                    # (la lógica de obtener_o_crear ya maneja esto)

                    # Crear estadía
                    datos_estadia = {
                        "persona_id": persona_id,
                        "establecimiento": reg.get("establecimiento"),
                        "habitacion": reg.get("habitacion", "S/N"),
                        "edad": reg.get("edad"),
                        "fecha_entrada": reg["fecha_entrada"],
                        "fecha_salida": reg.get("fecha_salida"),
                        "destino": reg.get("destino"),
                        "vehiculo_tiene": reg.get("vehiculo_tiene", False),
                        "vehiculo_datos": reg.get("vehiculo_datos"),
                        "usuario_carga": self.usuario,
                    }
                    self.estadia_ctrl.crear(datos_estadia)
                    stats["estadias_creadas"] += 1

                    if on_progress and i % 10 == 0:
                        pct = 10 + int(85 * (i + 1) / total)
                        on_progress(pct, 100, f"Importando registro {i+1} de {total}...")

                except Exception as e:
                    stats["errores"].append({
                        "fila": i + 2,
                        "datos": {k: str(v) for k, v in reg.items() if v is not None},
                        "errores": [str(e)],
                    })

            if on_progress:
                on_progress(100, 100, "Importación completada")

        except (ImportFileError, MissingColumnsError):
            raise
        except Exception as e:
            logger.error("Error durante importación: %s", e)
            raise ImportFileError(f"Error al importar: {e}") from e

        # Registrar en auditoría
        AuditoriaDAO.registrar(
            usuario=self.usuario,
            accion="IMPORTAR_EXCEL",
            tabla_afectada="estadias",
            detalles=(
                f"Archivo: {Path(filepath).name} | "
                f"Filas: {stats['total_filas']} | "
                f"Estadías creadas: {stats['estadias_creadas']} | "
                f"Errores: {len(stats['errores'])}"
            ),
        )

        logger.info(
            "Importación completada: %d estadías de %d filas (%d errores)",
            stats["estadias_creadas"], stats["total_filas"], len(stats["errores"]),
        )
        return stats
