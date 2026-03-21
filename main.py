import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from config import generar_icono_profesional
from ui.main_window import AsmoRootApp

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    generar_icono_profesional()

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

    window = AsmoRootApp()
    window.showMaximized()
    sys.exit(app.exec())
