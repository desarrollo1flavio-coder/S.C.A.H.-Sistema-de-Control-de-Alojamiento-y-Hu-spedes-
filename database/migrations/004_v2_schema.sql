-- ========================================================================
-- S.C.A.H. - Migración 004: Esquema V2
-- Separación de personas y estadías para soportar historial.
-- Nuevas tablas: personas, estadias, establecimientos, habitaciones.
-- Migración de datos de huespedes → personas + estadias.
-- ========================================================================

PRAGMA foreign_keys=OFF;

-- ========================================================================
-- TABLA: establecimientos
-- ========================================================================
CREATE TABLE IF NOT EXISTS establecimientos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT    UNIQUE NOT NULL COLLATE NOCASE,
    direccion   TEXT,
    telefono    TEXT,
    activo      BOOLEAN DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- TABLA: habitaciones
-- ========================================================================
CREATE TABLE IF NOT EXISTS habitaciones (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    establecimiento_id  INTEGER NOT NULL REFERENCES establecimientos(id),
    numero              TEXT    NOT NULL,
    tipo                TEXT    DEFAULT 'standard',
    capacidad           INTEGER DEFAULT 2 CHECK(capacidad > 0 AND capacidad <= 20),
    estado              TEXT    DEFAULT 'disponible'
                        CHECK(estado IN ('disponible', 'ocupada', 'mantenimiento', 'reservada')),
    activo              BOOLEAN DEFAULT 1,
    UNIQUE(establecimiento_id, numero)
);

-- ========================================================================
-- TABLA: personas (datos fijos de la persona)
-- ========================================================================
CREATE TABLE IF NOT EXISTS personas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nacionalidad    TEXT    NOT NULL,
    procedencia     TEXT    NOT NULL,
    apellido        TEXT    NOT NULL COLLATE NOCASE,
    nombre          TEXT    NOT NULL COLLATE NOCASE,
    dni             TEXT    UNIQUE,
    pasaporte       TEXT    UNIQUE,
    fecha_nacimiento DATE,
    profesion       TEXT,
    telefono        TEXT,
    fecha_registro  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo          BOOLEAN DEFAULT 1,
    CONSTRAINT chk_persona_doc CHECK (dni IS NOT NULL OR pasaporte IS NOT NULL)
);

-- ========================================================================
-- TABLA: estadias (cada visita / check-in de una persona)
-- ========================================================================
CREATE TABLE IF NOT EXISTS estadias (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_id          INTEGER NOT NULL REFERENCES personas(id),
    establecimiento     TEXT,
    habitacion          TEXT    DEFAULT 'S/N',
    edad                INTEGER CHECK(edad IS NULL OR (edad > 0 AND edad < 150)),
    fecha_entrada       DATE    NOT NULL,
    fecha_salida        DATE,
    destino             TEXT,
    vehiculo_tiene      BOOLEAN DEFAULT 0,
    vehiculo_datos      TEXT,
    usuario_carga       TEXT    NOT NULL,
    fecha_registro      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo              BOOLEAN DEFAULT 1,
    CONSTRAINT chk_estadia_fechas CHECK (fecha_salida IS NULL OR fecha_salida >= fecha_entrada)
);

-- ========================================================================
-- MIGRAR DATOS EXISTENTES de huespedes → personas + estadias
-- ========================================================================

-- Paso 1: Insertar personas únicas desde huespedes
INSERT OR IGNORE INTO personas (nacionalidad, procedencia, apellido, nombre, dni, pasaporte, fecha_nacimiento, profesion, telefono, fecha_registro, activo)
SELECT DISTINCT
    nacionalidad,
    procedencia,
    apellido,
    nombre,
    dni,
    pasaporte,
    fecha_nacimiento,
    profesion,
    telefono,
    fecha_registro,
    activo
FROM huespedes
WHERE EXISTS (SELECT 1 FROM huespedes LIMIT 1);

-- Paso 2: Insertar estadías vinculadas a personas
INSERT INTO estadias (persona_id, establecimiento, habitacion, edad, fecha_entrada, fecha_salida, destino, vehiculo_tiene, vehiculo_datos, usuario_carga, fecha_registro, activo)
SELECT
    p.id,
    h.establecimiento,
    h.habitacion,
    h.edad,
    h.fecha_entrada,
    h.fecha_salida,
    h.destino,
    h.vehiculo_tiene,
    h.vehiculo_datos,
    h.usuario_carga,
    h.fecha_registro,
    h.activo
FROM huespedes h
INNER JOIN personas p ON (
    (h.dni IS NOT NULL AND h.dni = p.dni)
    OR (h.pasaporte IS NOT NULL AND h.pasaporte = p.pasaporte)
)
WHERE EXISTS (SELECT 1 FROM huespedes LIMIT 1);

-- ========================================================================
-- ACTUALIZAR TABLA AUDITORIA para nuevas acciones
-- ========================================================================
-- Quitar el CHECK constraint limitante reemplazando la tabla
CREATE TABLE IF NOT EXISTS auditoria_v2 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario          TEXT    NOT NULL,
    accion           TEXT    NOT NULL,
    tabla_afectada   TEXT,
    registro_id      INTEGER,
    datos_anteriores TEXT,
    datos_nuevos     TEXT,
    detalles         TEXT,
    fecha            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO auditoria_v2 SELECT * FROM auditoria
WHERE EXISTS (SELECT 1 FROM auditoria LIMIT 1);

DROP TABLE IF EXISTS auditoria;
ALTER TABLE auditoria_v2 RENAME TO auditoria;

-- ========================================================================
-- ÍNDICES DE RENDIMIENTO (nuevas tablas)
-- ========================================================================
CREATE INDEX IF NOT EXISTS idx_personas_dni ON personas(dni);
CREATE INDEX IF NOT EXISTS idx_personas_pasaporte ON personas(pasaporte);
CREATE INDEX IF NOT EXISTS idx_personas_apellido ON personas(apellido);
CREATE INDEX IF NOT EXISTS idx_personas_nombre ON personas(nombre);
CREATE INDEX IF NOT EXISTS idx_personas_activo ON personas(activo);

CREATE INDEX IF NOT EXISTS idx_estadias_persona ON estadias(persona_id);
CREATE INDEX IF NOT EXISTS idx_estadias_fechas ON estadias(fecha_entrada, fecha_salida);
CREATE INDEX IF NOT EXISTS idx_estadias_establecimiento ON estadias(establecimiento);
CREATE INDEX IF NOT EXISTS idx_estadias_activo ON estadias(activo);

CREATE INDEX IF NOT EXISTS idx_establecimientos_nombre ON establecimientos(nombre);
CREATE INDEX IF NOT EXISTS idx_habitaciones_estab ON habitaciones(establecimiento_id);

CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria(usuario);
CREATE INDEX IF NOT EXISTS idx_auditoria_accion ON auditoria(accion);

PRAGMA foreign_keys=ON;
