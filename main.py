import sys
import os
import ctypes
import json
import traceback

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView

from core.paths import PATH_ICO

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
        # Fix para que el icono se vea en la barra de tareas de Windows
        myappid = u'asmoroot.academic.management.v2.9'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

        app = QApplication(sys.argv)
        app.setFont(QFont("Segoe UI", 10))
        app.setStyle("Fusion")
        
        if os.path.exists(PATH_ICO):
            app.setWindowIcon(QIcon(PATH_ICO))
        
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
        from ui.main_window import AsmoRootApp
        window = AsmoRootApp()
        window.showMaximized()

        from core.updater import Updater
        updater = Updater(window, window.version_sistema)
        updater.verificar()

        sys.exit(app.exec())
        
    except Exception as e:
        print("\n" + "!"*60)
        print("ERROR CRÍTICO AL INICIAR ASMOROOT:")
        print("!"*60)
        traceback.print_exc()
        print("!"*60 + "\n")
        input("Presiona Enter para cerrar...")
        sys.exit(1)