import os
import psutil
import win32com.client
from PyQt6.QtCore import QThread, pyqtSignal

# ─────────────────────────────────────────────
#  MONITOR DE ARCHIVO (hilo en segundo plano)
# ─────────────────────────────────────────────


class MonitorArchivo(QThread):
    archivo_cerrado = pyqtSignal()

    def __init__(self, ruta):
        super().__init__()
        self.ruta = ruta
        self.activo = True

    def run(self):
        import time
        time.sleep(3)
        while self.activo:
            time.sleep(2)
            try:
                if self.ruta.endswith(".docx"):
                    word = win32com.client.GetActiveObject("Word.Application")
                    nombres = [doc.FullName for doc in word.Documents]
                    if os.path.abspath(self.ruta) not in [os.path.abspath(n) for n in nombres]:
                        self.archivo_cerrado.emit()
                        break
                elif self.ruta.endswith(".pdf"):
                    nombre_sin_ext = os.path.splitext(os.path.basename(self.ruta))[0].lower()
                    abierto = False
                    for proc in psutil.process_iter(['name', 'cmdline']):
                        try:
                            if 'pdfgear' in proc.name().lower():
                                if nombre_sin_ext in " ".join(proc.cmdline()).lower():
                                    abierto = True
                                    break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    if not abierto:
                        self.archivo_cerrado.emit()
                        break
            except Exception:
                if self.ruta.endswith(".docx"):
                    self.archivo_cerrado.emit()
                    break

    def detener(self):
        self.activo = False
