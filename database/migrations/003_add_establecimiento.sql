-- Migración: Agregar campo establecimiento a huespedes
-- Fecha: 2026-02-08
-- Descripción: Almacena el nombre del hotel/establecimiento donde se aloja el huésped

ALTER TABLE huespedes ADD COLUMN establecimiento VARCHAR(150);
