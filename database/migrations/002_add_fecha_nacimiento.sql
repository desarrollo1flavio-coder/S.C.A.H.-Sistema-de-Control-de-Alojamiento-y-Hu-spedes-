-- ========================================================================
-- S.C.A.H. - Migración 002: Agregar campo fecha_nacimiento
-- ========================================================================

ALTER TABLE huespedes ADD COLUMN fecha_nacimiento DATE;
