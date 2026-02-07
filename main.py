"""Punto de entrada principal de S.C.A.H.

Inicializa la base de datos, crea el usuario admin por defecto
y lanza la ventana de login.
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz esté en el path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.database import initialize_database
from config.settings import APP_TITLE
from controllers.auth_controller import AuthController, SessionInfo
from utils.logger import get_logger, setup_logger
from views.login_view import LoginView

logger = get_logger("main")


def main() -> None:
    """Función principal de la aplicación."""
    setup_logger()
    logger.info("=" * 60)
    logger.info("Iniciando %s", APP_TITLE)
    logger.info("=" * 60)

    # 1. Inicializar base de datos y migraciones
    try:
        initialize_database()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.critical("Error fatal al inicializar BD: %s", e)
        print(f"[ERROR FATAL] No se pudo inicializar la base de datos: {e}")
        sys.exit(1)

    # 2. Crear controlador de autenticación y admin por defecto
    auth = AuthController()
    try:
        auth.ensure_admin_exists()
        logger.info("Usuario admin verificado/creado")
    except Exception as e:
        logger.error("Error al verificar admin: %s", e)

    # 3. Lanzar login
    def on_login_success(session: SessionInfo) -> None:
        """Callback al loguearse exitosamente.

        Args:
            session: Sesión del usuario.
        """
        logger.info("Login exitoso: %s (%s)", session.nombre_completo, session.rol)

        # Ocultar login y abrir dashboard
        login_app.withdraw()

        from views.dashboard_view import DashboardView

        def on_logout() -> None:
            """Restaura la ventana de login al cerrar sesión."""
            login_app.deiconify()
            login_app._password_entry.delete(0, "end")
            login_app._username_entry.focus_set()
            login_app._msg_label.configure(text="")

        dashboard = DashboardView(
            master=login_app,
            session=session,
            auth_controller=auth,
            on_logout=on_logout,
        )

    login_app = LoginView(
        auth_controller=auth,
        on_login_success=on_login_success,
    )

    logger.info("Aplicación lista — esperando login")
    login_app.mainloop()

    logger.info("Aplicación cerrada")


if __name__ == "__main__":
    main()
