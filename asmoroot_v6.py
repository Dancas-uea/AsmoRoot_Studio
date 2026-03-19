import sys
import os
import json
import shutil
from datetime import datetime

import psutil
from google import genai

from PIL import Image

from PyQt6.QtWidgets import (
    QApplication, QDialog, QMainWindow, QTextEdit, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QFrame,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QInputDialog,
    QScrollArea,QSizeGrip, QSpacerItem, QFileDialog, QSizePolicy, QMenu,
    QGraphicsDropShadowEffect, QStackedWidget
)
from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage, QWebEngineDownloadRequest)
from PyQt6.QtCore import Qt, QUrl, QSize, QPropertyAnimation, QPoint, QEasingCurve, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QDrag
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QMimeData
import win32com.client

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
PATH_RAIZ     = r"C:\Users\AsmoRoot\Desktop\Universidad Estatal Amazonica"
PATH_LOGO     = os.path.join(PATH_RAIZ, "Logo", "logo.png")
PATH_ICO      = os.path.join(PATH_RAIZ, "Logo", "logo.ico")
ARCHIVO_CONFIG = os.path.join(PATH_RAIZ, "config_carrera.json")

def generar_icono_profesional():
    try:
        if os.path.exists(PATH_LOGO):
            img = Image.open(PATH_LOGO)
            img.save(PATH_ICO, format='ICO', sizes=[(256,256),(128,128),(64,64),(32,32)])
    except Exception as e:
        print(f"Icono error: {e}")

generar_icono_profesional()

# ─────────────────────────────────────────────
#  PALETA macOS dark/light  (CSS variables → QSS)
# ─────────────────────────────────────────────
THEME = {
    "dark": {
        "bg":       "#08081a",
        "win":      "rgba(13,13,28,210)",
        "sb":       "#0b0b18",
        "bar":      "#10101e",
        "card":     "rgba(255,255,255,10)",
        "cardh":    "rgba(255,255,255,20)",
        "inp":      "rgba(255,255,255,13)",
        "brd":      "rgba(255,255,255,23)",
        "acc":      "#378ADD",
        "accd":     "rgba(55,138,221,40)",
        "acct":     "#85B7EB",
        "tp":       "rgba(255,255,255,230)",
        "ts":       "rgba(255,255,255,115)",
        "tm":       "rgba(255,255,255,56)",
        "grn":      "#28c840",
        "red":      "#ff5f57",
        "yel":      "#febc2e",
        "shadow":   "0 32px 80px rgba(0,0,0,190)",
        "browserbg":"#0d0d1a",
    },
    "light": {
        "bg":       "#b8c4d8",
        "win":      "rgba(230,235,252,199)",
        "sb":       "#d7def5",
        "bar":      "#d0d8f0",
        "card":     "rgba(255,255,255,115)",
        "cardh":    "rgba(255,255,255,178)",
        "inp":      "rgba(255,255,255,140)",
        "brd":      "rgba(0,0,0,20)",
        "acc":      "#185FA5",
        "accd":     "rgba(24,95,165,30)",
        "acct":     "#185FA5",
        "tp":       "rgba(0,0,0,224)",
        "ts":       "rgba(0,0,0,128)",
        "tm":       "rgba(0,0,0,76)",
        "grn":      "#1a8c30",
        "red":      "#d93025",
        "yel":      "#c8890a",
        "shadow":   "0 32px 80px rgba(0,0,0,51)",
        "browserbg":"#f5f6fa",
    }
}

# ─────────────────────────────────────────────
#  HELPERS DE ESTILO
# ─────────────────────────────────────────────
def t(key):
    """Devuelve el color del tema activo por clave."""
    return AsmoRootApp.CURRENT_THEME.get(key, "#ffffff")


def card_style(radius=10, border_key="brd", bg_key="card"):
    return f"""
        background: {t(bg_key)};
        border: 1px solid {t(border_key)};
        border-radius: {radius}px;
    """


def btn_style(bg="#378ADD", color="white", radius=8, padding="10px 18px"):
    return f"""
        QPushButton {{
            background: {bg};
            color: {color};
            border: none;
            border-radius: {radius}px;
            padding: {padding};
            font-weight: 600;
            font-size: 12px;
            font-family: Inter, -apple-system, sans-serif;
        }}
        QPushButton:hover {{ opacity: 0.85; background: {bg}; border: 1px solid rgba(255,255,255,40); }}
        QPushButton:disabled {{ opacity: 0.35; }}
    """


def input_style():
    return f"""
        QLineEdit, QComboBox {{
            background: {t('inp')};
            color: {t('tp')};
            border: 1px solid {t('brd')};
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
            font-family: Inter, -apple-system, sans-serif;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {t('accd')};
        }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox::down-arrow {{ image: none; width: 0; }}
    """


def label_style(size=11, color_key="ts", weight="normal"):
    return f"color: {t(color_key)}; font-size: {size}px; font-weight: {weight}; font-family: Inter, -apple-system, sans-serif; border: none;"


# ─────────────────────────────────────────────
#  MONITOR DE ARCHIVO (hilo)
# ─────────────────────────────────────────────


class MonitorArchivo(QThread):
    archivo_cerrado = pyqtSignal()

    def __init__(self, ruta):
        super().__init__()
        self.ruta = ruta
        self.activo = True

    def run(self):
        import time
        nombre_archivo = os.path.basename(self.ruta).lower()
        time.sleep(3)
        while self.activo:
            time.sleep(2)
            try:
                if self.ruta.endswith(".docx"):
                    word = win32com.client.GetActiveObject("Word.Application")
                    nombres = [doc.FullName for doc in word.Documents]
                    if os.path.abspath(self.ruta) not in [os.path.abspath(n) for n in nombres]:
                        self.archivo_cerrado.emit(); break
                elif self.ruta.endswith(".pdf"):
                    nombre_sin_ext = os.path.splitext(os.path.basename(self.ruta))[0].lower()
                    abierto = False
                    for proc in psutil.process_iter(['name', 'cmdline']):
                        try:
                            if 'pdfgear' in proc.name().lower():
                                if nombre_sin_ext in " ".join(proc.cmdline()).lower():
                                    abierto = True; break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    if not abierto:
                        self.archivo_cerrado.emit(); break
            except:
                if self.ruta.endswith(".docx"):
                    self.archivo_cerrado.emit(); break

    def detener(self):
        self.activo = False


# ─────────────────────────────────────────────
#  PESTAÑA DE ARCHIVO ABIERTO  (estilo macOS pill)
# ─────────────────────────────────────────────
class PestanaArchivo(QFrame):
    def __init__(self, ruta, parent_app):
        super().__init__()
        self.ruta = ruta
        self.parent_app = parent_app
        self.nombre = os.path.basename(ruta)
        self.es_pdf = ruta.endswith(".pdf")

        self.setFixedHeight(42)
        self.setStyleSheet(f"""
            PestanaArchivo {{
                background: {t('card')};
                border: 1px solid {t('accd')};
                border-radius: 10px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 0, 8, 0)
        lay.setSpacing(6)

        # Icono tipo badge
        badge = QLabel("P" if self.es_pdf else "W")
        badge.setFixedSize(26, 26)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = "rgba(163,45,45,90)" if self.es_pdf else "rgba(24,95,165,90)"
        txt   = "#F09595" if self.es_pdf else "#85B7EB"
        badge.setStyleSheet(f"background:{color};color:{txt};border-radius:6px;font-weight:700;font-size:10px;border:none;")

        # Info
        info = QVBoxLayout()
        info.setSpacing(0)
        nlab = QLabel(self.nombre[:28] + "…" if len(self.nombre) > 28 else self.nombre)
        nlab.setStyleSheet(label_style(10, "tp", "600"))
        tlab = QLabel("PDF · abierto" if self.es_pdf else "Word · abierto")
        tlab.setStyleSheet(label_style(9, "acct"))
        info.addWidget(nlab)
        info.addWidget(tlab)

        # Botones
        btn_r = QPushButton("▶")
        btn_r.setFixedSize(20, 20)
        btn_r.setStyleSheet(f"background:transparent;color:{t('acc')};border:none;font-size:11px;")
        btn_r.clicked.connect(self.reabrir)

        btn_c = QPushButton("✕")
        btn_c.setFixedSize(16, 16)
        btn_c.setStyleSheet(f"background:transparent;color:{t('tm')};border:none;font-size:10px;")
        btn_c.clicked.connect(self.cerrar)

        lay.addWidget(badge)
        lay.addLayout(info)
        lay.addStretch()
        lay.addWidget(btn_r)
        lay.addWidget(btn_c)

    def reabrir(self):
        os.startfile(self.ruta)

    def cerrar(self):
        self.parent_app.cerrar_pestana_archivo(self)


# ─────────────────────────────────────────────
#  NAVEGADOR (pestaña)
# ─────────────────────────────────────────────
class MiPaginaWeb(QWebEnginePage):
    def createWindow(self, _type):
        self._url_anterior = self.url()
        self.loadFinished.connect(self._volver)
        return self

    def _volver(self, ok):
        self.loadFinished.disconnect(self._volver)
        if hasattr(self, '_url_anterior'):
            self.setUrl(self._url_anterior)


class PestañaNavegador(QWidget):
    def __init__(self, perfil, parent=None, url="https://www.google.com"):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.web_page = MiPaginaWeb(perfil, parent)
        self.browser = QWebEngineView()
        self.browser.setPage(self.web_page)
        self.browser.settings().setAttribute(self.browser.settings().WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.browser.settings().setAttribute(self.browser.settings().WebAttribute.LocalStorageEnabled, True)
        self.browser.setUrl(QUrl(url))
        lay.addWidget(self.browser)


# ─────────────────────────────────────────────
#  PANEL DE DESCARGAS  (sidebar right)
# ─────────────────────────────────────────────
class PanelDescargas(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.setFixedWidth(290)
        self.setStyleSheet(f"""
            PanelDescargas {{
                background: {t('sb')};
                border-left: 1px solid {t('brd')};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setFixedHeight(44)
        hdr.setStyleSheet(f"background:{t('bar')};border-bottom:1px solid {t('brd')};")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(12, 0, 12, 0)
        ttl = QLabel("⬇ Descargas")
        ttl.setStyleSheet(label_style(12, "tp", "600"))
        btn_ver = QPushButton("Ver todas")
        btn_ver.setFixedHeight(26)
        btn_ver.setStyleSheet(btn_style(t('accd'), t('acct'), 6, "4px 10px"))
        btn_ver.clicked.connect(lambda: self.parent_app.abrir_explorador_descargas())
        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(24, 24)
        btn_cerrar.setStyleSheet(f"background:transparent;color:{t('tm')};border:none;font-size:13px;")
        btn_cerrar.clicked.connect(lambda: self.parent_app.cerrar_panel_descargas())
        hdr_lay.addWidget(ttl)
        hdr_lay.addStretch()
        hdr_lay.addWidget(btn_ver)
        hdr_lay.addWidget(btn_cerrar)
        lay.addWidget(hdr)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border:none;background:transparent;QScrollBar:vertical{width:3px;background:transparent;}QScrollBar::handle:vertical{background:rgba(255,255,255,40);border-radius:2px;}")
        self.contenedor = QWidget()
        self.contenedor.setStyleSheet("background:transparent;")
        self.lista_lay = QVBoxLayout(self.contenedor)
        self.lista_lay.setContentsMargins(10, 10, 10, 10)
        self.lista_lay.setSpacing(6)
        self.lista_lay.addStretch()
        self.scroll.setWidget(self.contenedor)
        lay.addWidget(self.scroll)

        self.cargar_archivos()

    def cargar_archivos(self):
        while self.lista_lay.count() > 1:
            item = self.lista_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(carpeta):
            return
        archivos = sorted(
            [f for f in os.listdir(carpeta) if f.endswith((".docx", ".pdf"))],
            key=lambda x: os.path.getmtime(os.path.join(carpeta, x)),
            reverse=True
        )[:15]

        for arc in archivos:
            ruta = os.path.join(carpeta, arc)
            kb = os.path.getsize(ruta) // 1024
            es_docx = arc.endswith(".docx")

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background:{t('card')};
                    border:1px solid {t('brd')};
                    border-radius:10px;
                }}
                QFrame:hover {{ border:1px solid {t('bacc') if 'bacc' in t.__code__.co_consts else t('acc')}; }}
            """)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(10, 8, 10, 8)
            cl.setSpacing(8)

            badge = QLabel("W" if es_docx else "P")
            badge.setFixedSize(34, 34)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bg = "rgba(24,95,165,80)" if es_docx else "rgba(163,45,45,80)"
            fg = "#85B7EB" if es_docx else "#F09595"
            badge.setStyleSheet(f"background:{bg};color:{fg};border-radius:8px;font-weight:700;font-size:11px;border:none;")

            info = QVBoxLayout()
            info.setSpacing(1)
            n = QLabel(arc[:26] + "…" if len(arc) > 26 else arc)
            n.setStyleSheet(label_style(10, "tp", "600"))
            s = QLabel(f"{kb} KB")
            s.setStyleSheet(label_style(9, "tm"))
            info.addWidget(n)
            info.addWidget(s)

            btn_open = QPushButton("↗")
            btn_open.setFixedSize(26, 26)
            btn_open.setStyleSheet(f"background:transparent;color:{t('acc')};border:none;font-size:14px;")
            btn_open.clicked.connect(lambda _, r=ruta: os.startfile(r))

            cl.addWidget(badge)
            cl.addLayout(info)
            cl.addStretch()
            cl.addWidget(btn_open)

            self.lista_lay.insertWidget(self.lista_lay.count() - 1, card)


# ─────────────────────────────────────────────
#  EXPLORADOR DE DESCARGAS (diálogo)
# ─────────────────────────────────────────────
class ExploradorDescargas(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
        self.setWindowTitle("Explorador de Descargas")
        self.setFixedSize(780, 520)
        self.setStyleSheet(f"background:{t('win')};color:{t('tp')};font-family:Inter,-apple-system,sans-serif;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        ttl = QLabel("⬇  Explorador de Descargas")
        ttl.setStyleSheet(label_style(16, "acc", "600"))
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar archivo…")
        self.buscador.setFixedWidth(220)
        self.buscador.setStyleSheet(input_style())
        self.buscador.textChanged.connect(self.cargar_archivos)
        hdr.addWidget(ttl); hdr.addStretch(); hdr.addWidget(self.buscador)
        lay.addLayout(hdr)

        # Tabla
        self.tabla = QTreeWidget()
        self.tabla.setHeaderLabels(["Nombre", "Tipo", "Tamaño", "Fecha"])
        self.tabla.setColumnWidth(0, 340); self.tabla.setColumnWidth(1, 60)
        self.tabla.setColumnWidth(2, 80); self.tabla.setColumnWidth(3, 160)
        self.tabla.setStyleSheet(f"""
            QTreeWidget {{
                background:{t('card')};
                color:{t('tp')};
                border:1px solid {t('brd')};
                border-radius:10px;
                outline: none;
                font-size:12px;
            }}
            QTreeWidget::item:hover {{ background:{t('cardh')}; }}
            QTreeWidget::item:selected {{ background:{t('accd')};color:{t('acct')}; }}
            QHeaderView::section {{
                background:{t('bar')};
                color:{t('ts')};
                border:none;
                padding:6px;
                font-weight:600;
                font-size:11px;
            }}
        """)
        self.tabla.itemDoubleClicked.connect(self.abrir_archivo)
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.menu_contextual)
        lay.addWidget(self.tabla)

        # Botones
        btns = QHBoxLayout()
        for txt, color, fn in [
            ("↗ Abrir",            "#238636", self.abrir_archivo),
            ("📁 Mover al semestre","#1F6FEB", self.mover_archivo),
            ("✏️ Renombrar",       "#E1AD01", self.renombrar_archivo),
            ("🗑️ Eliminar",        "#C0392B", self.eliminar_archivo),
        ]:
            b = QPushButton(txt)
            b.setStyleSheet(btn_style(color, "white", 8, "9px 16px"))
            b.clicked.connect(fn)
            btns.addWidget(b)
        lay.addLayout(btns)
        self.cargar_archivos()

    def cargar_archivos(self):
        self.tabla.clear()
        query = self.buscador.text().lower() if hasattr(self, 'buscador') else ""
        if not os.path.exists(self.carpeta): return
        archivos = sorted(
            [f for f in os.listdir(self.carpeta) if f.endswith((".docx", ".pdf")) and query in f.lower()],
            key=lambda x: os.path.getmtime(os.path.join(self.carpeta, x)), reverse=True
        )
        for arc in archivos:
            ruta = os.path.join(self.carpeta, arc)
            item = QTreeWidgetItem([
                arc,
                "DOCX" if arc.endswith(".docx") else "PDF",
                f"{os.path.getsize(ruta)//1024} KB",
                datetime.fromtimestamp(os.path.getmtime(ruta)).strftime('%d/%m/%Y %H:%M')
            ])
            self.tabla.addTopLevelItem(item)

    def _item_actual(self):
        item = self.tabla.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecciona un archivo primero.")
            return None, None
        return item.text(0), os.path.join(self.carpeta, item.text(0))

    def abrir_archivo(self):
        _, ruta = self._item_actual()
        if ruta: os.startfile(ruta)

    def eliminar_archivo(self):
        nombre, ruta = self._item_actual()
        if not ruta: return
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar {nombre}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            os.remove(ruta)
            self.cargar_archivos()
            self.parent_app.actualizar_arbol()

    def renombrar_archivo(self):
        nombre, ruta = self._item_actual()
        if not ruta: return
        nuevo, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=nombre)
        if ok and nuevo:
            if not nuevo.endswith((".docx", ".pdf")):
                nuevo += ".docx" if nombre.endswith(".docx") else ".pdf"
            os.rename(ruta, os.path.join(self.carpeta, nuevo))
            self.cargar_archivos()
            self.parent_app.actualizar_arbol()

    def mover_archivo(self):
        nombre, ruta = self._item_actual()
        if not ruta: return
        semestres = self.parent_app.obtener_semestres_raiz()
        sem, ok1 = QInputDialog.getItem(self, "Mover", "Semestre:", semestres, 0, False)
        if not ok1: return
        materias = [m for m in os.listdir(os.path.join(PATH_RAIZ, sem))
                    if os.path.isdir(os.path.join(PATH_RAIZ, sem, m)) and m != "Plantillas"]
        mat, ok2 = QInputDialog.getItem(self, "Mover", "Materia:", materias, 0, False)
        if not ok2: return
        shutil.move(ruta, os.path.join(PATH_RAIZ, sem, mat, nombre))
        self.cargar_archivos()
        self.parent_app.actualizar_arbol()
        QMessageBox.information(self, "Éxito", f"Movido → {sem} / {mat}")

    def menu_contextual(self, pos):
        menu = QMenu()
        menu.setStyleSheet(f"QMenu{{background:{t('sb')};color:{t('tp')};border:1px solid {t('brd')};border-radius:8px;font-size:12px;}} QMenu::item:selected{{background:{t('accd')};color:{t('acct')}}}")
        menu.addAction("↗ Abrir").triggered.connect(self.abrir_archivo)
        menu.addAction("📁 Mover").triggered.connect(self.mover_archivo)
        menu.addAction("✏️ Renombrar").triggered.connect(self.renombrar_archivo)
        menu.addAction("🗑️ Eliminar").triggered.connect(self.eliminar_archivo)
        menu.exec(self.tabla.viewport().mapToGlobal(pos))


# ─────────────────────────────────────────────
#  NOTIFICACIÓN TOAST (macOS-style)
# ─────────────────────────────────────────────
class Notificacion(QFrame):
    def __init__(self, tipo, titulo, mensaje, parent):
        super().__init__(parent)
        colores = {
            "gn": ("#28c840", "rgba(40,200,64,25)"),
            "bl": ("#378ADD", "rgba(55,138,221,25)"),
            "or": ("#febc2e", "rgba(254,188,46,25)"),
            "rd": ("#ff5f57", "rgba(255,95,87,25)"),
        }
        acc, bg = colores.get(tipo, ("#378ADD", "rgba(55,138,221,25)"))

        self.setFixedWidth(300)
        self.setStyleSheet(f"""
            QFrame {{
                background: {t('nbg') if 'nbg' in t.__code__.co_consts else t('sb')};
                border: 1px solid {acc.replace('#','rgba(') if False else acc};
                border-radius: 12px;
            }}
        """)
        self.setStyleSheet(f"QFrame{{background:{t('sb')};border:1px solid {acc};border-left:3px solid {acc};border-radius:12px;}}")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet(f"color:{acc};font-size:10px;border:none;")
        dot.setFixedWidth(12)

        info = QVBoxLayout()
        info.setSpacing(2)
        tit = QLabel(titulo)
        tit.setStyleSheet(label_style(12, "tp", "600"))
        msg = QLabel(mensaje)
        msg.setStyleSheet(label_style(11, "ts"))
        info.addWidget(tit)
        info.addWidget(msg)

        btn_x = QPushButton("✕")
        btn_x.setFixedSize(18, 18)
        btn_x.setStyleSheet(f"background:transparent;color:{t('tm')};border:none;font-size:10px;")
        btn_x.clicked.connect(self.cerrar)

        lay.addWidget(dot)
        lay.addLayout(info)
        lay.addStretch()
        lay.addWidget(btn_x)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.cerrar)
        self._timer.start(4000)

        # Animación entrada
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(280)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def cerrar(self):
        self._timer.stop()
        if self.parent():
            self.parent().remover_notif(self)


# ─────────────────────────────────────────────
#  ÁREA DE NOTIFICACIONES
# ─────────────────────────────────────────────
class AreaNotificaciones(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.notifs = []
        self.setFixedWidth(310)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def agregar(self, tipo, titulo, mensaje):
        n = Notificacion(tipo, titulo, mensaje, self)
        self.notifs.append(n)
        self._reposicionar()
        n.show()

    def remover_notif(self, n):
        if n in self.notifs:
            self.notifs.remove(n)
            n.hide()
            n.deleteLater()
            self._reposicionar()

    def _reposicionar(self):
        y = 0
        for n in self.notifs:
            n.move(0, y)
            n.resize(300, n.sizeHint().height() + 10)
            y += n.height() + 6
        self.resize(310, max(y, 10))


# ─────────────────────────────────────────────
#  TITLEBAR macOS (dots + title + buttons)
# ─────────────────────────────────────────────
class TitleBar(QFrame):
    def __init__(self, parent, titulo="AsmoRoot v6"):
        super().__init__(parent)
        self.parent_win = parent
        self.setFixedHeight(44)
        self.setStyleSheet(f"background:{t('bar')};border-bottom:1px solid {t('brd')};")
        self._drag_pos = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(8)

        # Botón tema (izquierda, antes de los dots)
        self.btn_tema = QPushButton("☀️")
        self.btn_tema.setFixedSize(28, 28)
        self.btn_tema.setStyleSheet(
            f"background:{t('card')};border:1px solid {t('brd')};border-radius:7px;font-size:13px;")
        self.btn_tema.clicked.connect(parent.toggle_tema)
        lay.addWidget(self.btn_tema)

        lay.addStretch()

        # Título central
        ttl = QLabel(titulo)
        ttl.setStyleSheet(label_style(12, "ts", "500"))
        lay.addWidget(ttl)

        lay.addStretch()

        # Dots macOS (derecha)
        dots_w = QWidget()
        dots_lay = QHBoxLayout(dots_w)
        dots_lay.setContentsMargins(0, 0, 0, 0)
        dots_lay.setSpacing(7)
        for color, fn in [
            ("#febc2e", parent.showMinimized),
            ("#28c840", parent._toggle_maximized),
            ("#ff5f57", parent.close),
        ]:
            d = QPushButton()
            d.setFixedSize(13, 13)
            d.setStyleSheet(f"background:{color};border-radius:6px;border:none;")
            d.clicked.connect(fn)
            dots_lay.addWidget(d)

        lay.addWidget(dots_w)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.parent_win.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.parent_win.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None


# ─────────────────────────────────────────────
#  APP PRINCIPAL
# ─────────────────────────────────────────────
class AsmoRootApp(QMainWindow):
    CURRENT_THEME = THEME["dark"]

    def __init__(self):
        super().__init__()

        # Estado
        self.archivo_docx_sesion = ""
        self.archivo_pdf_sesion = ""
        self.version_sistema = "v6.0"
        self.tema_actual = "dark"
        self.pestanas = []
        self.contador_descargas = 0

        self.setWindowTitle("AsmoRoot")
        self.resize(1380, 960)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if os.path.exists(PATH_ICO):
            self.setWindowIcon(QIcon(PATH_ICO))

        self.cargar_config()
        self._build_ui()
        self.actualizar_arbol()
        self.cargar_ultima_sesion()
        self._aplicar_tema()

    # ── Config ────────────────────────────────
    def cargar_config(self):
        if not os.path.exists(PATH_RAIZ): os.makedirs(PATH_RAIZ, exist_ok=True)
        if os.path.exists(ARCHIVO_CONFIG):
            with open(ARCHIVO_CONFIG, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {"semestres": {}, "ultimo_semestre": "", "ultima_materia": ""}
            self.guardar_config()

    def guardar_config(self):
        with open(ARCHIVO_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=4)

    # ── Build UI ──────────────────────────────
    def _build_ui(self):
        # Contenedor raíz (para fondo semitransparente con radio)
        self.root = QFrame(self)
        self.root.setObjectName("root_frame")
        self.setCentralWidget(self.root)
        root_lay = QVBoxLayout(self.root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ── Titlebar ──
        self.titlebar = TitleBar(self)
        root_lay.addWidget(self.titlebar)

        # ── Main tabs (UEA | Panel) ──
        self.mtabs_bar = QFrame()
        self.mtabs_bar.setFixedHeight(46)
        mtabs_lay = QHBoxLayout(self.mtabs_bar)
        mtabs_lay.setContentsMargins(14, 7, 14, 7)
        mtabs_lay.setSpacing(4)

        self.btn_tab_uea   = self._make_mtab("🌐  UEA", "uea")
        self.btn_tab_panel = self._make_mtab("📚  Gestión", "panel")
        mtabs_lay.addWidget(self.btn_tab_uea)
        mtabs_lay.addWidget(self.btn_tab_panel)
        mtabs_lay.addStretch()
        root_lay.addWidget(self.mtabs_bar)

        # ── Body (sidebar + content) ──
        self.body_widget = QWidget()
        self.body_lay = QHBoxLayout(self.body_widget)
        self.body_lay.setContentsMargins(0, 0, 0, 0)
        self.body_lay.setSpacing(0)
        root_lay.addWidget(self.body_widget, 1)

        # ── Sidebar ──
        self._build_sidebar()

        # ── Stacked content ──
        self.stack = QStackedWidget()
        self.body_lay.addWidget(self.stack, 1)

        # ── Panel UEA ──
        self._build_panel_uea()

        # ── Panel Gestión ──
        self._build_panel_gestion()

        # ── Panel Descargas (right) ──
        self.panel_descargas = PanelDescargas(self)
        self.panel_descargas.hide()
        self.body_lay.addWidget(self.panel_descargas)

        # ── Status bar ──
        self._build_statusbar()
        root_lay.addWidget(self.statusbar_frame)


        # ── Área de notificaciones ──
        self.notif_area = AreaNotificaciones(self.root)
        self.notif_area.move(self.root.width() - 320, 60)
        self.notif_area.raise_()


        # Activar tab UEA por defecto
        self._switch_main("uea")

    def _make_mtab(self, texto, tab_id):
        btn = QPushButton(texto)
        btn.setFixedHeight(30)
        btn.setCheckable(True)
        btn.setObjectName(f"mtab_{tab_id}")
        btn.setStyleSheet(self._mtab_style(False))
        btn.clicked.connect(lambda: self._switch_main(tab_id))
        return btn

    def _mtab_style(self, activo):
        if activo:
            return f"""QPushButton{{background:{t('accd')};color:{t('acct')};border:1px solid rgba(55,138,221,80);border-radius:8px;padding:0 14px;font-size:12px;font-weight:500;font-family:Inter,-apple-system,sans-serif;}}"""
        return f"""QPushButton{{background:transparent;color:{t('tm')};border:1px solid transparent;border-radius:8px;padding:0 14px;font-size:12px;font-family:Inter,-apple-system,sans-serif;}} QPushButton:hover{{background:{t('cardh')};color:{t('tp')};}}"""

    def _switch_main(self, tab_id):
        map_ = {"uea": (self.btn_tab_uea, 0), "panel": (self.btn_tab_panel, 1)}
        for k, (btn, idx) in map_.items():
            activo = (k == tab_id)
            btn.setStyleSheet(self._mtab_style(activo))
        self.stack.setCurrentIndex(map_[tab_id][1])

    # ── SIDEBAR ───────────────────────────────
    def _build_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(230)
        self.sidebar_lay = QVBoxLayout(self.sidebar)
        self.sidebar_lay.setContentsMargins(0, 0, 0, 0)
        self.sidebar_lay.setSpacing(0)
        self.sidebar_visible = True

        # ─ Logo / app info ─
        logo_frame = QFrame()
        logo_frame.setFixedHeight(110)
        logo_frame.setStyleSheet(f"border-bottom:1px solid {t('brd')};background:transparent;")
        logo_lay = QVBoxLayout(logo_frame)
        logo_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo_label = QLabel()
        if os.path.exists(PATH_LOGO):
            pix = QPixmap(PATH_LOGO).scaled(52, 52, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText("🎓")
            self.logo_label.setStyleSheet("font-size:30px;")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_name = QLabel("AsmoRoot")
        lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_name.setStyleSheet(label_style(11, "tp", "600"))

        lbl_ver = QLabel(self.version_sistema)
        lbl_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ver.setStyleSheet(label_style(9, "acct"))

        logo_lay.addWidget(self.logo_label)
        logo_lay.addWidget(lbl_name)
        logo_lay.addWidget(lbl_ver)
        self.sidebar_lay.addWidget(logo_frame)

        # ─ Tabs árbol / descargas ─
        sb_tabs = QFrame()
        sb_tabs.setFixedHeight(34)
        sb_tabs.setStyleSheet(f"border-bottom:1px solid {t('brd')};background:transparent;")
        st_lay = QHBoxLayout(sb_tabs)
        st_lay.setContentsMargins(0, 0, 0, 0)
        st_lay.setSpacing(0)

        self.sbt_tree = QPushButton("Árbol")
        self.sbt_dl   = QPushButton("Descargas")
        for b in [self.sbt_tree, self.sbt_dl]:
            b.setStyleSheet(self._sbt_style(False))
            st_lay.addWidget(b)
        self.sbt_tree.clicked.connect(lambda: self._sb_mode("tree"))
        self.sbt_dl.clicked.connect(lambda: self._sb_mode("dl"))
        self.sidebar_lay.addWidget(sb_tabs)

        # ─ Scroll árbol ─
        self.sb_tree_frame = QWidget()
        sb_tree_lay = QVBoxLayout(self.sb_tree_frame)
        sb_tree_lay.setContentsMargins(0, 0, 0, 0)
        sb_tree_lay.setSpacing(0)

        # Refresh
        btn_refresh = QPushButton("↻  Actualizar sistema")
        btn_refresh.setFixedHeight(30)
        btn_refresh.setStyleSheet(f"background:{t('card')};color:{t('ts')};border:none;border-bottom:1px solid {t('brd')};font-size:11px;font-family:Inter,-apple-system,sans-serif;")
        btn_refresh.clicked.connect(self.actualizar_arbol)
        sb_tree_lay.addWidget(btn_refresh)

        # Buscador
        self.search_ent = QLineEdit()
        self.search_ent.setPlaceholderText("🔍  Filtrar archivos…")
        self.search_ent.setFixedHeight(32)
        self.search_ent.setStyleSheet(f"""
            QLineEdit{{background:{t('inp')};color:{t('tp')};border:none;border-bottom:1px solid {t('brd')};padding:0 12px;font-size:11px;font-family:Inter,-apple-system,sans-serif;}}
        """)
        self.search_ent.textChanged.connect(self.actualizar_arbol)
        sb_tree_lay.addWidget(self.search_ent)

        # Árbol
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background:transparent;
                border:none;
                color:{t('tp')};
                font-size:11.5px;
                font-family:Inter,-apple-system,sans-serif;
                outline:none;
            }}
            QTreeWidget::item {{
                padding:4px 8px;
                border-radius:7px;
            }}
            QTreeWidget::item:hover {{
                background:{t('cardh')};
            }}
            QTreeWidget::item:selected {{
                background:{t('accd')};
                color:{t('acct')};
            }}
            QScrollBar:vertical{{background:transparent;width:4px;}}
            QScrollBar::handle:vertical{{background:rgba(255,255,255,40);border-radius:2px;}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
        """)
        self.tree.itemClicked.connect(self.seleccionar_desde_arbol)
        self.tree.itemDoubleClicked.connect(self.abrir_archivo_desde_arbol)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)
        self.tree.startDrag = self.iniciar_arrastre
        sb_tree_lay.addWidget(self.tree, 1)

        # Archivos abiertos
        self.zona_archivos_label = QLabel("ARCHIVOS ABIERTOS")
        self.zona_archivos_label.setStyleSheet(f"color:{t('tm')};font-size:9px;letter-spacing:1px;padding:6px 12px 2px;border:none;font-family:Inter,-apple-system,sans-serif;")
        self.zona_archivos_label.hide()
        sb_tree_lay.addWidget(self.zona_archivos_label)

        self.zona_archivos_widget = QWidget()
        self.zona_archivos_widget.setStyleSheet("background:transparent;")
        self.zona_archivos = QVBoxLayout(self.zona_archivos_widget)
        self.zona_archivos.setSpacing(4)
        self.zona_archivos.setContentsMargins(8, 0, 8, 4)

        self.zona_archivos_scroll = QScrollArea()
        self.zona_archivos_scroll.setWidget(self.zona_archivos_widget)
        self.zona_archivos_scroll.setWidgetResizable(True)
        self.zona_archivos_scroll.setMaximumHeight(160)
        self.zona_archivos_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self.zona_archivos_scroll.hide()
        sb_tree_lay.addWidget(self.zona_archivos_scroll)

        self.sidebar_lay.addWidget(self.sb_tree_frame, 1)

        # ─ Modo descargas ─
        self.sb_dl_frame = QWidget()
        self.sb_dl_frame.hide()
        sb_dl_lay = QVBoxLayout(self.sb_dl_frame)
        sb_dl_lay.setContentsMargins(0, 0, 0, 0)
        sb_dl_lay.setSpacing(0)

        dl_srch = QLineEdit()
        dl_srch.setPlaceholderText("🔍  Buscar archivo…")
        dl_srch.setFixedHeight(32)
        dl_srch.setStyleSheet(f"QLineEdit{{background:{t('inp')};color:{t('tp')};border:none;border-bottom:1px solid {t('brd')};padding:0 12px;font-size:11px;font-family:Inter,-apple-system,sans-serif;}}")
        sb_dl_lay.addWidget(dl_srch)

        self.dl_count_lbl = QLabel("0 archivos")
        self.dl_count_lbl.setStyleSheet(label_style(9, "tm") + "padding:4px 12px;")
        sb_dl_lay.addWidget(self.dl_count_lbl)

        self.dl_lista_widget = QWidget()
        self.dl_lista_widget.setStyleSheet("background:transparent;")
        self.dl_lista_lay = QVBoxLayout(self.dl_lista_widget)
        self.dl_lista_lay.setContentsMargins(8, 6, 8, 6)
        self.dl_lista_lay.setSpacing(5)
        self.dl_lista_lay.addStretch()

        dl_scroll = QScrollArea()
        dl_scroll.setWidget(self.dl_lista_widget)
        dl_scroll.setWidgetResizable(True)
        dl_scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}QScrollBar:vertical{width:3px;background:transparent;}QScrollBar::handle:vertical{background:rgba(255,255,255,40);border-radius:2px;}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        sb_dl_lay.addWidget(dl_scroll, 1)

        btn_back = QPushButton("← Volver al árbol")
        btn_back.setFixedHeight(34)
        btn_back.setStyleSheet(f"background:{t('card')};color:{t('ts')};border:none;border-top:1px solid {t('brd')};font-size:11px;font-family:Inter,-apple-system,sans-serif;")
        btn_back.clicked.connect(lambda: self._sb_mode("tree"))
        sb_dl_lay.addWidget(btn_back)

        self.sidebar_lay.addWidget(self.sb_dl_frame)
        dl_srch.textChanged.connect(lambda q: self._cargar_dl_sidebar(q))

        # ─ Botón nuevo semestre ─
        self.btn_new_sem = QPushButton("＋  Nuevo Semestre")
        self.btn_new_sem.setFixedHeight(38)
        self.btn_new_sem.setStyleSheet(btn_style(t('acc'), "white", 0, "0 14px") +
            f"border-top:1px solid {t('brd')};border-radius:0;")
        self.btn_new_sem.clicked.connect(self.crear_nuevo_semestre)
        self.sidebar_lay.addWidget(self.btn_new_sem)

        self.body_lay.addWidget(self.sidebar)
        self._sb_mode("tree")

    def _sbt_style(self, activo):
        if activo:
            return f"QPushButton{{flex:1;background:transparent;color:{t('acct')};border:none;border-bottom:2px solid {t('acc')};font-size:11px;font-weight:500;font-family:Inter,-apple-system,sans-serif;padding:0 12px;}}"
        return f"QPushButton{{flex:1;background:transparent;color:{t('tm')};border:none;border-bottom:2px solid transparent;font-size:11px;font-family:Inter,-apple-system,sans-serif;padding:0 12px;}} QPushButton:hover{{color:{t('ts')};background:{t('card')}}}"

    def _sb_mode(self, modo):
        if modo == "tree":
            self.sb_tree_frame.show()
            self.sb_dl_frame.hide()
            self.sbt_tree.setStyleSheet(self._sbt_style(True))
            self.sbt_dl.setStyleSheet(self._sbt_style(False))
        else:
            self.sb_tree_frame.hide()
            self.sb_dl_frame.show()
            self.sbt_dl.setStyleSheet(self._sbt_style(True))
            self.sbt_tree.setStyleSheet(self._sbt_style(False))
            self._cargar_dl_sidebar("")

    def _cargar_dl_sidebar(self, query=""):
        # Limpiar lista
        while self.dl_lista_lay.count() > 1:
            item = self.dl_lista_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(carpeta):
            self.dl_count_lbl.setText("0 archivos")
            return

        archivos = sorted(
            [f for f in os.listdir(carpeta) if f.endswith((".docx", ".pdf")) and query.lower() in f.lower()],
            key=lambda x: os.path.getmtime(os.path.join(carpeta, x)), reverse=True
        )[:15]

        self.dl_count_lbl.setText(f"{len(archivos)} archivo{'s' if len(archivos)!=1 else ''} · clic para opciones")

        for arc in archivos:
            ruta = os.path.join(carpeta, arc)
            es_docx = arc.endswith(".docx")
            kb = os.path.getsize(ruta) // 1024

            card = QFrame()
            card.setStyleSheet(f"QFrame{{background:{t('card')};border:1px solid {t('brd')};border-radius:10px;}} QFrame:hover{{border:1px solid {t('acc')};}}")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(0, 0, 0, 0)
            card_lay.setSpacing(0)

            row = QFrame()
            row.setStyleSheet("background:transparent;border:none;")
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(9, 7, 9, 7)
            row_lay.setSpacing(7)

            badge = QLabel("W" if es_docx else "P")
            badge.setFixedSize(28, 28)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bg = "rgba(24,95,165,80)" if es_docx else "rgba(163,45,45,80)"
            fg = "#85B7EB" if es_docx else "#F09595"
            badge.setStyleSheet(f"background:{bg};color:{fg};border-radius:7px;font-weight:700;font-size:10px;border:none;")

            info = QVBoxLayout()
            info.setSpacing(1)
            n = QLabel(arc[:22] + "…" if len(arc) > 22 else arc)
            n.setStyleSheet(label_style(10, "tp", "500"))
            s = QLabel(f"{kb} KB")
            s.setStyleSheet(label_style(9, "tm"))
            info.addWidget(n); info.addWidget(s)

            arr = QLabel("▾")
            arr.setStyleSheet(label_style(11, "tm"))

            row_lay.addWidget(badge)
            row_lay.addLayout(info)
            row_lay.addStretch()
            row_lay.addWidget(arr)
            card_lay.addWidget(row)

            # Botones acción (hidden, se muestran al click)
            actions = QFrame()
            actions.setStyleSheet("background:transparent;border:none;")
            actions.hide()
            act_lay = QHBoxLayout(actions)
            act_lay.setContentsMargins(8, 0, 8, 8)
            act_lay.setSpacing(4)

            for txt, style, fn in [
                ("↗ Abrir",     "background:rgba(40,200,64,35);color:#28c840;border:1px solid rgba(40,200,64,50);",  lambda _,r=ruta: os.startfile(r)),
                ("📁 Mover",    f"background:{t('accd')};color:{t('acct')};border:1px solid rgba(55,138,221,50);",  lambda _,r=ruta,a=arc: self._dl_mover(r,a)),
                ("✏️ Renombrar","background:rgba(254,188,46,35);color:#febc2e;border:1px solid rgba(254,188,46,50);",lambda _,r=ruta,a=arc: self._dl_renombrar(r,a)),
                ("🗑️ Eliminar", "background:rgba(255,95,87,35);color:#ff5f57;border:1px solid rgba(255,95,87,50);",  lambda _,r=ruta,a=arc: self._dl_eliminar(r,a)),
            ]:
                b = QPushButton(txt)
                b.setFixedHeight(24)
                b.setStyleSheet(f"QPushButton{{{style}border-radius:6px;font-size:10px;font-family:Inter,-apple-system,sans-serif;padding:0 7px;}} QPushButton:hover{{opacity:0.75;}}")
                b.clicked.connect(fn)
                act_lay.addWidget(b)
            card_lay.addWidget(actions)

            # Toggle actions
            def toggle(c=card, a=actions, ar=arr):
                vis = a.isVisible()
                a.setVisible(not vis)
                ar.setText("▴" if not vis else "▾")
            row.mousePressEvent = lambda e, fn=toggle: fn()
            row.setCursor(Qt.CursorShape.PointingHandCursor)

            self.dl_lista_lay.insertWidget(self.dl_lista_lay.count() - 1, card)

    def _dl_mover(self, ruta, nombre):
        sems = self.obtener_semestres_raiz()
        sem, ok1 = QInputDialog.getItem(self, "Mover", "Semestre:", sems, 0, False)
        if not ok1: return
        mats = [m for m in os.listdir(os.path.join(PATH_RAIZ, sem))
                if os.path.isdir(os.path.join(PATH_RAIZ, sem, m)) and m != "Plantillas"]
        mat, ok2 = QInputDialog.getItem(self, "Mover", "Materia:", mats, 0, False)
        if not ok2: return
        shutil.move(ruta, os.path.join(PATH_RAIZ, sem, mat, nombre))
        self._cargar_dl_sidebar()
        self.actualizar_arbol()
        self.notificar("gn", "Movido", f"→ {sem} / {mat}")

    def _dl_renombrar(self, ruta, nombre):
        nuevo, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=nombre)
        if ok and nuevo:
            if not nuevo.endswith((".docx", ".pdf")):
                nuevo += ".docx" if nombre.endswith(".docx") else ".pdf"
            carpeta = os.path.dirname(ruta)
            os.rename(ruta, os.path.join(carpeta, nuevo))
            self._cargar_dl_sidebar()
            self.actualizar_arbol()

    def _dl_eliminar(self, ruta, nombre):
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar {nombre}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            os.remove(ruta)
            self._cargar_dl_sidebar()
            self.actualizar_arbol()

    # ── PANEL UEA (navegador) ─────────────────
    def _build_panel_uea(self):
        self.panel_uea = QWidget()
        uea_lay = QVBoxLayout(self.panel_uea)
        uea_lay.setContentsMargins(0, 0, 0, 0)
        uea_lay.setSpacing(0)

        # ─ Browser bar (tabs + dl) ─
        br_bar = QFrame()
        br_bar.setFixedHeight(44)
        br_bar.setStyleSheet(f"background:{t('bar')};border-bottom:1px solid {t('brd')};")
        br_bar_lay = QHBoxLayout(br_bar)
        br_bar_lay.setContentsMargins(10, 7, 10, 7)
        br_bar_lay.setSpacing(5)

        # Toggle sidebar
        self.btn_sb_tog = QPushButton("☰")
        self.btn_sb_tog.setFixedSize(30, 30)
        self.btn_sb_tog.setStyleSheet(f"QPushButton{{background:{t('card')};border:1px solid {t('brd')};border-radius:8px;color:{t('ts')};font-size:14px;}} QPushButton:hover{{background:{t('cardh')};}}")
        self.btn_sb_tog.clicked.connect(self.toggle_sidebar)
        br_bar_lay.addWidget(self.btn_sb_tog)

        # Tabs contenedor
        self.tabs_container = QWidget()
        self.tabs_container_lay = QHBoxLayout(self.tabs_container)
        self.tabs_container_lay.setContentsMargins(0, 0, 0, 0)
        self.tabs_container_lay.setSpacing(3)
        self.tabs_container_lay.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinimumSize)  # ← AGREGA ESTO
        br_bar_lay.addWidget(self.tabs_container)

        # + nueva pestaña
        btn_new_tab = QPushButton("+")
        btn_new_tab.setFixedSize(26, 26)
        btn_new_tab.setStyleSheet(f"QPushButton{{background:{t('card')};color:{t('tm')};border:1px solid {t('brd')};border-radius:50%;font-size:16px;font-weight:bold;}} QPushButton:hover{{background:{t('cardh')};}}")
        btn_new_tab.clicked.connect(lambda: self.nueva_pestana())
        br_bar_lay.addWidget(btn_new_tab)

        br_bar_lay.addStretch(1)

        # Botón descargas
        self.btn_dl_nav = QPushButton(f"⬇  0")
        self.btn_dl_nav.setFixedHeight(28)
        self.btn_dl_nav.setStyleSheet(f"QPushButton{{background:{t('accd')};color:{t('acct')};border:1px solid rgba(55,138,221,80);border-radius:7px;padding:0 11px;font-size:11px;font-weight:600;font-family:Inter,-apple-system,sans-serif;}} QPushButton:hover{{background:rgba(55,138,221,70);}}")
        self.btn_dl_nav.clicked.connect(self.toggle_panel_descargas)
        br_bar_lay.addWidget(self.btn_dl_nav)

        uea_lay.addWidget(br_bar)

        # ─ URL bar ─
        url_bar = QFrame()
        url_bar.setFixedHeight(40)
        url_bar.setStyleSheet(f"background:{t('bar')};border-bottom:1px solid {t('brd')};")
        url_lay = QHBoxLayout(url_bar)
        url_lay.setContentsMargins(10, 6, 10, 6)
        url_lay.setSpacing(5)

        for txt, fn in [("←", lambda: self.browser_actual().back()),
                        ("→", lambda: self.browser_actual().forward()),
                        ("↻", lambda: self.browser_actual().reload())]:
            b = QPushButton(txt)
            b.setFixedSize(26, 26)
            b.setStyleSheet(f"QPushButton{{background:{t('card')};border:1px solid {t('brd')};border-radius:7px;color:{t('tm')};font-size:12px;}} QPushButton:hover{{background:{t('cardh')};color:{t('tp')};}}")
            b.clicked.connect(fn)
            url_lay.addWidget(b)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Buscar en Google o ingresar URL…")
        self.url_bar.setFixedHeight(28)
        self.url_bar.setStyleSheet(f"QLineEdit{{background:{t('inp')};color:{t('ts')};border:1px solid {t('brd')};border-radius:8px;padding:0 12px;font-size:11.5px;font-family:Inter,-apple-system,sans-serif;}}")
        self.url_bar.returnPressed.connect(self.navegar_url)
        url_lay.addWidget(self.url_bar, 1)

        uea_lay.addWidget(url_bar)

        # ─ Stack navegadores ─
        self.stack_browsers = QStackedWidget()
        self.stack_browsers.setStyleSheet("background:transparent;border:none;")
        uea_lay.addWidget(self.stack_browsers, 1)

        # Perfiles
        self.perfil_persistente = QWebEngineProfile("Storage_AsmoRoot", self)
        ruta_datos = os.path.join(PATH_RAIZ, "Navegador_Datos")
        self.perfil_persistente.setPersistentStoragePath(ruta_datos)
        self.perfil_persistente.setDownloadPath(os.path.join(os.path.expanduser("~"), "Downloads"))
        self.perfil_persistente.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.perfil_persistente.setHttpAcceptLanguage("es-ES,es;q=0.9")
        self.perfil_persistente.downloadRequested.connect(self.gestionar_descarga)

        self.perfil_google = QWebEngineProfile("Storage_Google", self)
        ruta_google = os.path.join(PATH_RAIZ, "Google_Datos")
        self.perfil_google.setPersistentStoragePath(ruta_google)
        self.perfil_google.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.perfil_google.setHttpAcceptLanguage("es-ES,es;q=0.9")
        self.perfil_google.downloadRequested.connect(self.gestionar_descarga)

        # Pestaña UEA
        self.nueva_pestana(
            url="https://eva.pregrado.uea.edu.ec/eva2526/web/my/courses.php?lang=es",
            titulo="🎓 UEA",
            fija=True
        )

        self.stack.addWidget(self.panel_uea)   # index 0

    # ── PANEL GESTIÓN ─────────────────────────
    def _build_panel_gestion(self):
        self.panel_gestion = QScrollArea()
        self.panel_gestion.setWidgetResizable(True)
        self.panel_gestion.setStyleSheet("border:none;background:transparent;")

        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(20)

        # Título
        ttl = QLabel("CENTRO DE GESTIÓN ACADÉMICA")
        ttl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ttl.setStyleSheet(label_style(22, "tp", "600"))
        lay.addWidget(ttl)

        # ─ Row: Formulario + Botones ─
        mid = QHBoxLayout()
        mid.setSpacing(16)

        # Card formulario
        self.card_inputs = QFrame()
        self.card_inputs.setStyleSheet(f"QFrame{{background:{t('card')};border:1px solid {t('brd')};border-radius:14px;}}")
        form_lay = QVBoxLayout(self.card_inputs)
        form_lay.setContentsMargins(20, 18, 20, 18)
        form_lay.setSpacing(12)

        self.sem_menu = QComboBox()
        self.sem_menu.addItems(self.obtener_semestres_raiz())
        self.sem_menu.currentTextChanged.connect(self.actualizar_materias)

        self.mat_menu = QComboBox()
        self.mat_menu.currentTextChanged.connect(self.guardar_materia_seleccionada)

        self.sem_ent = QLineEdit()
        self.sem_ent.setPlaceholderText("Ej: Semana 10")

        self.tema_ent = QLineEdit()
        self.tema_ent.setPlaceholderText("Escriba el título de la tarea…")

        for etiqueta, widget in [
            ("Seleccione el semestre", self.sem_menu),
            ("Seleccione la materia",  self.mat_menu),
            ("Semana de trabajo",      self.sem_ent),
            ("Tema de la tarea",       self.tema_ent),
        ]:
            lbl = QLabel(etiqueta)
            lbl.setStyleSheet(label_style(11, "tm", "500"))
            widget.setFixedHeight(40)
            widget.setStyleSheet(input_style())
            form_lay.addWidget(lbl)
            form_lay.addWidget(widget)

        mid.addWidget(self.card_inputs, 3)

        # Botones acción
        col_btns = QVBoxLayout()
        col_btns.setSpacing(10)

        self.btn_start = QPushButton("🚀  Iniciar Nueva Tarea")
        self.btn_start.setFixedHeight(58)
        self.btn_start.setStyleSheet(btn_style(t('acc'), "white", 12, "0 20px") + f"QPushButton{{font-size:14px;}}")
        self.btn_start.clicked.connect(self.iniciar_flujo)

        self.btn_pdf_main = QPushButton("📄  Generar PDF")
        self.btn_pdf_main.setFixedHeight(58)
        self.btn_pdf_main.setStyleSheet(btn_style("#21618C", "white", 12, "0 20px") + f"QPushButton{{font-size:14px;}}")
        self.btn_pdf_main.clicked.connect(self.generar_pdf)

        self.btn_finalizar = QPushButton("✅  Finalizar")
        self.btn_finalizar.setFixedHeight(58)
        self.btn_finalizar.setStyleSheet(btn_style("#7f0000", "white", 12, "0 20px") + f"QPushButton{{font-size:14px;}}")
        self.btn_finalizar.clicked.connect(self.reset_ui)

        col_btns.addWidget(self.btn_start)
        col_btns.addWidget(self.btn_pdf_main)
        col_btns.addWidget(self.btn_finalizar)
        col_btns.addStretch()
        mid.addLayout(col_btns, 1)
        lay.addLayout(mid)

        # ─ Recovery box ─
        self.fix_box = QFrame()
        self.fix_box.setStyleSheet(f"QFrame{{background:{t('card')};border:1px solid {t('brd')};border-radius:14px;}}")
        fix_lay = QVBoxLayout(self.fix_box)
        fix_lay.setContentsMargins(20, 16, 20, 16)
        fix_lay.setSpacing(10)

        hdr_fix = QHBoxLayout()
        lbl_fix = QLabel("MODO DE RECUPERACIÓN / CORRECCIÓN")
        lbl_fix.setStyleSheet(label_style(11, "acc", "600"))
        self.status_ind = QLabel("● REPOSO")
        self.status_ind.setStyleSheet(label_style(11, "tm", "600"))
        hdr_fix.addWidget(lbl_fix)
        hdr_fix.addStretch()
        hdr_fix.addWidget(self.status_ind)
        fix_lay.addLayout(hdr_fix)

        btns_fix = QHBoxLayout()
        btns_fix.setSpacing(10)
        self.btn_fix_word = QPushButton("📂  Abrir Word Histórico")
        self.btn_fix_word.setFixedHeight(38)
        self.btn_fix_word.setStyleSheet(btn_style("#238636", "white", 9, "0 16px"))
        self.btn_fix_word.setEnabled(False)
        self.btn_fix_word.clicked.connect(self.reabrir_word)

        self.btn_fix_pdf = QPushButton("📄  Actualizar PDF Histórico")
        self.btn_fix_pdf.setFixedHeight(38)
        self.btn_fix_pdf.setStyleSheet(btn_style("#1F6FEB", "white", 9, "0 16px"))
        self.btn_fix_pdf.setEnabled(False)
        self.btn_fix_pdf.clicked.connect(self.generar_pdf)

        btns_fix.addWidget(self.btn_fix_word)
        btns_fix.addWidget(self.btn_fix_pdf)
        fix_lay.addLayout(btns_fix)
        lay.addWidget(self.fix_box)
        lay.addStretch()

        self.panel_gestion.setWidget(inner)
        self.stack.addWidget(self.panel_gestion)   # index 1

    # ── STATUS BAR ────────────────────────────
    def _build_statusbar(self):
        self.statusbar_frame = QFrame()
        self.statusbar_frame.setFixedHeight(28)
        self.statusbar_frame.setStyleSheet(f"background:{t('bar')};border-top:1px solid {t('brd')};")
        sb_lay = QHBoxLayout(self.statusbar_frame)
        sb_lay.setContentsMargins(14, 0, 30, 0)  # ← 30px derecha para el grip
        sb_lay.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet(f"color:{t('grn')};font-size:9px;border:none;")
        self.sb_lbl = QLabel("Sistema listo")
        self.sb_lbl.setStyleSheet(label_style(10, "ts"))
        sep = QLabel("·")
        sep.setStyleSheet(label_style(10, "tm"))
        self.sb_lbl2 = QLabel("")
        self.sb_lbl2.setStyleSheet(label_style(10, "ts"))
        ver = QLabel(f"AsmoRoot {self.version_sistema}")
        ver.setStyleSheet(label_style(10, "tm"))

        sb_lay.addWidget(dot)
        sb_lay.addWidget(self.sb_lbl)
        sb_lay.addWidget(sep)
        sb_lay.addWidget(self.sb_lbl2)
        sb_lay.addStretch()
        sb_lay.addWidget(ver)

        # Grip posicionado con move() absoluto — única forma que funciona en FramelessWindowHint
        self._grip_lbl = QLabel("◢", self.statusbar_frame)
        self._grip_lbl.setFixedSize(24, 24)
        self._grip_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._grip_lbl.setStyleSheet("color:rgba(255,255,255,100);font-size:13px;border:none;background:transparent;")
        self._grip_lbl.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self._grip_lbl._drag_pos = None
        self._grip_lbl._orig_size = None

        def _press(e):
            if e.button() == Qt.MouseButton.LeftButton:
                self._grip_lbl._drag_pos = e.globalPosition().toPoint()
                self._grip_lbl._orig_size = self.size()

        def _move(e):
            if self._grip_lbl._drag_pos:
                delta = e.globalPosition().toPoint() - self._grip_lbl._drag_pos
                self.resize(
                    max(800, self._grip_lbl._orig_size.width() + delta.x()),
                    max(600, self._grip_lbl._orig_size.height() + delta.y())
                )

        def _release(e):
            self._grip_lbl._drag_pos = None

        self._grip_lbl.mousePressEvent = _press
        self._grip_lbl.mouseMoveEvent = _move
        self._grip_lbl.mouseReleaseEvent = _release

        # Posicionar en esquina derecha del statusbar
        self.statusbar_frame.resizeEvent = lambda e: self._grip_lbl.move(
            self.statusbar_frame.width() - 24, 2
        )

    # ── TEMA ──────────────────────────────────
    def toggle_tema(self):
        self.tema_actual = "light" if self.tema_actual == "dark" else "dark"
        AsmoRootApp.CURRENT_THEME = THEME[self.tema_actual]
        self._aplicar_tema()
        self.titlebar.btn_tema.setText("🌙" if self.tema_actual == "light" else "☀️")

    def _aplicar_tema(self):
        T = AsmoRootApp.CURRENT_THEME
        # Fondo general de la ventana
        self.setStyleSheet(f"background:{T['bg']};font-family:Inter,-apple-system,sans-serif;")
        # Frame raíz
        self.root.setStyleSheet(f"""
            #root_frame {{
                background: {T['win']};
                border-radius: 14px;
                border: 1px solid {T['brd']};
            }}
        """)
        # Titlebar
        self.titlebar.setStyleSheet(f"background:{T['bar']};border-bottom:1px solid {T['brd']};")
        # Main tabs bar
        self.mtabs_bar.setStyleSheet(f"background:{T['bar']};border-bottom:1px solid {T['brd']};")
        # Sidebar
        self.sidebar.setStyleSheet(f"background:{T['sb']};border-right:1px solid {T['brd']};")
        # Status bar
        self.statusbar_frame.setStyleSheet(f"background:{T['bar']};border-top:1px solid {T['brd']};")
        # Refrescar botones de tabs principales
        self.btn_tab_uea.setStyleSheet(self._mtab_style(self.stack.currentIndex() == 0))
        self.btn_tab_panel.setStyleSheet(self._mtab_style(self.stack.currentIndex() == 1))

    # ── SIDEBAR TOGGLE ────────────────────────
    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.setVisible(self.sidebar_visible)

    # ── ÁRBOL ─────────────────────────────────
    def obtener_semestres_raiz(self):
        if not os.path.exists(PATH_RAIZ): return []
        return [f for f in os.listdir(PATH_RAIZ)
                if os.path.isdir(os.path.join(PATH_RAIZ, f)) and f not in ["Logo","Navegador_Datos","Google_Datos"]]

    def crear_nuevo_semestre(self):
        sem, ok1 = QInputDialog.getText(self, "Nuevo Semestre", "Nombre del semestre:")
        if not ok1 or not sem: return
        mats_raw, ok2 = QInputDialog.getText(self, "Materias", "Materias separadas por coma:")
        if not ok2 or not mats_raw: return
        ruta_sem = os.path.join(PATH_RAIZ, sem)
        os.makedirs(os.path.join(ruta_sem, "Plantillas"), exist_ok=True)
        for mat in [m.strip() for m in mats_raw.split(",")]:
            os.makedirs(os.path.join(ruta_sem, mat), exist_ok=True)
            with open(os.path.join(ruta_sem, "Plantillas", f"{mat}.docx"), 'wb'): pass
        self.actualizar_arbol()
        self.sem_menu.clear()
        self.sem_menu.addItems(self.obtener_semestres_raiz())
        self.notificar("gn", "Semestre creado", sem)

    def actualizar_arbol(self):
        self.tree.clear()
        query = self.search_ent.text().lower()
        orden = {"primer":1,"1er":1,"segundo":2,"2do":2,"tercer":3,"3er":3,
                 "cuarto":4,"4to":4,"quinto":5,"5to":5,"sexto":6,"6to":6,
                 "septimo":7,"7mo":7,"octavo":8,"8vo":8,"noveno":9,"decimo":10}
        def peso(n):
            nl = n.lower()
            for k,v in orden.items():
                if k in nl: return v
            return 99

        for sem in sorted(self.obtener_semestres_raiz(), key=peso):
            sem_node = QTreeWidgetItem([f"📂  {sem}"])
            ruta_sem = os.path.join(PATH_RAIZ, sem)
            materias = sorted([m for m in os.listdir(ruta_sem) if os.path.isdir(os.path.join(ruta_sem, m))])
            for mat in materias:
                mat_node = QTreeWidgetItem([f"📘  {mat}"])
                ruta_mat = os.path.join(ruta_sem, mat)
                archivos = sorted(
                    [f for f in os.listdir(ruta_mat) if f.endswith((".docx", ".pdf"))],
                    key=lambda x: os.path.getmtime(os.path.join(ruta_mat, x)), reverse=True
                )
                for arc in archivos:
                    if query in arc.lower() or query in mat.lower():
                        icon = "📝" if arc.endswith(".docx") else "📕"
                        mat_node.addChild(QTreeWidgetItem([f"{icon}  {arc}"]))
                if mat_node.childCount() > 0 or query == "":
                    sem_node.addChild(mat_node)
            if sem_node.childCount() > 0:
                self.tree.addTopLevelItem(sem_node)

        # Carpeta descargas
        carpeta_dl = os.path.join(os.path.expanduser("~"), "Downloads")
        nodo_dl = QTreeWidgetItem(["⬇️  Descargas"])
        if os.path.exists(carpeta_dl):
            for arc in sorted([f for f in os.listdir(carpeta_dl) if f.endswith((".docx",".pdf"))],
                              key=lambda x: os.path.getmtime(os.path.join(carpeta_dl, x)), reverse=True):
                if query in arc.lower() or query == "":
                    icon = "📝" if arc.endswith(".docx") else "📕"
                    nodo_dl.addChild(QTreeWidgetItem([f"{icon}  {arc}"]))
        self.tree.addTopLevelItem(nodo_dl)

    def actualizar_materias(self, semestre):
        self.mat_menu.clear()
        ruta = os.path.join(PATH_RAIZ, semestre)
        if os.path.exists(ruta):
            mats = sorted([m for m in os.listdir(ruta) if os.path.isdir(os.path.join(ruta, m)) and m != "Plantillas"])
            self.mat_menu.addItems(mats)
            self.config["ultimo_semestre"] = semestre
            self.guardar_config()

    def guardar_materia_seleccionada(self, mat):
        if mat:
            self.config["ultima_materia"] = mat
            self.guardar_config()

    def cargar_ultima_sesion(self):
        u_sem = self.config.get("ultimo_semestre", "")
        if u_sem in self.obtener_semestres_raiz():
            self.sem_menu.setCurrentText(u_sem)
            self.actualizar_materias(u_sem)
            self.mat_menu.setCurrentText(self.config.get("ultima_materia", ""))

    # ── LÓGICA ACADÉMICA ──────────────────────
    def iniciar_flujo(self):
        try:
            sem = self.sem_menu.currentText()
            mat = self.mat_menu.currentText()
            sema = self.sem_ent.text()
            tema = self.tema_ent.text()
            if not all([mat, sema, tema]):
                self.notificar("or", "Campos incompletos", "Rellena todos los campos")
                return
            fecha = datetime.now().strftime('%Y-%m-%d')
            ini_mat = "".join([p[0].upper() for p in mat.split() if p.lower() not in ["de","la","el","y"]])
            solo_num = "".join(filter(str.isdigit, sema))
            nombre = f"{fecha}_{tema.replace(' ','-')}_{ini_mat}_Semana-{solo_num or 'X'}.docx"
            self.archivo_docx_sesion = os.path.join(PATH_RAIZ, sem, mat, nombre)
            plantilla = os.path.join(PATH_RAIZ, sem, "Plantillas", f"{mat}.docx")
            if os.path.exists(plantilla):
                shutil.copy(plantilla, self.archivo_docx_sesion)
                os.startfile(self.archivo_docx_sesion)
                self.status_ind.setText("● EDITANDO")
                self.status_ind.setStyleSheet(label_style(11, "yel", "600"))
                self.btn_fix_word.setEnabled(True)
                self.btn_fix_pdf.setEnabled(True)
                self.actualizar_arbol()
                self._agregar_pestana_archivo(self.archivo_docx_sesion)
                self.notificar("bl", "Nueva Tarea", f"Iniciando en {mat}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def generar_pdf(self):
        if not os.path.exists(self.archivo_docx_sesion):
            self.notificar("or", "Sin documento", "Inicia una tarea primero")
            return
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(self.archivo_docx_sesion)
            path_pdf = self.archivo_docx_sesion.replace(".docx", ".pdf")
            doc.SaveAs(path_pdf, FileFormat=17)
            doc.Close()
            word.Quit()
            self.actualizar_arbol()
            self.status_ind.setText("● TAREA FINALIZADA")
            self.status_ind.setStyleSheet(label_style(11, "grn", "600"))
            self.notificar("gn", "PDF generado", "Guardado correctamente")
        except Exception as e:
            self.notificar("rd", "Error PDF", str(e)[:60])

    def reabrir_word(self):
        if os.path.exists(self.archivo_docx_sesion):
            os.startfile(self.archivo_docx_sesion)

    def reset_ui(self):
        self.tema_ent.clear()
        self.sem_ent.clear()
        self.status_ind.setText("● REPOSO")
        self.status_ind.setStyleSheet(label_style(11, "tm", "600"))
        self.btn_fix_word.setEnabled(False)
        self.btn_fix_pdf.setEnabled(False)
        self.notificar("or", "Finalizado", "Tarea archivada")

    # ── ÁRBOL: seleccionar / abrir ─────────────
    def seleccionar_desde_arbol(self, item):
        if item.parent() and item.parent().parent():
            nombre_arc = item.text(0).split("  ", 1)[-1]
            if not nombre_arc.endswith(".docx"): return
            materia  = item.parent().text(0).split("  ", 1)[-1]
            semestre = item.parent().parent().text(0).split("  ", 1)[-1]
            self.sem_menu.setCurrentText(semestre)
            self.mat_menu.setCurrentText(materia)
            self.archivo_docx_sesion = os.path.join(PATH_RAIZ, semestre, materia, nombre_arc)
            self.status_ind.setText("● TAREA DETECTADA")
            self.status_ind.setStyleSheet(label_style(11, "acc", "600"))
            self.btn_fix_word.setEnabled(True)
            self.btn_fix_pdf.setEnabled(True)

    def abrir_archivo_desde_arbol(self, item):
        if item.childCount() == 0:
            nombre_arc = item.text(0).split("  ", 1)[-1]
            padre = item.parent()
            if padre and "Descargas" in padre.text(0):
                carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
                ruta = os.path.join(carpeta, nombre_arc)
            else:
                mat = padre.text(0).split("  ", 1)[-1]
                sem = padre.parent().text(0).split("  ", 1)[-1]
                ruta = os.path.join(PATH_RAIZ, sem, mat, nombre_arc)
            if os.path.exists(ruta):
                os.startfile(ruta)
                self.sb_lbl.setText(f"📂 Abriendo: {nombre_arc}")
                QTimer.singleShot(4000, lambda: self.sb_lbl.setText("Sistema listo"))
                self._agregar_pestana_archivo(ruta)

    def mostrar_menu_contextual(self, posicion):
        item = self.tree.itemAt(posicion)
        if not item: return
        menu = QMenu()
        menu.setStyleSheet(f"QMenu{{background:{t('sb')};color:{t('tp')};border:1px solid {t('brd')};border-radius:10px;font-size:12px;padding:4px;}} QMenu::item{{padding:6px 14px;border-radius:6px;}} QMenu::item:selected{{background:{t('accd')};color:{t('acct')};}}")
        menu.addAction("✏️  Renombrar").triggered.connect(lambda: self.gestionar_item_arbol(item, "renombrar"))
        menu.addAction("🗑️  Eliminar").triggered.connect(lambda: self.gestionar_item_arbol(item, "borrar"))
        menu.exec(self.tree.viewport().mapToGlobal(posicion))

    def gestionar_item_arbol(self, item, operacion):
        texto = item.text(0).split("  ", 1)[-1]
        if not item.parent():
            ruta = os.path.join(PATH_RAIZ, texto); tipo = "Semestre"
        elif not item.parent().parent():
            sem = item.parent().text(0).split("  ", 1)[-1]
            ruta = os.path.join(PATH_RAIZ, sem, texto); tipo = "Materia"
        else:
            mat = item.parent().text(0).split("  ", 1)[-1]
            sem = item.parent().parent().text(0).split("  ", 1)[-1]
            ruta = os.path.join(PATH_RAIZ, sem, mat, texto); tipo = "Archivo"

        if operacion == "renombrar":
            nuevo, ok = QInputDialog.getText(self, f"Renombrar {tipo}", f"Nuevo nombre:", text=texto)
            if ok and nuevo:
                if tipo == "Archivo" and not nuevo.lower().endswith((".docx",".pdf")):
                    nuevo += ".docx" if texto.endswith(".docx") else ".pdf"
                try:
                    os.rename(ruta, os.path.join(os.path.dirname(ruta), nuevo))
                    self.actualizar_arbol()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
        elif operacion == "borrar":
            if QMessageBox.question(self, "Eliminar", f"¿Eliminar {tipo}?\n({texto})",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                try:
                    shutil.rmtree(ruta) if os.path.isdir(ruta) else os.remove(ruta)
                    self.actualizar_arbol()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))

    # ── ARCHIVOS ABIERTOS (pestañas) ──────────
    def _agregar_pestana_archivo(self, ruta):
        for i in range(self.zona_archivos.count()):
            w = self.zona_archivos.itemAt(i).widget()
            if w and isinstance(w, PestanaArchivo) and w.ruta == ruta:
                return
        pestana = PestanaArchivo(ruta, self)
        self.zona_archivos.addWidget(pestana)
        self.zona_archivos_label.show()
        self.zona_archivos_scroll.show()
        monitor = MonitorArchivo(ruta)
        monitor.archivo_cerrado.connect(lambda: self.cerrar_pestana_archivo(pestana))
        monitor.start()
        pestana.monitor = monitor

    def cerrar_pestana_archivo(self, pestana):
        if hasattr(pestana, 'monitor'):
            pestana.monitor.detener()
        self.zona_archivos.removeWidget(pestana)
        pestana.deleteLater()
        if self.zona_archivos.count() == 0:
            self.zona_archivos_label.hide()
            self.zona_archivos_scroll.hide()

    # ── NAVEGADOR ─────────────────────────────
    def nueva_pestana(self, url=None, titulo="Nueva pestaña", fija=False):
        if url is None:
            url = f"file:///{PATH_RAIZ}/nueva_pestana.html".replace("\\", "/")
        perfil = self.perfil_persistente if "uea.edu.ec" in url else self.perfil_google
        pestana = PestañaNavegador(perfil, self, url)

        # Botón tab
        btn_tab = QPushButton(titulo[:22])
        btn_tab.setFixedHeight(26)
        btn_tab.setMinimumWidth(55)
        btn_tab.setMaximumWidth(120)
        btn_tab.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_tab.setStyleSheet(self._tab_style(False))

        pestana.browser.titleChanged.connect(
            lambda t_txt, b=btn_tab, f=fija:
                b.setText(("🎓 UEA" if f else t_txt[:20]) if t_txt else "Nueva pestaña"))
        pestana.browser.urlChanged.connect(
            lambda url_obj:
                self.url_bar.setText("" if url_obj.toString().startswith("file:///") else url_obj.toString())
            if self.browser_actual() == pestana.browser else None)

        if not fija:
            btn_cerrar_tab = QPushButton("✕")
            btn_cerrar_tab.setFixedSize(15, 15)
            btn_cerrar_tab.setStyleSheet(f"background:transparent;color:{t('tm')};border:none;font-size:9px;")
            btn_cerrar_tab.clicked.connect(lambda: self.cerrar_pestana(btn_tab))
            tab_w = QWidget()
            tl = QHBoxLayout(tab_w)
            tl.setContentsMargins(0, 0, 0, 0)
            tl.setSpacing(2)
            tl.addWidget(btn_tab)
            tl.addWidget(btn_cerrar_tab)
            self.tabs_container_lay.addWidget(tab_w)
        else:
            self.tabs_container_lay.addWidget(btn_tab)

        btn_tab.clicked.connect(lambda: self.cambiar_pestana(btn_tab))
        self.pestanas.append((btn_tab, pestana, fija))
        self.stack_browsers.addWidget(pestana)
        self.cambiar_pestana(btn_tab)

    def _tab_style(self, activo):
        if activo:
            return f"QPushButton{{background:{t('accd')};color:{t('acct')};border:1px solid rgba(55,138,221,80);border-radius:7px;padding:0 8px;font-size:11px;font-family:Inter,-apple-system,sans-serif;text-align:left;}}"
        return f"QPushButton{{background:{t('card')};color:{t('ts')};border:1px solid {t('brd')};border-radius:7px;padding:0 8px;font-size:11px;font-family:Inter,-apple-system,sans-serif;text-align:left;}} QPushButton:hover{{background:{t('cardh')};}}"

    def cambiar_pestana(self, btn_activo):
        for btn, pestana, fija in self.pestanas:
            activo = (btn == btn_activo)
            btn.setProperty("activa", activo)
            btn.setStyleSheet(self._tab_style(activo))
            self.stack_browsers.setCurrentWidget(pestana) if activo else None
            if activo:
                url_str = pestana.browser.url().toString()
                self.url_bar.setText("" if url_str.startswith("file:///") else url_str)

    def cerrar_pestana(self, btn_tab):
        if len(self.pestanas) <= 1: return
        for i, (btn, pestana, fija) in enumerate(self.pestanas):
            if btn == btn_tab and not fija:
                self.pestanas.pop(i)
                for j in range(self.tabs_container_lay.count()):
                    w = self.tabs_container_lay.itemAt(j).widget()
                    if w and (btn_tab == w or btn_tab in w.findChildren(QPushButton)):
                        self.tabs_container_lay.takeAt(j).widget().deleteLater()
                        break
                self.stack_browsers.removeWidget(pestana)
                pestana.deleteLater()
                idx = max(0, i-1)
                self.cambiar_pestana(self.pestanas[idx][0])
                break

    def navegar_url(self):
        url = self.url_bar.text().strip()
        if not url.startswith("http"):
            url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
        self.browser_actual().setUrl(QUrl(url))

    def browser_actual(self):
        for btn, pestana, fija in self.pestanas:
            if btn.property("activa"):
                return pestana.browser
        return self.pestanas[0][1].browser if self.pestanas else None

    # ── DESCARGAS ─────────────────────────────
    def gestionar_descarga(self, download):
        carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
        nombre = download.suggestedFileName()
        ruta_final = os.path.join(carpeta, nombre)
        if os.path.exists(ruta_final):
            resp = QMessageBox.question(self, "Archivo existe",
                f'"{nombre}" ya existe.\n¿Reemplazar?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp == QMessageBox.StandardButton.No:
                base, ext = os.path.splitext(nombre)
                c = 1
                while os.path.exists(os.path.join(carpeta, f"{base} ({c}){ext}")):
                    c += 1
                nombre = f"{base} ({c}){ext}"
        download.setDownloadDirectory(carpeta)
        download.setDownloadFileName(nombre)
        download.accept()
        self.sb_lbl.setText(f"⬇️ Descargando: {nombre}…")
        download.isFinishedChanged.connect(lambda: self._descarga_completada(nombre))

    def _descarga_completada(self, nombre):
        self.contador_descargas += 1
        self.btn_dl_nav.setText(f"⬇  {self.contador_descargas}")
        self.sb_lbl.setText(f"✅ Descargado: {nombre}")
        self.actualizar_arbol()
        QTimer.singleShot(4000, lambda: self.sb_lbl.setText("Sistema listo"))
        self.notificar("gn", "Descarga completa", nombre[:40])

    def toggle_panel_descargas(self):
        if self.panel_descargas.isVisible():
            self.cerrar_panel_descargas()
        else:
            self.panel_descargas.cargar_archivos()
            self.panel_descargas.show()

    def cerrar_panel_descargas(self):
        self.panel_descargas.hide()

    def abrir_explorador_descargas(self):
        ExploradorDescargas(self).exec()

    # ── DRAG & DROP árbol ─────────────────────
    def iniciar_arrastre(self, supportedActions):
        item = self.tree.currentItem()
        if not item or item.childCount() > 0: return
        texto_arc = item.text(0).split("  ", 1)[-1]
        try:
            mat = item.parent().text(0).split("  ", 1)[-1]
            sem = item.parent().parent().text(0).split("  ", 1)[-1]
            ruta = os.path.abspath(os.path.join(PATH_RAIZ, sem, mat, texto_arc))
        except AttributeError:
            return
        if os.path.exists(ruta):
            data = QMimeData()
            data.setUrls([QUrl.fromLocalFile(ruta)])
            drag = QDrag(self)
            drag.setMimeData(data)
            pix = QPixmap(32, 32)
            pix.fill(Qt.GlobalColor.transparent)
            drag.setPixmap(pix)
            drag.exec(Qt.DropAction.CopyAction)

    # ── NOTIFICACIONES ────────────────────────
    def notificar(self, tipo, titulo, mensaje):
        self.notif_area.agregar(tipo, titulo, mensaje)

    # ── RESIZE ───────────────────────────────
    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'notif_area') and hasattr(self, 'root'):
            self.notif_area.move(self.root.width() - 320, 60)

    def _toggle_maximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Inter", 10))
    app.setStyle("Fusion")
    window = AsmoRootApp()
    window.showMaximized()
    sys.exit(app.exec())