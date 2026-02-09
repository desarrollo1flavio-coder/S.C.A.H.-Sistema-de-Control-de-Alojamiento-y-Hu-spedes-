-- ========================================================================
-- S.C.A.H. - Migración 001: Esquema Inicial
-- Sistema de Control de Alojamiento y Huéspedes
-- Departamento de Inteligencia Criminal - Policía de Tucumán
-- ========================================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA encoding='UTF-8';

-- ========================================================================
-- TABLA: huespedes
-- ========================================================================
CREATE TABLE IF NOT EXISTS huespedes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nacionalidad    TEXT    NOT NULL,
    procedencia     TEXT    NOT NULL,
    apellido        TEXT    NOT NULL COLLATE NOCASE,
    nombre          TEXT    NOT NULL COLLATE NOCASE,
    dni             TEXT    UNIQUE,
    pasaporte       TEXT    UNIQUE,
    edad            INTEGER CHECK(edad IS NULL OR (edad > 0 AND edad < 150)),
    fecha_nacimiento DATE,
    profesion       TEXT,
    establecimiento TEXT,
    habitacion      TEXT    NOT NULL,
    destino         TEXT,
    vehiculo_tiene  BOOLEAN DEFAULT 0,
    vehiculo_datos  TEXT,
    telefono        TEXT,
    fecha_entrada   DATE    NOT NULL,
    fecha_salida    DATE,
    fecha_registro  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_carga   TEXT    NOT NULL,
    activo          BOOLEAN DEFAULT 1,
    CONSTRAINT chk_dni_o_pasaporte CHECK (dni IS NOT NULL OR pasaporte IS NOT NULL),
    CONSTRAINT chk_fechas CHECK (fecha_salida IS NULL OR fecha_salida >= fecha_entrada)
);

-- ========================================================================
-- TABLA: usuarios
-- ========================================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    username          TEXT    UNIQUE NOT NULL COLLATE NOCASE,
    password_hash     TEXT    NOT NULL,
    nombre_completo   TEXT    NOT NULL,
    rol               TEXT    NOT NULL DEFAULT 'operador'
                      CHECK(rol IN ('admin', 'supervisor', 'operador')),
    activo            BOOLEAN DEFAULT 1,
    ultimo_acceso     TIMESTAMP,
    intentos_fallidos INTEGER DEFAULT 0,
    bloqueado_hasta   TIMESTAMP,
    fecha_creacion    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- TABLA: auditoria (inmutable, solo INSERT)
-- ========================================================================
CREATE TABLE IF NOT EXISTS auditoria (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario          TEXT    NOT NULL,
    accion           TEXT    NOT NULL
                     CHECK(accion IN (
                         'INSERT', 'UPDATE', 'DELETE',
                         'LOGIN', 'LOGOUT', 'LOGIN_FAILED',
                         'IMPORT', 'EXPORT', 'BACKUP',
                         'USER_CREATE', 'USER_UPDATE', 'USER_DISABLE'
                     )),
    tabla_afectada   TEXT,
    registro_id      INTEGER,
    datos_anteriores TEXT,
    datos_nuevos     TEXT,
    detalles         TEXT,
    fecha            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- ÍNDICES DE RENDIMIENTO
-- ========================================================================
CREATE INDEX IF NOT EXISTS idx_huespedes_dni ON huespedes(dni);
CREATE INDEX IF NOT EXISTS idx_huespedes_pasaporte ON huespedes(pasaporte);
CREATE INDEX IF NOT EXISTS idx_huespedes_apellido ON huespedes(apellido);
CREATE INDEX IF NOT EXISTS idx_huespedes_nombre ON huespedes(nombre);
CREATE INDEX IF NOT EXISTS idx_huespedes_fechas ON huespedes(fecha_entrada, fecha_salida);
CREATE INDEX IF NOT EXISTS idx_huespedes_nacionalidad ON huespedes(nacionalidad);
CREATE INDEX IF NOT EXISTS idx_huespedes_activo ON huespedes(activo);
CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);
CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(activo);
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria(usuario);
CREATE INDEX IF NOT EXISTS idx_auditoria_accion ON auditoria(accion);
