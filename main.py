import sys
import os
import json

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView  # DEBE ir antes de QApplication

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.expanduser("~"), "AsmoRoot_config.json")


def cargar_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"configurado": False}


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyle("Fusion")
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

    config = cargar_config()

    # ── Primera vez → mostrar wizard ──────────
    if not config.get("configurado", False):
        from ui.setup_wizard import SetupWizard
        wizard = SetupWizard(CONFIG_PATH)
        if wizard.exec() != SetupWizard.DialogCode.Accepted:
            sys.exit(0)
        config = cargar_config()

    # ── Abrir app principal ───────────────────
    from ui.main_window import AsmoRootApp
    window = AsmoRootApp()
    window.showMaximized()

    # ── Verificar actualizaciones en segundo plano ──
    from core.updater import Updater
    updater = Updater(window)
    updater.verificar()

    sys.exit(app.exec())