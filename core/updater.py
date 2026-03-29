import os
import sys
import json
import threading
import urllib.request
import subprocess
from PyQt6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout, QLabel, QVBoxLayout, QProgressBar, QDialog
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from styles.helpers import t, label_style

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

            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'AsmoRoot-Updater')]
            urllib.request.install_opener(opener)
            
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
        self.version_actual = version_actual.strip("v")

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
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            version_nueva = data.get("tag_name", "0").strip("v")
            notas         = data.get("body", "Sin notas de versión.")
            url_release   = data.get("html_url", "")

            # Buscar .exe en assets (Detección flexible)
            url_exe = ""
            for asset in data.get("assets", []):
                asset_name = asset.get("name", "").lower()
                if asset_name.endswith(".exe"):
                    url_exe = asset.get("browser_download_url", "")
                    break

            if _es_mayor(version_nueva, self.version_actual):
                QTimer.singleShot(3000, lambda: self._mostrar_dialogo(
                    version_nueva, url_exe, url_release, notas))

        except Exception as e:
            print(f"Updater Debug: {e}")

    # ── DIÁLOGO MAC DARK ──────────────────────────
    def _mostrar_dialogo(self, version, url_exe, url_release, notas):
        dlg = QDialog(self.parent_app)
        dlg.setWindowTitle("Actualización disponible")
        dlg.setFixedSize(450, 320)
        
        # Estilo macOS v2.9
        bg = t('bg')
        brd = t('brd')
        acc = t('acc')
        
        dlg.setStyleSheet(f"""
            QDialog {{
                background: {bg};
                border: 1px solid {brd};
                border-radius: 14px;
            }}
        """)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(30, 25, 30, 25)
        lay.setSpacing(15)

        # Header
        head = QHBoxLayout()
        ic = QLabel("🚀")
        ic.setStyleSheet("font-size:32px;border:none;background:transparent;")
        lbl_titulo = QLabel(f"SGA v{version}")
        lbl_titulo.setStyleSheet(f"color:{t('tp')};font-size:18px;font-weight:700;border:none;")
        head.addWidget(ic)
        head.addWidget(lbl_titulo)
        head.addStretch()
        lay.addLayout(head)

        # Notas
        lbl_notas_tit = QLabel("NOVEDADES EN ESTA VERSIÓN:")
        lbl_notas_tit.setStyleSheet(label_style(10, "tm", "600"))
        lay.addWidget(lbl_notas_tit)

        notas_limitadas = notas[:200] + "..." if len(notas) > 200 else notas
        self.lbl_notas = QLabel(notas_limitadas)
        self.lbl_notas.setWordWrap(True)
        self.lbl_notas.setStyleSheet(label_style(11, "ts"))
        lay.addWidget(self.lbl_notas)

        # Barra de progreso (culta al inicio)
        self.progress = QProgressBar()
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background:rgba(255,255,255,10); border-radius:4px; border:none; }}
            QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {acc}, stop:1 #7B5FF7); border-radius:4px; }}
        """)
        self.progress.hide()
        lay.addWidget(self.progress)

        self.lbl_estado = QLabel("")
        self.lbl_estado.setStyleSheet(label_style(10, "acct"))
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.hide()
        lay.addWidget(self.lbl_estado)

        lay.addStretch()

        # Botones
        btns = QHBoxLayout()
        btns.setSpacing(10)

        btn_omitir = QPushButton("Ahora no")
        btn_omitir.setFixedHeight(34)
        btn_omitir.setStyleSheet(f"""
            QPushButton {{ background:rgba(255,255,255,10); color:{t('ts')};
                border:1px solid {t('brd')}; border-radius:8px; padding:0 20px; font-size:12px; }}
            QPushButton:hover {{ background:rgba(255,255,255,18); color:{t('tp')}; }}
        """)
        btn_omitir.clicked.connect(dlg.reject)

        if url_exe:
            self.btn_actualizar = QPushButton("Actualizar automáticamente")
            self.btn_actualizar.clicked.connect(lambda: self._descargar(url_exe, dlg))
        else:
            self.btn_actualizar = QPushButton("Ver en GitHub")
            self.btn_actualizar.clicked.connect(lambda: self._abrir_release(url_release, dlg))

        self.btn_actualizar.setFixedHeight(34)
        self.btn_actualizar.setStyleSheet(f"""
            QPushButton {{ background:{acc}; color:white; border:none;
                border-radius:8px; padding:0 24px; font-size:12px; font-weight:600; }}
            QPushButton:hover {{ background:#6EA3FA; }}
            QPushButton:disabled {{ background:rgba(255,255,255,5); color:rgba(255,255,255,40); }}
        """)

        btns.addWidget(btn_omitir)
        btns.addWidget(self.btn_actualizar)
        lay.addLayout(btns)

        self._dlg = dlg
        dlg.exec()

    # ── DESCARGA Y AUTO-REEMPLAZO ────────────────
    def _descargar(self, url_exe, dlg):
        if not getattr(sys, "frozen", False):
            QMessageBox.information(
                dlg, "Modo Desarrollo",
                "La auto-actualización requiere correr desde el .exe compilado.\n"
                "Usa el link de GitHub para bajarlo manualmente.")
            return

        self.btn_actualizar.setEnabled(False)
        self.btn_actualizar.setText("Descargando...")
        self.progress.show()
        self.lbl_estado.show()
        self.lbl_notas.hide() # Espacio para la barra

        exe_actual   = sys.executable
        destino_temp = exe_actual + ".new"

        self.hilo = DescargaHilo(url_exe, destino_temp)
        self.hilo.progreso.connect(self._on_progreso)
        self.hilo.completado.connect(lambda d: self._on_completado(d, exe_actual, dlg))
        self.hilo.error.connect(self._on_error)
        self.hilo.start()

    def _on_progreso(self, pct):
        self.progress.setValue(pct)
        self.lbl_estado.setText(f"Descargando nueva versión... {pct}%")

    def _on_completado(self, destino_temp, exe_actual, dlg):
        self.lbl_estado.setText("✅ Descarga completa. Reiniciando...")
        self.btn_actualizar.setText("Listo")
        
        # Nombre del proceso a esperar en el script
        exe_filename = os.path.basename(exe_actual)
        bat_path = os.path.join(os.path.dirname(exe_actual), "updater_asmoroot.bat")
        
        # SCRIPT INTELIGENTE: Espera al proceso, reemplaza, reinicia y se borra
        with open(bat_path, "w", encoding="ansi") as f:
            f.write(f"""@echo off
title Actualizando SGA...
echo Esperando a que el programa se cierre...
timeout /t 2 /nobreak >nul

:wait_loop
tasklist /FI "IMAGENAME eq {exe_filename}" 2>NUL | find /I /N "{exe_filename}">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

echo Reemplazando archivo ejecutable...
move /y "{destino_temp}" "{exe_actual}"

echo Iniciando nueva version...
start "" "{exe_actual}"

echo Limpiando...
del "%~f0"
""")

        # Ejecutar script de forma independiente
        os.startfile(bat_path)
        
        # Cerrar app de inmediato
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
        sys.exit(0)

    def _on_error(self, msg):
        self.lbl_estado.setText(f"❌ Error de descarga: {msg[:40]}")
        self.btn_actualizar.setEnabled(True)
        self.btn_actualizar.setText("Reintentar actualización")

    def _abrir_release(self, url_release, dlg):
        import webbrowser
        webbrowser.open(url_release)
        dlg.accept()