# --- Forzar el AppUserModelID para el icono de la barra de tareas en Windows ---
import ctypes
import os
import sys

# ID único para esta versión para forzar el refresco de Windows
# Si no funciona, cambiaremos este string ligeramente cada vez.
MY_APP_ID = u'SGA.SistemaGestionAcademica.Studio.v5'

try:
    # Este paso es CRUCIAL para que Windows no agrupe el proceso con Python.exe
    res = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(MY_APP_ID)
    # print(f"Registro de AppID {MY_APP_ID}: {'Éxito' if res == 0 else 'Fallo'}")
except Exception as e:
    print(f"Error crítico de sistema al registrar AppID: {e}")
# --------------------------------------------------------------------------

import json
import traceback

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView

from core.paths import PATH_ICO, PATH_PNG

CONFIG_PATH = os.path.join(os.path.expanduser("~"), "AsmoRoot_config.json")

def cargar_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"configurado": True} # Forzamos True para pruebas

if __name__ == "__main__":
    try:
        # Configuración de High DPI
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

        app = QApplication(sys.argv)
        app.setFont(QFont("Segoe UI", 10))
        app.setStyle("Fusion")
        
        # Intentar cargar el icono (probamos .ico y luego .png como respaldo)
        debug_path = os.path.join(os.path.expanduser("~"), "debug_sga.txt")
        with open(debug_path, "w") as f:
            f.write(f"PATH_ICO: {PATH_ICO}\n")
            f.write(f"PATH_PNG: {PATH_PNG}\n")
            f.write(f"ICO exists: {os.path.exists(PATH_ICO)}\n")
            f.write(f"PNG exists: {os.path.exists(PATH_PNG)}\n")
        app_icon = QIcon()
        if os.path.exists(PATH_ICO):
            app_icon.addFile(PATH_ICO)
        if os.path.exists(PATH_PNG):
            app_icon.addFile(PATH_PNG)
            
        with open(debug_path, "a") as f:
            f.write(f"Icon is null: {app_icon.isNull()}\n")
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
        else:
            with open(debug_path, "a") as f:
                f.write(f"PELIGRO: No se pudo cargar ningún icono desde {PATH_ICO}\n")

        app.setStyleSheet("""
            QToolTip {
                background: rgba(25,25,40,240);
                color: rgba(255,255,255,210);
                border: 1px solid rgba(255,255,255,25);
                border-radius: 7px;
                padding: 5px 10px;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # Omitimos el asistente para depurar
        from ui.main_window import SGAApp
        window = SGAApp()
        
        # Forzamos el icono de nuevo en la ventana principal expresamente
        if not app_icon.isNull():
            window.setWindowIcon(app_icon)

        window.showMaximized()

        from core.updater import Updater
        updater = Updater(window, window.version_sistema)
        updater.verificar()

        # Ejecución
        exit_code = app.exec()
        window.close()
        del window
        sys.exit(exit_code)
        
    except Exception as e:
        print("\n" + "!"*60)
        print("ERROR CRÍTICO AL INICIAR SGA:")
        print("!"*60)
        traceback.print_exc()
        print("!"*60 + "\n")
        input("Presiona Enter para cerrar...")
        sys.exit(1)