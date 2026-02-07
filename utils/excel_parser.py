"""Parser de archivos Excel para S.C.A.H.

Lee, mapea columnas automáticamente, valida filas y retorna datos
listos para importar a la base de datos.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from config.settings import COLUMNAS_MAPEO, MAX_IMPORT_ROWS
from utils.logger import get_logger
from utils.validators import sanitizar_texto

logger = get_logger("utils.excel_parser")


class ExcelParser:
    """Parser de archivos Excel con mapeo automático de columnas."""

    def __init__(self, file_path: Path) -> None:
        """Inicializa el parser.

        Args:
            file_path: Ruta al archivo Excel.
        """
        self._file_path = Path(file_path)
        self._column_map: dict[str, str] = {}

    def parse(self) -> dict:
        """Lee y procesa el archivo Excel.

        Returns:
            Diccionario con:
                - total_rows: número total de filas leídas
                - valid_rows: lista de dicts con datos válidos
                - errors: lista de dicts {row, error}
                - duplicates: lista de dicts con filas duplicadas
                - column_mapping: mapeo de columnas detectado
        """
        logger.info("Parseando archivo: %s", self._file_path)

        df = self._read_file()
        if df.empty:
            return {
                "total_rows": 0, "valid_rows": [], "errors": [],
                "duplicates": [], "column_mapping": {},
            }

        # Limitar filas
        total_rows = len(df)
        if total_rows > MAX_IMPORT_ROWS:
            logger.warning(
                "Archivo truncado: %d filas (máx %d)", total_rows, MAX_IMPORT_ROWS,
            )
            df = df.head(MAX_IMPORT_ROWS)

        # Mapear columnas
        self._column_map = self._auto_map_columns(df.columns.tolist())
        logger.info("Mapeo de columnas: %s", self._column_map)

        # Renombrar columnas según mapeo
        df = df.rename(columns=self._column_map)

        # Procesar filas
        valid_rows: list[dict] = []
        errors: list[dict] = []
        seen_docs: set[str] = set()
        duplicates: list[dict] = []

        for idx, row in df.iterrows():
            row_num = int(idx) + 2  # +2 por header + 0-index
            try:
                data = self._process_row(row)
                if not data:
                    errors.append({"row": row_num, "error": "Fila vacía o sin datos suficientes"})
                    continue

                # Verificar duplicados dentro del archivo
                doc_key = data.get("dni") or data.get("pasaporte") or ""
                if doc_key and doc_key in seen_docs:
                    duplicates.append({"row": row_num, **data})
                    continue
                if doc_key:
                    seen_docs.add(doc_key)

                valid_rows.append(data)

            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})

        result = {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "errors": errors,
            "duplicates": duplicates,
            "column_mapping": self._column_map,
        }

        logger.info(
            "Resultado: %d válidos, %d errores, %d duplicados de %d totales",
            len(valid_rows), len(errors), len(duplicates), total_rows,
        )

        return result

    def _read_file(self) -> pd.DataFrame:
        """Lee el archivo Excel.

        Returns:
            DataFrame con datos del archivo.
        """
        try:
            suffix = self._file_path.suffix.lower()
            engine = "openpyxl" if suffix == ".xlsx" else "xlrd"

            df = pd.read_excel(
                self._file_path,
                engine=engine,
                dtype=str,
                keep_default_na=False,
            )

            # Limpiar nombres de columnas
            df.columns = [
                str(col).strip().lower().replace(" ", "_")
                for col in df.columns
            ]

            # Eliminar filas completamente vacías
            df = df.dropna(how="all")
            df = df[df.astype(str).apply(lambda x: x.str.strip().str.len().sum(), axis=1) > 0]

            logger.info("Archivo leído: %d filas, %d columnas", len(df), len(df.columns))
            return df

        except Exception as e:
            logger.error("Error al leer archivo Excel: %s", e)
            raise ValueError(f"No se pudo leer el archivo: {e}") from e

    def _auto_map_columns(self, file_columns: list[str]) -> dict[str, str]:
        """Mapea columnas del archivo a campos del sistema.

        Args:
            file_columns: Nombres de columnas del archivo.

        Returns:
            Mapeo {columna_archivo: campo_sistema}.
        """
        mapping: dict[str, str] = {}

        for system_field, aliases in COLUMNAS_MAPEO.items():
            for col in file_columns:
                col_clean = col.strip().lower().replace(" ", "_")
                if col_clean in aliases:
                    mapping[col] = system_field
                    break

        return mapping

    def _process_row(self, row: pd.Series) -> Optional[dict]:
        """Procesa una fila del DataFrame.

        Args:
            row: Serie de Pandas con datos de la fila.

        Returns:
            Diccionario con datos procesados o None si la fila es inválida.
        """
        data: dict[str, Any] = {}

        # Campos de texto
        for field in ("apellido", "nombre", "nacionalidad", "procedencia",
                       "profesion", "habitacion", "destino", "telefono",
                       "vehiculo"):
            val = self._get_value(row, field)
            if val:
                data[field] = sanitizar_texto(val) if field in (
                    "apellido", "nombre", "nacionalidad", "procedencia",
                ) else val.strip()

        # Documentos
        dni = self._get_value(row, "dni")
        if dni:
            dni = dni.strip().replace(".", "").replace("-", "")
            if dni.isdigit() and 7 <= len(dni) <= 8:
                data["dni"] = dni

        pasaporte = self._get_value(row, "pasaporte")
        if pasaporte:
            pasaporte = pasaporte.strip().upper()
            if pasaporte.isalnum() and 5 <= len(pasaporte) <= 15:
                data["pasaporte"] = pasaporte

        # Validar que tenga al menos un documento
        if "dni" not in data and "pasaporte" not in data:
            raise ValueError("Sin documento válido (DNI o Pasaporte)")

        # Validar campos obligatorios
        for required in ("apellido", "nombre"):
            if required not in data or not data[required]:
                raise ValueError(f"Campo obligatorio '{required}' vacío")

        # Defaults para campos obligatorios faltantes
        if "nacionalidad" not in data:
            data["nacionalidad"] = "Argentina"
        if "procedencia" not in data:
            data["procedencia"] = "Sin especificar"
        if "habitacion" not in data:
            data["habitacion"] = "S/N"

        # Edad
        edad = self._get_value(row, "edad")
        if edad:
            try:
                edad_int = int(float(edad))
                if 0 < edad_int < 150:
                    data["edad"] = edad_int
            except (ValueError, TypeError):
                pass

        # Fechas
        data["fecha_entrada"] = self._parse_date(
            self._get_value(row, "fecha_entrada"),
        ) or date.today()

        fecha_salida = self._parse_date(self._get_value(row, "fecha_salida"))
        if fecha_salida:
            data["fecha_salida"] = fecha_salida

        # Vehículo
        vehiculo = data.pop("vehiculo", None)
        if vehiculo:
            data["vehiculo_tiene"] = True
            data["vehiculo_datos"] = vehiculo
        else:
            data["vehiculo_tiene"] = False

        return data

    @staticmethod
    def _get_value(row: pd.Series, field: str) -> Optional[str]:
        """Obtiene un valor de la fila.

        Args:
            row: Serie de datos.
            field: Nombre del campo.

        Returns:
            Valor como string o None.
        """
        if field in row.index:
            val = row[field]
            if pd.notna(val) and str(val).strip():
                return str(val).strip()
        return None

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[date]:
        """Parsea una fecha desde múltiples formatos.

        Args:
            value: String con la fecha.

        Returns:
            Objeto date o None.
        """
        if not value:
            return None

        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d.%m.%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue

        # Intentar con pandas
        try:
            return pd.to_datetime(value).date()
        except Exception:
            return None
