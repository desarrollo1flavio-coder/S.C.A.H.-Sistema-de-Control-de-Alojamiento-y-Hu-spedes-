"""Controlador de importación de archivos Excel para S.C.A.H.

Orquesta el flujo de importación: lectura, validación, previsualización
e inserción masiva de registros de huéspedes.
"""

from pathlib import Path
from typing import Callable, Optional

from controllers.auth_controller import SessionInfo
from models.auditoria import AuditoriaDAO
from models.huesped import HuespedDAO, HuespedSchema
from utils.exceptions import (
    ImportFileError,
    InvalidFileFormatError,
    MissingColumnsError,
    PermissionDeniedError,
    ValidationError,
)
from utils.excel_parser import ExcelParser
from utils.logger import get_logger

logger = get_logger("import_controller")


class ImportController:
    """Controlador para importación de datos desde archivos Excel."""

    def __init__(self, session: SessionInfo) -> None:
        """Inicializa el controlador.

        Args:
            session: Sesión del usuario autenticado.
        """
        self._session = session

    def preview(self, file_path: str | Path) -> dict:
        """Lee un archivo Excel y retorna vista previa + resumen.

        Args:
            file_path: Ruta al archivo Excel.

        Returns:
            Diccionario con datos de previsualización.

        Raises:
            PermissionDeniedError: Sin permisos de escritura.
            InvalidFileFormatError: Formato de archivo inválido.
        """
        if not self._session.tiene_permiso("escritura"):
            raise PermissionDeniedError("Sin permisos para importar datos")

        path = Path(file_path)
        if not path.exists():
            raise InvalidFileFormatError("El archivo no existe")

        if path.suffix.lower() not in (".xlsx", ".xls"):
            raise InvalidFileFormatError("Formato no soportado. Use .xlsx o .xls")

        try:
            parser = ExcelParser(path)
            result = parser.parse()
        except Exception as e:
            raise ImportFileError(f"Error al procesar el archivo: {e}") from e

        if not result.get("valid_rows"):
            raise MissingColumnsError(
                "No se encontraron registros válidos. "
                "Verifique que las columnas del archivo coincidan con: "
                "apellido, nombre, dni/pasaporte, nacionalidad, etc.",
            )

        logger.info(
            "Preview: %d válidos, %d errores — archivo: %s",
            len(result["valid_rows"]),
            len(result.get("errors", [])),
            path.name,
        )

        return result

    def import_data(
        self,
        valid_rows: list[dict],
        *,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> dict:
        """Importa registros válidos a la base de datos.

        Args:
            valid_rows: Lista de diccionarios con datos validados.
            progress_callback: Función callback(current, total) para progreso.

        Returns:
            Diccionario con resumen: imported, errors, skipped.
        """
        if not self._session.tiene_permiso("escritura"):
            raise PermissionDeniedError("Sin permisos para importar datos")

        total = len(valid_rows)
        imported = 0
        errors: list[dict] = []
        skipped = 0

        for i, row in enumerate(valid_rows, 1):
            try:
                # Agregar usuario de carga
                row["usuario_carga"] = self._session.username

                # Validar con Pydantic
                schema = HuespedSchema(**row)
                datos = schema.model_dump()

                # Verificar duplicados en BD
                existentes = HuespedDAO.buscar_por_documento(
                    dni=datos.get("dni"),
                    pasaporte=datos.get("pasaporte"),
                )
                if existentes:
                    skipped += 1
                    doc = datos.get("dni") or datos.get("pasaporte")
                    errors.append({
                        "row": i,
                        "error": f"Documento {doc} ya existe en la BD",
                        "type": "duplicate",
                    })
                    continue

                # Insertar
                huesped_id = HuespedDAO.crear(datos)
                imported += 1

                # Auditoría
                AuditoriaDAO.registrar(
                    usuario=self._session.username,
                    accion="INSERT",
                    tabla_afectada="huespedes",
                    registro_id=huesped_id,
                    datos_nuevos=datos,
                    detalles="Importación desde Excel",
                )

            except Exception as e:
                errors.append({"row": i, "error": str(e), "type": "validation"})

            # Callback de progreso
            if progress_callback:
                try:
                    progress_callback(i, total)
                except Exception:
                    pass

        summary = {
            "total": total,
            "imported": imported,
            "errors": len([e for e in errors if e["type"] != "duplicate"]),
            "skipped": skipped,
            "error_details": errors,
        }

        logger.info(
            "Importación: %d importados, %d omitidos, %d errores — usuario: %s",
            imported, skipped, summary["errors"], self._session.username,
        )

        # Auditoría global
        AuditoriaDAO.registrar(
            usuario=self._session.username,
            accion="INSERT",
            tabla_afectada="huespedes",
            detalles=f"Importación masiva: {imported} registros importados, "
                     f"{skipped} omitidos, {summary['errors']} errores",
        )

        return summary
