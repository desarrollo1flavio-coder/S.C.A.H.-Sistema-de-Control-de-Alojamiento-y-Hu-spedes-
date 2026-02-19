"""Modelo y DAO de Auditoría para S.C.A.H. v2."""

import json
from typing import Optional

from config.database import get_connection, get_transaction
from utils.logger import get_logger

logger = get_logger("models.auditoria")


class AuditoriaDAO:
    """Operaciones de base de datos para la tabla 'auditoria'."""

    @staticmethod
    def registrar(
        usuario: str,
        accion: str,
        tabla_afectada: Optional[str] = None,
        registro_id: Optional[int] = None,
        datos_anteriores: Optional[dict] = None,
        datos_nuevos: Optional[dict] = None,
        detalles: Optional[str] = None,
    ) -> int:
        datos_ant_json = (
            json.dumps(datos_anteriores, ensure_ascii=False, default=str)
            if datos_anteriores else None
        )
        datos_new_json = (
            json.dumps(datos_nuevos, ensure_ascii=False, default=str)
            if datos_nuevos else None
        )
        try:
            with get_transaction() as conn:
                cursor = conn.execute(
                    "INSERT INTO auditoria "
                    "(usuario, accion, tabla_afectada, registro_id, "
                    "datos_anteriores, datos_nuevos, detalles) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (usuario, accion, tabla_afectada, registro_id,
                     datos_ant_json, datos_new_json, detalles),
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error("Error al registrar auditoría: %s", e)
            return -1

    @staticmethod
    def buscar(
        usuario: Optional[str] = None,
        accion: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        limite: int = 100,
    ) -> list[dict]:
        query = "SELECT * FROM auditoria WHERE 1=1"
        params: list = []
        if usuario:
            query += " AND usuario = ?"
            params.append(usuario)
        if accion:
            query += " AND accion = ?"
            params.append(accion)
        if fecha_desde:
            query += " AND fecha >= ?"
            params.append(fecha_desde)
        if fecha_hasta:
            query += " AND fecha <= ?"
            params.append(fecha_hasta + " 23:59:59")
        query += " ORDER BY fecha DESC LIMIT ?"
        params.append(limite)
        with get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
