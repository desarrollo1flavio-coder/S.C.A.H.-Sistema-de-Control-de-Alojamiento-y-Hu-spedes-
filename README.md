# 🛡️ S.C.A.H. — Sistema de Control de Alojamiento y Huéspedes

**Departamento de Inteligencia Criminal — Policía de Tucumán — Sección Hoteles**

Aplicación de escritorio para el registro, búsqueda y gestión de huéspedes en alojamientos hoteleros, desarrollada con Python y CustomTkinter.

---

## 📋 Características

- **Carga manual** de huéspedes con validación en tiempo real
- **Importación masiva** desde archivos Excel (.xlsx / .xls) con mapeo automático de columnas
- **Búsqueda rápida** (con debounce) y **búsqueda avanzada** con filtros y operadores AND/OR
- **Exportación** a Excel (formateado) y PDF (con encabezado institucional)
- **Autenticación** con bcrypt, bloqueo de cuenta tras intentos fallidos
- **Roles**: Admin, Supervisor, Operador con permisos diferenciados
- **Auditoría completa** de todas las operaciones (INSERT, UPDATE, DELETE)
- **Soft-delete** para registros de huéspedes
- **Tema oscuro/claro** conmutable en tiempo real

## 🛠️ Tecnologías

| Componente    | Tecnología              |
| ------------- | ----------------------- |
| Lenguaje      | Python 3.11+            |
| UI            | CustomTkinter 5.2+      |
| Base de datos | SQLite3 (WAL mode)      |
| Validación    | Pydantic 2.0+           |
| Excel         | Pandas + openpyxl       |
| PDF           | ReportLab               |
| Seguridad     | bcrypt (work factor 12) |

## 📁 Estructura del Proyecto

```
S.C.A.H./
├── main.py                  # Punto de entrada
├── requirements.txt         # Dependencias
├── .env.example             # Variables de entorno
├── config/
│   ├── settings.py          # Configuración global
│   └── database.py          # Conexión SQLite + migraciones
├── models/
│   ├── usuario.py           # Modelo de usuario + DAO
│   ├── huesped.py           # Modelo de huésped + DAO
│   └── auditoria.py         # Log de auditoría
├── controllers/
│   ├── auth_controller.py   # Autenticación y sesiones
│   ├── huesped_controller.py # CRUD de huéspedes
│   ├── import_controller.py  # Importación de Excel
│   └── report_controller.py  # Exportación Excel/PDF
├── views/
│   ├── login_view.py        # Pantalla de login
│   ├── dashboard_view.py    # Dashboard principal
│   ├── manual_view.py       # Formulario de carga manual
│   ├── import_view.py       # Importación de archivos
│   ├── search_view.py       # Búsqueda de huéspedes
│   └── components/
│       ├── status_bar.py    # Barra de estado
│       ├── data_table.py    # Tabla de datos reutilizable
│       └── form_fields.py   # Campos de formulario validados
├── utils/
│   ├── exceptions.py        # Excepciones personalizadas
│   ├── logger.py            # Logging con rotación
│   ├── encryption.py        # Hash bcrypt
│   ├── validators.py        # Validaciones de datos
│   └── excel_parser.py      # Parser de archivos Excel
├── database/
│   └── migrations/
│       └── 001_initial_schema.sql
├── tests/
└── logs/
```

## 🚀 Instalación

### Requisitos previos

- Python 3.11 o superior
- pip (gestor de paquetes)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/desarrollo1flavio-coder/S.C.A.H.-Sistema-de-Control-de-Alojamiento-y-Hu-spedes-.git
cd "S.C.A.H. (Sistema de Control de Alojamiento y Huéspedes)"

# 2. Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
python main.py
```

## 🔑 Credenciales por Defecto

| Campo          | Valor        |
| -------------- | ------------ |
| **Usuario**    | `admin`      |
| **Contraseña** | `Admin2026!` |

> ⚠️ **Cambie la contraseña del administrador en el primer inicio.**

## 📊 Uso

1. **Login**: Ingrese con las credenciales del administrador
2. **Carga Manual**: Use el formulario lateral para registrar huéspedes uno a uno
3. **Importar Excel**: Seleccione un archivo .xlsx, previsualice y confirme la importación
4. **Búsqueda**: Busque por DNI, pasaporte, apellido o nombre; use la búsqueda avanzada para filtros complejos

## 📄 Licencia

Uso interno — Policía de Tucumán.
