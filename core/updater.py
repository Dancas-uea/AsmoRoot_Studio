import os
import sys
import json
import threading
import urllib.request
from PyQt6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout, QLabel, QVBoxLayout, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal, Qt

# ─────────────────────────────────────────────
#  REPO  (no tocar)
# ─────────────────────────────────────────────
REPO_OWNER = "Dancas-uea"
REPO_NAME  = "AsmoRoot_Studio"
API_URL    = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"


# ─────────────────────────────────────────────
#  COMPARADOR DE VERSIONES (seguro: 1.9 < 1.10)
# ─────────────────────────────────────────────
def _es_mayor(nueva: str, actual: str) -> bool:
    try:
        n = [int(x) for x in nueva.strip("v").split(".")]
        a = [int(x) for x in actual.strip("v").split(".")]
        return n > a
    except Exception:
        return False


# ─────────────────────────────────────────────
#  HILO DE DESCARGA
# ─────────────────────────────────────────────
class DescargaHilo(QThread):
    progreso   = pyqtSignal(int)
    completado = pyqtSignal(str)
    error      = pyqtSignal(str)

    def __init__(self, url, destino):
        super().__init__()
        self.url     = url
        self.destino = destino

    def run(self):
        try:
            def _progress(block, block_size, total):
                if total > 0:
                    pct = int(block * block_size * 100 / total)
                    self.progreso.emit(min(pct, 100))

            urllib.request.urlretrieve(self.url, self.destino, _progress)
            self.completado.emit(self.destino)
        except Exception as e:
            self.error.emit(str(e))


# ─────────────────────────────────────────────
#  VERIFICADOR PRINCIPAL
# ─────────────────────────────────────────────
class Updater:
    def __init__(self, parent_app, version_actual):
        self.parent_app     = parent_app
        self.version_actual = version_actual.strip("v")  # acepta "v2.0.10" o "2.0.10"

    def verificar(self):
        """Verifica en segundo plano usando GitHub Releases API."""
        hilo = threading.Thread(target=self._check, daemon=True)
        hilo.start()

    def _check(self):
        try:
            req = urllib.request.Request(
                API_URL,
                headers={"User-Agent": "AsmoRoot-Updater"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            version_nueva = data.get("tag_name", "0").strip("v")
            notas         = data.get("body", "Sin notas de versión.")
            url_release   = data.get("html_url", "")

            # Buscar .exe entre los assets del release
            url_exe = ""
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    url_exe = asset.get("browser_download_url", "")
                    break

            if _es_mayor(version_nueva, self.version_actual):
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(2000, lambda: self._mostrar_dialogo(
                    version_nueva, url_exe, url_release, notas))

        except Exception as e:
            print(f"Updater: {e}")

    # ── DIÁLOGO ───────────────────────────────
    def _mostrar_dialogo(self, version, url_exe, url_release, notas):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
        from PyQt6.QtCore import Qt

        dlg = QDialog(self.parent_app)
        dlg.setWindowTitle("Nueva actualización disponible")
        dlg.setFixedSize(440, 280)
        dlg.setStyleSheet("""
            QDialog {
                background: #0d0d1c;
                border: 1px solid rgba(55,138,221,60);
                border-radius: 14px;
            }
        """)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        ic = QLabel("🚀")
        ic.setStyleSheet("font-size:32px;border:none;background:transparent;")
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_titulo = QLabel(f"AsmoRoot v{version} disponible")
        lbl_titulo.setStyleSheet(
            "color:rgba(255,255,255,230);font-size:16px;font-weight:700;"
            "border:none;background:transparent;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_notas = QLabel(notas[:180] + "…" if len(notas) > 180 else notas)
        lbl_notas.setStyleSheet(
            "color:rgba(255,255,255,115);font-size:11px;"
            "border:none;background:transparent;")
        lbl_notas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_notas.setWordWrap(True)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar { background:rgba(255,255,255,15); border-radius:3px; border:none; }
            QProgressBar::chunk { background:#378ADD; border-radius:3px; }
        """)
        self.progress.hide()

        self.lbl_estado = QLabel("")
        self.lbl_estado.setStyleSheet(
            "color:rgba(255,255,255,56);font-size:10px;border:none;background:transparent;")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.hide()

        btns = QHBoxLayout()

        btn_omitir = QPushButton("Más tarde")
        btn_omitir.setFixedHeight(36)
        btn_omitir.setStyleSheet("""
            QPushButton { background:rgba(255,255,255,10); color:rgba(255,255,255,115);
                border:1px solid rgba(255,255,255,23); border-radius:8px; padding:0 20px;
                font-size:12px; }
            QPushButton:hover { background:rgba(255,255,255,20); }
        """)
        btn_omitir.clicked.connect(dlg.reject)

        if url_exe:
            self.btn_actualizar = QPushButton("⬇  Actualizar ahora")
            self.btn_actualizar.clicked.connect(lambda: self._descargar(url_exe, dlg))
        else:
            self.btn_actualizar = QPushButton("🌐  Ver en GitHub")
            self.btn_actualizar.clicked.connect(lambda: self._abrir_release(url_release, dlg))

        self.btn_actualizar.setFixedHeight(36)
        self.btn_actualizar.setStyleSheet("""
            QPushButton { background:#378ADD; color:white; border:none;
                border-radius:8px; padding:0 20px; font-size:12px; font-weight:600; }
            QPushButton:hover { border:1px solid rgba(255,255,255,50); }
            QPushButton:disabled { opacity:0.5; }
        """)

        btns.addWidget(btn_omitir)
        btns.addWidget(self.btn_actualizar)

        lay.addWidget(ic)
        lay.addWidget(lbl_titulo)
        lay.addWidget(lbl_notas)
        lay.addWidget(self.progress)
        lay.addWidget(self.lbl_estado)
        lay.addStretch()
        lay.addLayout(btns)

        self._dlg = dlg
        dlg.exec()

    # ── DESCARGA DIRECTA ──────────────────────
    def _descargar(self, url_exe, dlg):
        if not getattr(sys, "frozen", False):
            QMessageBox.information(
                self._dlg, "Modo desarrollo",
                "La descarga automática solo funciona en el .exe compilado.\n"
                "Descarga la nueva versión desde GitHub manualmente.")
            return

        self.btn_actualizar.setEnabled(False)
        self.btn_actualizar.setText("Descargando...")
        self.progress.show()
        self.lbl_estado.show()
        self.lbl_estado.setText("Conectando...")

        exe_actual   = sys.executable
        destino_temp = exe_actual + ".new"

        self.hilo = DescargaHilo(url_exe, destino_temp)
        self.hilo.progreso.connect(self._on_progreso)
        self.hilo.completado.connect(lambda d: self._on_completado(d, exe_actual, dlg))
        self.hilo.error.connect(self._on_error)
        self.hilo.start()

    def _abrir_release(self, url_release, dlg):
        import webbrowser
        webbrowser.open(url_release)
        dlg.accept()

    # ── CALLBACKS DESCARGA ────────────────────
    def _on_progreso(self, pct):
        self.progress.setValue(pct)
        self.lbl_estado.setText(f"Descargando... {pct}%")

    def _on_completado(self, destino_temp, exe_actual, dlg):
        self.lbl_estado.setText("✅ Descarga completa — reinicia la app")
        self.btn_actualizar.setText("✅ Listo")

        bat = os.path.join(os.path.dirname(exe_actual), "_update.bat")
        with open(bat, "w") as f:
            f.write(f"""@echo off
timeout /t 2 /nobreak >nul
move /y "{destino_temp}" "{exe_actual}"
start "" "{exe_actual}"
del "%~f0"
""")
        QMessageBox.information(
            self._dlg,
            "Actualización lista",
            "La actualización se instalará al cerrar el programa.\n"
            "Cierra AsmoRoot y vuelve a abrirlo.")
        dlg.accept()

    def _on_error(self, msg):
        self.lbl_estado.setText(f"❌ Error: {msg[:50]}")
        self.btn_actualizar.setEnabled(True)
        self.btn_actualizar.setText("⬇  Reintentar")