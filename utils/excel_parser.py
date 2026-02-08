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
        self._sheet_count: int = 0
        self._sheet_names: list[str] = []

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

        # Mapear columnas (excluyendo columnas internas)
        map_cols = [c for c in df.columns.tolist() if not c.startswith("_")]
        self._column_map = self._auto_map_columns(map_cols)
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
            hoja = row.get("_hoja_origen", "")
            row_label = f"Hoja '{hoja}' fila {row_num}" if hoja else f"Fila {row_num}"
            try:
                data = self._process_row(row)
                if not data:
                    errors.append({"row": row_label, "error": "Fila vacía o sin datos suficientes"})
                    continue

                # Guardar hoja de origen en el registro
                if hoja:
                    data["_hoja_origen"] = hoja

                # Verificar duplicados dentro del archivo
                doc_key = data.get("dni") or data.get("pasaporte") or ""
                if doc_key and doc_key in seen_docs:
                    duplicates.append({"row": row_label, **data})
                    continue
                if doc_key:
                    seen_docs.add(doc_key)

                valid_rows.append(data)

            except Exception as e:
                errors.append({"row": row_label, "error": str(e)})

        result = {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "errors": errors,
            "duplicates": duplicates,
            "column_mapping": self._column_map,
            "sheet_count": self._sheet_count,
            "sheet_names": self._sheet_names,
        }

        logger.info(
            "Resultado: %d válidos, %d errores, %d duplicados de %d totales",
            len(valid_rows), len(errors), len(duplicates), total_rows,
        )

        return result

    def _read_file(self) -> pd.DataFrame:
        """Lee TODAS las hojas del archivo Excel y las concatena.

        Returns:
            DataFrame con datos combinados de todas las hojas.
        """
        try:
            suffix = self._file_path.suffix.lower()
            engine = "openpyxl" if suffix == ".xlsx" else "xlrd"

            # Leer TODAS las hojas (sheet_name=None devuelve dict)
            all_sheets = pd.read_excel(
                self._file_path,
                engine=engine,
                dtype=str,
                keep_default_na=False,
                sheet_name=None,
            )

            self._sheet_count = len(all_sheets)
            self._sheet_names = list(all_sheets.keys())
            logger.info(
                "Hojas encontradas (%d): %s",
                self._sheet_count, self._sheet_names,
            )

            frames: list[pd.DataFrame] = []
            for sheet_name, sheet_df in all_sheets.items():
                if sheet_df.empty:
                    logger.info("Hoja '%s' vacía, omitida", sheet_name)
                    continue

                # Limpiar nombres de columnas
                sheet_df.columns = [
                    str(col).strip().lower().replace(" ", "_")
                    for col in sheet_df.columns
                ]

                # Eliminar filas completamente vacías
                sheet_df = sheet_df.dropna(how="all")
                sheet_df = sheet_df[
                    sheet_df.astype(str).apply(
                        lambda x: x.str.strip().str.len().sum(), axis=1,
                    ) > 0
                ]

                if not sheet_df.empty:
                    sheet_df = sheet_df.copy()
                    sheet_df["_hoja_origen"] = str(sheet_name)
                    frames.append(sheet_df)
                    logger.info(
                        "Hoja '%s': %d filas, %d columnas",
                        sheet_name, len(sheet_df), len(sheet_df.columns) - 1,
                    )

            if not frames:
                logger.warning("Ninguna hoja contiene datos")
                return pd.DataFrame()

            # Concatenar todas las hojas
            df = pd.concat(frames, ignore_index=True, sort=False)
            # Rellenar NaN de columnas faltantes con cadena vacía
            df = df.fillna("")

            logger.info(
                "Total combinado: %d filas de %d hojas",
                len(df), len(frames),
            )
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
        import unicodedata

        def normalize(text: str) -> str:
            """Normaliza texto removiendo acentos y caracteres especiales."""
            text = text.strip().lower().replace(" ", "_")
            nfkd = unicodedata.normalize("NFKD", text)
            ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
            ascii_text = ascii_text.replace(".", "").replace("°", "").replace("º", "")
            return ascii_text

        mapping: dict[str, str] = {}
        used_fields: set[str] = set()

        for system_field, aliases in COLUMNAS_MAPEO.items():
            normalized_aliases = [normalize(a) for a in aliases]
            for col in file_columns:
                if col in mapping:
                    continue
                col_clean = col.strip().lower().replace(" ", "_")
                col_normalized = normalize(col)

                # Coincidencia exacta o normalizada
                if col_clean in aliases or col_normalized in normalized_aliases:
                    mapping[col] = system_field
                    used_fields.add(system_field)
                    break

                # Coincidencia parcial (solo con aliases de 5+ caracteres)
                for alias in aliases:
                    alias_norm = normalize(alias)
                    if len(alias_norm) >= 5 and (
                        alias_norm in col_normalized or col_normalized in alias_norm
                    ):
                        if system_field not in used_fields:
                            mapping[col] = system_field
                            used_fields.add(system_field)
                            break
                if system_field in used_fields:
                    break

        logger.info("Columnas del archivo: %s", file_columns)
        logger.info("Mapeo resultante: %s", mapping)
        logger.info("Columnas no mapeadas: %s", [c for c in file_columns if c not in mapping])

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

        # Documentos — detectar tipo automáticamente
        dni = self._get_value(row, "dni")
        pasaporte = self._get_value(row, "pasaporte")

        # Si hay columna combinada DNI/Pasaporte, detectar tipo
        if dni and not pasaporte:
            cleaned = dni.strip().replace(".", "").replace("-", "").replace(" ", "")
            if cleaned.endswith(".0"):  # Fix float de Excel
                cleaned = cleaned[:-2]
            if cleaned.isdigit() and 7 <= len(cleaned) <= 8:
                data["dni"] = cleaned
            elif cleaned.isalnum() and 5 <= len(cleaned) <= 15:
                data["pasaporte"] = cleaned.upper()
        else:
            if dni:
                cleaned = dni.strip().replace(".", "").replace("-", "").replace(" ", "")
                if cleaned.endswith(".0"):
                    cleaned = cleaned[:-2]
                if cleaned.isdigit() and 7 <= len(cleaned) <= 8:
                    data["dni"] = cleaned
            if pasaporte:
                cleaned_p = pasaporte.strip().upper().replace(" ", "")
                if cleaned_p.isalnum() and 5 <= len(cleaned_p) <= 15:
                    data["pasaporte"] = cleaned_p

        # Fallback: buscar número de 7-8 dígitos en cualquier columna
        if "dni" not in data and "pasaporte" not in data:
            for col_val in row.values:
                val = str(col_val).strip().replace(".", "").replace("-", "").replace(" ", "")
                if val.endswith(".0"):
                    val = val[:-2]
                if val.isdigit() and 7 <= len(val) <= 8:
                    data["dni"] = val
                    break

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
