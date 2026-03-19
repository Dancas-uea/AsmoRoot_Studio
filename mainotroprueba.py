import sys
import os
import json
import shutil
from datetime import datetime
import win32com.client
from PIL import Image
import os
import psutil
from google import genai

from PIL import Image
# Busca esta línea al principio de tu archivo y asegúrate de que QMenu esté ahí:
from PyQt6.QtWidgets import (QApplication,QDialog, QMainWindow,QTextEdit, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QComboBox, QFrame,
                             QTreeWidget, QTreeWidgetItem, QMessageBox, QInputDialog,
                             QScrollArea, QSpacerItem,QFileDialog, QSizePolicy, QMenu) # <--- AGREGA ESTO AQUÍ
from PyQt6.QtWebEngineCore import (QWebEngineProfile, QWebEnginePage,
                                   QWebEngineDownloadRequest)

from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtCore import QPropertyAnimation, QPoint, QEasingCurve
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView

from PyQt6.QtCore import QMimeData
from PyQt6.QtGui import QDrag

#esta es solo una prueba
# --- CONFIGURACIÓN ESTRUCTURAL ---
PATH_RAIZ = r"C:\Users\AsmoRoot\Desktop\Universidad Estatal Amazonica"
PATH_LOGO = os.path.join(PATH_RAIZ, "Logo", "logo.png")
# Definimos la ruta de salida para el .ico en la misma carpeta del logo
PATH_ICO = os.path.join(PATH_RAIZ, "Logo", "logo.ico")

def generar_icono_profesional():
    try:
        if os.path.exists(PATH_LOGO):
            img = Image.open(PATH_LOGO)
            # Guardamos con varios tamaños para que el .exe se vea bien en todo Windows
            img.save(PATH_ICO, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
            print(f"✅ Icono creado exitosamente en: {PATH_ICO}")
        else:
            print(f"❌ No se encontró el archivo PNG en: {PATH_LOGO}")
    except Exception as e:
        print(f"❌ Error al crear el icono: {e}")

# Ejecutar la función
generar_icono_profesional()

ARCHIVO_CONFIG = os.path.join(PATH_RAIZ, "config_carrera.json")

# Monitorear en hilo separado para no congelar la UI
from PyQt6.QtCore import QThread, pyqtSignal

class MonitorArchivo(QThread):
    archivo_cerrado = pyqtSignal()

    def __init__(self, ruta):
        super().__init__()
        self.ruta = ruta
        self.activo = True

    def run(self):
        import time
        nombre_archivo = os.path.basename(self.ruta).lower()
        # Esperar 3 segundos antes de empezar a monitorear
        time.sleep(3)
        while self.activo:
            time.sleep(2)
            try:
                if self.ruta.endswith(".docx"):
                    import win32com.client
                    word = win32com.client.GetActiveObject("Word.Application")
                    nombres = [doc.FullName for doc in word.Documents]
                    if os.path.abspath(self.ruta) not in [os.path.abspath(n) for n in nombres]:
                        self.archivo_cerrado.emit()
                        break
                elif self.ruta.endswith(".pdf"):
                    nombre_archivo = os.path.splitext(os.path.basename(self.ruta))[0].lower()
                    abierto = False
                    for proc in psutil.process_iter(['name', 'cmdline']):
                        try:
                            if 'pdfgear' in proc.name().lower():
                                cmdline_str = " ".join(proc.cmdline()).lower()
                                if nombre_archivo in cmdline_str:
                                    abierto = True
                                    break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    if not abierto:
                        self.archivo_cerrado.emit()
                        break
            except:
                if self.ruta.endswith(".docx"):
                    self.archivo_cerrado.emit()
                    break

    def detener(self):
        self.activo = False

class PestanaArchivo(QWidget):
    def __init__(self, ruta, parent_app):
        super().__init__()
        self.ruta = ruta
        self.parent_app = parent_app
        self.nombre = os.path.basename(ruta)
        self.es_pdf = ruta.endswith(".pdf")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(5)

        # Ícono
        icono = QLabel("📕" if self.es_pdf else "📝")
        icono.setStyleSheet("border: none; font-size: 13px;")
        icono.setFixedWidth(18)

        # Info
        info = QVBoxLayout()
        info.setSpacing(0)
        nombre_label = QLabel(self.nombre[:25] + "..." if len(self.nombre) > 25 else self.nombre)
        nombre_label.setStyleSheet("color: white; font-size: 10px; font-weight: bold; border: none;")
        tipo_label = QLabel("PDF · abierto" if self.es_pdf else "Word · abierto")
        tipo_label.setStyleSheet("color: #E1AD01; font-size: 9px; border: none;")
        info.addWidget(nombre_label)
        info.addWidget(tipo_label)

        # Botón reabrir
        btn_reabrir = QPushButton("▶")
        btn_reabrir.setFixedSize(20, 20)
        btn_reabrir.setStyleSheet("background: transparent; color: #00A3FF; border: none; font-size: 12px;")
        btn_reabrir.clicked.connect(self.reabrir)

        # Botón cerrar
        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(16, 16)
        btn_cerrar.setStyleSheet("background: transparent; color: #555; border: none; font-size: 10px;")
        btn_cerrar.clicked.connect(self.cerrar)

        layout.addWidget(icono)
        layout.addLayout(info)
        layout.addStretch()
        layout.addWidget(btn_reabrir)
        layout.addWidget(btn_cerrar)

        self.setStyleSheet("""
            PestanaArchivo {
                background: #161B22;
                border: 0.5px solid #E1AD01;
                border-radius: 5px;
            }
        """)
        self.setFixedHeight(40)

    def reabrir(self):
        os.startfile(self.ruta)

    def cerrar(self):
        self.parent_app.cerrar_pestana_archivo(self)

class PestañaNavegador(QWidget):
    def __init__(self, perfil, parent=None, url="https://www.google.com"):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_page = MiPaginaWeb(perfil, parent)
        self.browser = QWebEngineView()
        self.browser.setPage(self.web_page)
        self.browser.settings().setAttribute(
            self.browser.settings().WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.browser.settings().setAttribute(
            self.browser.settings().WebAttribute.LocalStorageEnabled, True)
        self.browser.setUrl(QUrl(url))
        layout.addWidget(self.browser)


class MiPaginaWeb(QWebEnginePage):
    def createWindow(self, _type):
        # Guardamos la URL actual antes de que cambie
        self._url_anterior = self.url()
        # Conectamos una sola vez para volver cuando termine
        self.loadFinished.connect(self._volver_url_anterior)
        return self

    def _volver_url_anterior(self, ok):
        # Desconectamos para no repetir en cada carga
        self.loadFinished.disconnect(self._volver_url_anterior)
        # Volvemos a la página donde estábamos
        if hasattr(self, '_url_anterior'):
            self.setUrl(self._url_anterior)

class PanelDescargas(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.setFixedWidth(300)
        self.setStyleSheet("""
            background: #161B22;
            border-left: 1px solid #30363D;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("background: #1C2128; border-bottom: 1px solid #30363D;")
        header.setFixedHeight(45)
        header_layout = QHBoxLayout(header)
        titulo = QLabel("Descargas")
        titulo.setStyleSheet("color: white; font-weight: bold; font-size: 13px; border: none;")
        btn_abrir_carpeta = QPushButton("📂 Ver todas")
        btn_abrir_carpeta.setStyleSheet("""
            QPushButton {
                background: #21262d; color: #00A3FF;
                border: 1px solid #30363D; border-radius: 4px;
                font-size: 11px; padding: 4px 8px;
            }
            QPushButton:hover { background: #00A3FF; color: white; }
        """)
        btn_abrir_carpeta.clicked.connect(lambda: self.parent_app.abrir_explorador_descargas())
        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(25, 25)
        btn_cerrar.setStyleSheet("background: transparent; color: #8B949E; border: none; font-size: 13px;")
        btn_cerrar.clicked.connect(lambda: self.parent_app.cerrar_panel_descargas())
        header_layout.addWidget(titulo)
        header_layout.addStretch()
        header_layout.addWidget(btn_abrir_carpeta)
        header_layout.addWidget(btn_cerrar)
        layout.addWidget(header)

        # Lista de archivos
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        self.contenedor = QWidget()
        self.contenedor.setStyleSheet("background: transparent;")
        self.lista_layout = QVBoxLayout(self.contenedor)
        self.lista_layout.setContentsMargins(8, 8, 8, 8)
        self.lista_layout.setSpacing(6)
        self.lista_layout.addStretch()
        self.scroll.setWidget(self.contenedor)
        layout.addWidget(self.scroll)

        self.cargar_archivos()

    def cargar_archivos(self):
        # Limpiar lista
        while self.lista_layout.count() > 1:
            item = self.lista_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
        archivos = [f for f in os.listdir(carpeta) if f.endswith((".docx", ".pdf"))]
        archivos_ordenados = sorted(
            archivos,
            key=lambda x: os.path.getmtime(os.path.join(carpeta, x)),
            reverse=True
        )[:15]  # Mostrar solo los 15 más recientes

        for arc in archivos_ordenados:
            ruta = os.path.join(carpeta, arc)
            tamanio = os.path.getsize(ruta) // 1024
            es_docx = arc.endswith(".docx")

            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #1C2128;
                    border: 1px solid #30363D;
                    border-radius: 6px;
                }
                QFrame:hover { border: 1px solid #00A3FF; }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(8)

            # Ícono
            icono = QLabel("W" if es_docx else "P")
            icono.setFixedSize(36, 36)
            icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icono.setStyleSheet(f"""
                background: {'#185FA5' if es_docx else '#A32D2D'};
                color: {'#E6F1FB' if es_docx else '#FCEBEB'};
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                border: none;
            """)

            # Info
            info = QVBoxLayout()
            nombre_label = QLabel(arc[:30] + "..." if len(arc) > 30 else arc)
            nombre_label.setStyleSheet("color: white; font-size: 11px; font-weight: bold; border: none;")
            size_label = QLabel(f"{tamanio} KB")
            size_label.setStyleSheet("color: #8B949E; font-size: 10px; border: none;")
            info.addWidget(nombre_label)
            info.addWidget(size_label)

            # Botón abrir
            btn = QPushButton("↗")
            btn.setFixedSize(24, 24)
            btn.setStyleSheet("background: transparent; color: #00A3FF; border: none; font-size: 14px;")
            btn.clicked.connect(lambda _, r=ruta: os.startfile(r))

            card_layout.addWidget(icono)
            card_layout.addLayout(info)
            card_layout.addStretch()
            card_layout.addWidget(btn)

            self.lista_layout.insertWidget(self.lista_layout.count() - 1, card)

class ExploradorDescargas(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
        self.setWindowTitle("Explorador de Descargas")
        self.setFixedSize(750, 500)
        self.setStyleSheet("background: #0D1117; color: white;")

        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        titulo = QLabel("📥 Explorador de Descargas")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #00A3FF;")
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar archivo...")
        self.buscador.setStyleSheet("background: #161B22; color: white; border: 1px solid #30363D; padding: 5px; border-radius: 4px;")
        self.buscador.textChanged.connect(self.cargar_archivos)
        header.addWidget(titulo)
        header.addStretch()
        header.addWidget(self.buscador)
        layout.addLayout(header)

        # Tabla de archivos
        self.tabla = QTreeWidget()
        self.tabla.setHeaderLabels(["Nombre", "Tipo", "Tamaño", "Fecha"])
        self.tabla.setColumnWidth(0, 320)
        self.tabla.setColumnWidth(1, 60)
        self.tabla.setColumnWidth(2, 80)
        self.tabla.setColumnWidth(3, 150)
        self.tabla.setStyleSheet("""
            QTreeWidget {
                background: #161B22; color: white;
                border: 1px solid #30363D; border-radius: 6px;
            }
            QTreeWidget::item:hover { background: #1C2128; }
            QTreeWidget::item:selected { background: #00A3FF; color: white; }
            QHeaderView::section {
                background: #1C2128; color: #8B949E;
                border: none; padding: 5px; font-weight: bold;
            }
        """)
        self.tabla.itemDoubleClicked.connect(self.abrir_archivo)
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.menu_contextual)
        layout.addWidget(self.tabla)

        # Botones inferiores
        btn_layout = QHBoxLayout()
        btn_abrir = QPushButton("↗ Abrir")
        btn_mover = QPushButton("📁 Mover al semestre")
        btn_renombrar = QPushButton("✏️ Renombrar")
        btn_eliminar = QPushButton("🗑️ Eliminar")

        for btn, color in [(btn_abrir, "#238636"), (btn_mover, "#1F6FEB"),
                           (btn_renombrar, "#E1AD01"), (btn_eliminar, "#C0392B")]:
            btn.setStyleSheet(f"background: {color}; color: white; padding: 8px 16px; border-radius: 5px; font-weight: bold;")
            btn_layout.addWidget(btn)

        btn_abrir.clicked.connect(self.abrir_archivo)
        btn_mover.clicked.connect(self.mover_archivo)
        btn_renombrar.clicked.connect(self.renombrar_archivo)
        btn_eliminar.clicked.connect(self.eliminar_archivo)
        layout.addLayout(btn_layout)

        self.cargar_archivos()

    def cargar_archivos(self):
        self.tabla.clear()
        query = self.buscador.text().lower() if hasattr(self, 'buscador') else ""
        archivos = [f for f in os.listdir(self.carpeta)
                    if f.endswith((".docx", ".pdf")) and query in f.lower()]
        archivos_ordenados = sorted(
            archivos,
            key=lambda x: os.path.getmtime(os.path.join(self.carpeta, x)),
            reverse=True
        )
        for arc in archivos_ordenados:
            ruta = os.path.join(self.carpeta, arc)
            tamanio = f"{os.path.getsize(ruta) // 1024} KB"
            tipo = "DOCX" if arc.endswith(".docx") else "PDF"
            fecha = datetime.fromtimestamp(os.path.getmtime(ruta)).strftime('%d/%m/%Y %H:%M')
            item = QTreeWidgetItem([arc, tipo, tamanio, fecha])
            self.tabla.addTopLevelItem(item)

    def get_archivo_seleccionado(self):
        item = self.tabla.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecciona un archivo primero.")
            return None, None
        return item.text(0), os.path.join(self.carpeta, item.text(0))

    def abrir_archivo(self):
        nombre, ruta = self.get_archivo_seleccionado()
        if ruta: os.startfile(ruta)

    def eliminar_archivo(self):
        nombre, ruta = self.get_archivo_seleccionado()
        if not ruta: return
        confirmar = QMessageBox.question(self, "Eliminar", f"¿Eliminar {nombre}?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirmar == QMessageBox.StandardButton.Yes:
            os.remove(ruta)
            self.cargar_archivos()
            self.parent_app.actualizar_arbol()

    def renombrar_archivo(self):
        nombre, ruta = self.get_archivo_seleccionado()
        if not ruta: return
        nuevo, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=nombre)
        if ok and nuevo:
            if not nuevo.endswith((".docx", ".pdf")):
                nuevo += ".docx" if nombre.endswith(".docx") else ".pdf"
            os.rename(ruta, os.path.join(self.carpeta, nuevo))
            self.cargar_archivos()
            self.parent_app.actualizar_arbol()

    def mover_archivo(self):
        nombre, ruta = self.get_archivo_seleccionado()
        if not ruta: return

        # Seleccionar semestre y materia
        semestres = self.parent_app.obtener_semestres_raiz()
        sem, ok1 = QInputDialog.getItem(self, "Mover archivo", "Selecciona el semestre:", semestres, 0, False)
        if not ok1: return

        materias = [m for m in os.listdir(os.path.join(PATH_RAIZ, sem))
                    if os.path.isdir(os.path.join(PATH_RAIZ, sem, m)) and m != "Plantillas"]
        mat, ok2 = QInputDialog.getItem(self, "Mover archivo", "Selecciona la materia:", materias, 0, False)
        if not ok2: return

        destino = os.path.join(PATH_RAIZ, sem, mat, nombre)
        shutil.move(ruta, destino)
        self.cargar_archivos()
        self.parent_app.actualizar_arbol()
        QMessageBox.information(self, "Éxito", f"Archivo movido a {sem} → {mat}")

    def menu_contextual(self, pos):
        menu = QMenu()
        menu.setStyleSheet("QMenu { background: #161B22; color: white; border: 1px solid #30363D; } QMenu::item:selected { background: #00A3FF; }")
        menu.addAction("↗ Abrir").triggered.connect(self.abrir_archivo)
        menu.addAction("📁 Mover").triggered.connect(self.mover_archivo)
        menu.addAction("✏️ Renombrar").triggered.connect(self.renombrar_archivo)
        menu.addAction("🗑️ Eliminar").triggered.connect(self.eliminar_archivo)
        menu.exec(self.tabla.viewport().mapToGlobal(pos))

#-------------------------------------------------------------------------------
class AsmoRootApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AsmoRoot - Academic Management System v13.7")
        self.resize(1350, 950)

        # Colores Identitarios
        self.azul_pro = "#00A3FF"
        self.fondo_dark = "#0D1117"
        self.fondo_card = "#161B22"
        self.rojo_alert = "#C0392B"
        self.verde_ok = "#27AE60"
        self.gris_borde = "#30363D"

        self.archivo_docx_sesion = ""
        self.archivo_pdf_sesion = ""
        self.version_sistema = "v1.15.4"

        self.cargar_config()
        self.init_ui()
        self.actualizar_arbol()
        self.cargar_ultima_sesion()

    def cargar_config(self):
        if not os.path.exists(PATH_RAIZ): os.makedirs(PATH_RAIZ)
        if os.path.exists(ARCHIVO_CONFIG):
            with open(ARCHIVO_CONFIG, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {"semestres": {}, "ultimo_semestre": "", "ultima_materia": ""}
            self.guardar_config()

    def guardar_config(self):
        with open(ARCHIVO_CONFIG, 'w') as f: json.dump(self.config, f, indent=4)

    def init_ui(self):
        # Widget Central
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- SIDEBAR IZQUIERDA ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet(f"""
            background-color: {self.fondo_dark}; 
            border-right: 1px solid {self.gris_borde};
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)

        # Logo
        self.logo_label = QLabel()
        if os.path.exists(PATH_LOGO):
            pix = QPixmap(PATH_LOGO).scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.logo_label)

        # AGREGA ESTO justo después del logo:
        self.nombre_label = QLabel("AsmoRoot - Academic Management System")
        self.nombre_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nombre_label.setStyleSheet(
            "color: #27AE60; font-size: 11px; border: none; margin-bottom: 5px;")
        sidebar_layout.addWidget(self.nombre_label)

        self.ver_label = QLabel(f"{self.version_sistema}")
        self.ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ver_label.setStyleSheet("color: #27AE60; font-size: 11px; border: none; margin-bottom: 5px;")
        sidebar_layout.addWidget(self.ver_label)

        # Botón Actualizar
        self.btn_refresh = QPushButton("  ACTUALIZAR SISTEMA")
        self.btn_refresh.setStyleSheet("background: #1F2937; color: white; padding: 8px; border-radius: 4px;")
        self.btn_refresh.clicked.connect(self.actualizar_arbol)
        sidebar_layout.addWidget(self.btn_refresh)

        # Buscador
        sidebar_layout.addWidget(QLabel("🔍 BUSCAR ARCHIVO"))
        self.search_ent = QLineEdit()
        self.search_ent.setPlaceholderText("Filtrar...")
        self.search_ent.setStyleSheet(
            f"background: {self.fondo_card}; color: white; border: 1px solid {self.gris_borde}; padding: 5px;")
        self.search_ent.textChanged.connect(self.actualizar_arbol)
        sidebar_layout.addWidget(self.search_ent)

        # ÁREA DE SCROLL ESTILIZADA
        self.scroll_tree = QScrollArea()
        self.scroll_tree.setWidgetResizable(True)
        self.scroll_tree.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {self.fondo_dark};
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #30363D;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar:horizontal {{
                background: {self.fondo_dark};
                height: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: #30363D;
                min-width: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line, QScrollBar::sub-line {{ border: none; background: none; }}
        """)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, self.tree.header().ResizeMode.ResizeToContents)
        self.tree.setStyleSheet("QTreeWidget { background: transparent; border: none; color: white; }")
        self.tree.itemClicked.connect(self.seleccionar_desde_arbol)
        self.tree.itemDoubleClicked.connect(self.abrir_archivo_desde_arbol)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.mostrar_menu_contextual)

        # ACTIVAR ARRASTRE
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)  # Solo para sacar archivos
        self.tree.startDrag = self.iniciar_arrastre  #


        self.scroll_tree.setWidget(self.tree)
        sidebar_layout.addWidget(self.scroll_tree)

        self.zona_archivos_label = QLabel("ARCHIVOS ABIERTOS")
        self.zona_archivos_label.setStyleSheet(
            "color: #8B949E; font-size: 9px; letter-spacing: 1px; padding: 4px 0px 2px 0px; border: none;")
        self.zona_archivos_label.hide()

        # Widget interno con layout
        self.zona_archivos_widget = QWidget()
        self.zona_archivos_widget.setStyleSheet("background: transparent;")
        self.zona_archivos = QVBoxLayout(self.zona_archivos_widget)
        self.zona_archivos.setSpacing(4)
        self.zona_archivos.setContentsMargins(0, 0, 0, 4)

        # ScrollArea que lo contiene
        self.zona_archivos_scroll = QScrollArea()
        self.zona_archivos_scroll.setWidget(self.zona_archivos_widget)
        self.zona_archivos_scroll.setWidgetResizable(True)
        self.zona_archivos_scroll.setMaximumHeight(160)  # Máximo 4 pestañas visibles
        self.zona_archivos_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #0D1117; width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #30363D; border-radius: 3px;
            }
            QScrollBar::add-line, QScrollBar::sub-line { border: none; background: none; }
        """)
        self.zona_archivos_scroll.hide()

        sidebar_layout.addWidget(self.zona_archivos_label)
        sidebar_layout.addWidget(self.zona_archivos_scroll)

        # Nuevo Semestre
        self.btn_new_sem = QPushButton("+ NUEVO SEMESTRE")
        self.btn_new_sem.setStyleSheet(
            f"background: {self.azul_pro}; color: white; font-weight: bold; padding: 12px; border-radius: 6px; margin: 5px 0px;")
        self.btn_new_sem.clicked.connect(self.crear_nuevo_semestre)
        sidebar_layout.addWidget(self.btn_new_sem)

        # Barra de Estado (Ubicada al final)
        bottom_bar = QHBoxLayout()

        self.status_bar_label = QLabel("")
        self.status_bar_label.setStyleSheet(
            f"color: #27AE60; font-size: 11px; padding: 5px; border-top: 1px solid {self.gris_borde};")
        bottom_bar.addWidget(self.status_bar_label)
        sidebar_layout.addLayout(bottom_bar)

        self.main_layout.addWidget(self.sidebar)

        # --- CONTENIDO CENTRAL (SCROLLABLE) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #010409;")
        self.content_layout = QVBoxLayout(self.content_widget)

        titulo_main = QLabel("CENTRO DE GESTIÓN ACADÉMICA")
        titulo_main.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        titulo_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(titulo_main)

        self.mid_layout = QHBoxLayout()
        col_datos = QVBoxLayout()

        self.card_inputs = QFrame()
        self.card_inputs.setStyleSheet(
            f"background: {self.fondo_card}; border: 1px solid {self.gris_borde}; border-radius: 12px;")
        form_layout = QVBoxLayout(self.card_inputs)

        self.sem_menu = QComboBox()
        self.sem_menu.addItems(self.obtener_semestres_raiz())
        self.sem_menu.currentTextChanged.connect(self.actualizar_materias)

        self.mat_menu = QComboBox()
        self.mat_menu.currentTextChanged.connect(self.guardar_materia_seleccionada)

        self.sem_ent = QLineEdit()
        self.sem_ent.setPlaceholderText("Ej: Semana 10")

        self.tema_ent = QLineEdit()
        self.tema_ent.setPlaceholderText("Escriba el título de la tarea...")

        for lab, wid in [("SELECCIONE EL SEMESTRE:", self.sem_menu), ("SELECCIONE LA MATERIA:", self.mat_menu),
                         ("SEMANA DE TRABAJO:", self.sem_ent), ("TEMA DE LA TAREA:", self.tema_ent)]:
            l = QLabel(lab)
            l.setStyleSheet("color: #8B949E; font-weight: bold; border: none;")
            form_layout.addWidget(l)
            wid.setStyleSheet("background: #0D1117; color: white; padding: 12px; border: 1px solid #30363D;")
            wid.setFixedHeight(40)
            form_layout.addWidget(wid)

        col_datos.addWidget(self.card_inputs)

        self.fix_box = QFrame()
        self.fix_box.setStyleSheet(f"background: #1C2128; border: 1px solid {self.gris_borde}; border-radius: 12px;")
        fix_layout = QVBoxLayout(self.fix_box)

        header_fix = QHBoxLayout()
        title_fix = QLabel("MODO DE RECUPERACIÓN / CORRECCIÓN")
        title_fix.setStyleSheet(f"color: {self.azul_pro}; font-weight: bold; border: none;")
        self.status_ind = QLabel("● REPOSO")
        self.status_ind.setStyleSheet("color: gray; font-weight: bold; border: none;")
        header_fix.addWidget(title_fix)
        header_fix.addStretch()
        header_fix.addWidget(self.status_ind)
        fix_layout.addLayout(header_fix)

        btn_fix_layout = QHBoxLayout()
        self.btn_fix_word = QPushButton(" Abrir Word Histórico")
        self.btn_fix_word.setStyleSheet("background: #238636; color: white; padding: 10px; border-radius: 5px;")
        self.btn_fix_word.setEnabled(False)
        self.btn_fix_word.clicked.connect(self.reabrir_word)

        self.btn_fix_pdf = QPushButton(" Actualizar PDF Histórico")
        self.btn_fix_pdf.setStyleSheet("background: #1F6FEB; color: white; padding: 10px; border-radius: 5px;")
        self.btn_fix_pdf.setEnabled(False)
        self.btn_fix_pdf.clicked.connect(self.generar_pdf)

        btn_fix_layout.addWidget(self.btn_fix_word)
        btn_fix_layout.addWidget(self.btn_fix_pdf)
        fix_layout.addLayout(btn_fix_layout)
        col_datos.addWidget(self.fix_box)

        self.mid_layout.addLayout(col_datos, 3)


        col_btns = QVBoxLayout()
        self.btn_start = QPushButton("Iniciar Nueva Tarea")
        self.btn_start.setStyleSheet(
            f"background: {self.azul_pro}; font-weight: bold; font-size: 16px; color: white; border-radius: 8px;")
        self.btn_start.setFixedHeight(60)
        self.btn_start.clicked.connect(self.iniciar_flujo)

        self.btn_pdf_main = QPushButton("Generar PDF")
        self.btn_pdf_main.setStyleSheet("background: #21618C; font-weight: bold; color: white; border-radius: 8px;")
        self.btn_pdf_main.setFixedHeight(60)
        self.btn_pdf_main.clicked.connect(self.generar_pdf)

        self.btn_finalizar = QPushButton("Finalizar")
        self.btn_finalizar.setStyleSheet(
            f"background: {self.rojo_alert}; font-weight: bold; color: white; border-radius: 8px;")
        self.btn_finalizar.setFixedHeight(60)
        self.btn_finalizar.clicked.connect(self.reset_ui)

        col_btns.addWidget(self.btn_start)
        col_btns.addWidget(self.btn_pdf_main)
        col_btns.addWidget(self.btn_finalizar)
        col_btns.addStretch()

        self.mid_layout.addLayout(col_btns, 1)
        self.content_layout.addLayout(self.mid_layout)

        #NAVEGADOR UEA LINEA 270 APROX 319

        # --- NAVEGADOR UEA (MOODLE) ---
        # --- NAVEGADOR CON PESTAÑAS ---
        self.browser_frame = QFrame()
        self.browser_frame.setStyleSheet(
            f"background: {self.fondo_card}; border: 1px solid {self.gris_borde}; border-radius: 8px;")
        browser_vbox = QVBoxLayout(self.browser_frame)
        browser_vbox.setContentsMargins(5, 5, 5, 5)
        browser_vbox.setSpacing(4)

        # --- BARRA DE PESTAÑAS ---
        tabs_bar = QHBoxLayout()
        tabs_bar.setSpacing(4)

        self.tabs_container = QHBoxLayout()
        self.tabs_container.setSpacing(4)
        self.tabs_container.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinimumSize)
        self.pestanas = []  # lista de (btn_tab, PestañaNavegador)

        btn_nueva = QPushButton("+")
        btn_nueva.setFixedSize(30, 28)
        btn_nueva.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nueva.setStyleSheet(f"""
            QPushButton {{
                background: #21262d; color: white;
                border: 1px solid {self.gris_borde}; border-radius: 4px;
                font-size: 16px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {self.azul_pro}; }}
        """)
        btn_nueva.clicked.connect(lambda: self.nueva_pestana())

        tabs_bar.addLayout(self.tabs_container)
        tabs_bar.addWidget(btn_nueva)
        tabs_bar.addStretch()
        browser_vbox.addLayout(tabs_bar)

        # --- BARRA DE NAVEGACIÓN ---
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(4)

        self.btn_atras = QPushButton("⬅")
        self.btn_adelante = QPushButton("➡")
        self.btn_recargar = QPushButton("🔄")

        for btn in [self.btn_atras, self.btn_adelante, self.btn_recargar]:
            btn.setFixedSize(35, 30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #21262d; color: white;
                    border: 1px solid {self.gris_borde}; border-radius: 4px;
                }}
                QPushButton:hover {{ background: {self.azul_pro}; }}
            """)

        self.btn_atras.clicked.connect(lambda: self.browser_actual().back())
        self.btn_adelante.clicked.connect(lambda: self.browser_actual().forward())
        self.btn_recargar.clicked.connect(lambda: self.browser_actual().reload())

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Buscar en Google o ingresar URL...")
        self.url_bar.setStyleSheet(f"""
            background: #0D1117; color: white;
            border: 1px solid {self.gris_borde}; border-radius: 4px; padding: 5px;
        """)
        self.url_bar.setFixedHeight(30)
        self.url_bar.returnPressed.connect(self.navegar_url)

        self.btn_descargas_nav = QPushButton("⬇️ 0")
        self.btn_descargas_nav.setFixedSize(55, 30)
        self.btn_descargas_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_descargas_nav.setStyleSheet(f"""
            QPushButton {{
                background: #21262d; color: {self.azul_pro};
                border: 1px solid {self.gris_borde}; border-radius: 4px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {self.azul_pro}; color: white; }}
        """)
        self.contador_descargas = 0
        self.btn_descargas_nav.clicked.connect(self.toggle_panel_descargas)

        nav_bar.addWidget(self.btn_atras)
        nav_bar.addWidget(self.btn_adelante)
        nav_bar.addWidget(self.btn_recargar)
        nav_bar.addWidget(self.url_bar)
        nav_bar.addWidget(self.btn_descargas_nav)
        browser_vbox.addLayout(nav_bar)

        # --- STACK DE NAVEGADORES ---
        self.stack_browsers = QVBoxLayout()
        browser_vbox.addLayout(self.stack_browsers)

        # Configurar perfil persistente
        self.perfil_persistente = QWebEngineProfile("Storage_AsmoRoot", self)
        ruta_datos = os.path.join(PATH_RAIZ, "Navegador_Datos")
        self.perfil_persistente.setPersistentStoragePath(ruta_datos)
        self.perfil_persistente.setDownloadPath(os.path.join(os.path.expanduser("~"), "Downloads"))
        self.perfil_persistente.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.perfil_persistente.setHttpAcceptLanguage("es-ES,es;q=0.9")
        self.perfil_persistente.downloadRequested.connect(self.gestionar_descarga)

        # Perfil para Google y otras páginas (guarda sesión de Google)
        self.perfil_google = QWebEngineProfile("Storage_Google", self)
        ruta_google = os.path.join(PATH_RAIZ, "Google_Datos")
        self.perfil_google.setPersistentStoragePath(ruta_google)
        self.perfil_google.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.perfil_google.setHttpAcceptLanguage("es-ES,es;q=0.9")
        self.perfil_google.downloadRequested.connect(self.gestionar_descarga)

        # Crear pestaña UEA por defecto
        self.nueva_pestana(
            url="https://eva.pregrado.uea.edu.ec/eva2526/web/my/courses.php?lang=es",
            titulo="🎓 UEA",
            fija=True
        )

        browser_vbox.setContentsMargins(5, 5, 5, 5)
        self.browser_frame.setFixedHeight(800)
        self.content_layout.addWidget(self.browser_frame)

        self.scroll_area.setWidget(self.content_widget)
        self.panel_descargas = PanelDescargas(self)
        self.panel_descargas.hide()  # ← AGREGAR

        self.main_layout.addWidget(self.scroll_area)  # ← ESTA LA CONSERVAS
        self.main_layout.addWidget(self.panel_descargas)  # ← AGREGAR

    # --- LÓGICA ---
    def obtener_semestres_raiz(self):
        if not os.path.exists(PATH_RAIZ): return []
        return [f for f in os.listdir(PATH_RAIZ) if os.path.isdir(os.path.join(PATH_RAIZ, f)) and f not in ["Logo", "Navegador_Datos", "Google_Datos"]]

    def crear_nuevo_semestre(self):
        semestre, ok1 = QInputDialog.getText(self, "Nuevo Semestre", "Nombre del Semestre:")
        if not ok1 or not semestre: return
        materias_raw, ok2 = QInputDialog.getText(self, "Materias", "Materias separadas por coma:")
        if not ok2 or not materias_raw: return

        ruta_sem = os.path.join(PATH_RAIZ, semestre)
        os.makedirs(os.path.join(ruta_sem, "Plantillas"), exist_ok=True)
        for mat in [m.strip() for m in materias_raw.split(",")]:
            os.makedirs(os.path.join(ruta_sem, mat), exist_ok=True)
            with open(os.path.join(ruta_sem, "Plantillas", f"{mat}.docx"), 'wb') as f: pass

        self.actualizar_arbol()
        self.sem_menu.clear()
        self.sem_menu.addItems(self.obtener_semestres_raiz())

    def actualizar_materias(self, semestre):
        self.mat_menu.clear()
        ruta = os.path.join(PATH_RAIZ, semestre)
        if os.path.exists(ruta):
            mats = sorted([m for m in os.listdir(ruta) if os.path.isdir(os.path.join(ruta, m)) and m != "Plantillas"])
            self.mat_menu.addItems(mats)
            self.config["ultimo_semestre"] = semestre
            self.guardar_config()

    def guardar_materia_seleccionada(self, mat):
        if mat: self.config["ultima_materia"] = mat; self.guardar_config()

    def actualizar_arbol(self):
        self.tree.clear()
        query = self.search_ent.text().lower()

        # --- DICCIONARIO DE ORDEN LÓGICO ---
        orden_semestres = {
            "primer": 1, "1er": 1, "1°": 1,
            "segundo": 2, "2do": 2, "2°": 2,
            "tercer": 3, "3er": 3, "3°": 3,
            "cuarto": 4, "4to": 4, "4°": 4,
            "quinto": 5, "5to": 5, "5°": 5,
            "sexto": 6, "6to": 6, "6°": 6,
            "septimo": 7, "7mo": 7, "7°": 7,
            "octavo": 8, "8vo": 8, "8°": 8,
            "noveno": 9, "9no": 9, "9°": 9,
            "decimo": 10, "10mo": 10, "10°": 10
        }

        def obtener_peso(nombre):
            nombre_min = nombre.lower()
            # Buscamos si alguna palabra clave está en el nombre de la carpeta
            for clave, valor in orden_semestres.items():
                if clave in nombre_min:
                    return valor
            return 99  # Si no coincide, lo manda al final

        # Obtenemos semestres y los ordenamos con la lógica nueva
        semestres_lista = self.obtener_semestres_raiz()
        semestres_ordenados = sorted(semestres_lista, key=obtener_peso)

        for sem in semestres_ordenados:
            sem_node = QTreeWidgetItem([f"📂 {sem}"])
            ruta_sem = os.path.join(PATH_RAIZ, sem)

            # Materias (alfabético está bien aquí)
            materias = sorted([m for m in os.listdir(ruta_sem) if os.path.isdir(os.path.join(ruta_sem, m))])

            for mat in materias:
                mat_node = QTreeWidgetItem([f"📘 {mat}"])
                ruta_mat = os.path.join(ruta_sem, mat)

                # Archivos por tiempo de modificación (el más nuevo arriba)
                archivos = [f for f in os.listdir(ruta_mat) if f.endswith((".docx", ".pdf"))]
                archivos_ordenados = sorted(
                    archivos,
                    key=lambda x: os.path.getmtime(os.path.join(ruta_mat, x)),
                    reverse=True
                )

                for arc in archivos_ordenados:
                    if query in arc.lower() or query in mat.lower():
                        icon = "📝" if arc.endswith(".docx") else "📕"
                        mat_node.addChild(QTreeWidgetItem([f"{icon} {arc}"]))

                if mat_node.childCount() > 0 or query == "":
                    sem_node.addChild(mat_node)

            if sem_node.childCount() > 0:
                self.tree.addTopLevelItem(sem_node)

        # --- NODO ESPECIAL: CARPETA DE DESCARGAS ---
        carpeta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")
        nodo_descargas = QTreeWidgetItem(["⬇️ Descargas"])

        archivos_dl = [f for f in os.listdir(carpeta_descargas)
                       if f.endswith((".docx", ".pdf"))]
        archivos_dl_ordenados = sorted(
            archivos_dl,
            key=lambda x: os.path.getmtime(os.path.join(carpeta_descargas, x)),
            reverse=True
        )

        for arc in archivos_dl_ordenados:
            if query in arc.lower() or query == "":
                icon = "📝" if arc.endswith(".docx") else "📕"
                nodo_descargas.addChild(QTreeWidgetItem([f"{icon} {arc}"]))

        self.tree.addTopLevelItem(nodo_descargas)

    def seleccionar_desde_arbol(self, item):
        if item.parent() and item.parent().parent():
            nombre_arc = item.text(0).split(" ", 1)[-1]
            if not nombre_arc.endswith(".docx"): return
            materia = item.parent().text(0).split(" ", 1)[-1]
            semestre = item.parent().parent().text(0).split(" ", 1)[-1]
            self.sem_menu.setCurrentText(semestre)
            self.mat_menu.setCurrentText(materia)
            self.archivo_docx_sesion = os.path.join(PATH_RAIZ, semestre, materia, nombre_arc)
            self.status_ind.setText("● TAREA DETECTADA")
            self.status_ind.setStyleSheet(f"color: {self.verde_ok}; font-weight: bold;")
            self.btn_fix_word.setEnabled(True);
            self.btn_fix_pdf.setEnabled(True)

    def iniciar_flujo(self):
        try:
            sem, mat, sema, tema = self.sem_menu.currentText(), self.mat_menu.currentText(), self.sem_ent.text(), self.tema_ent.text()
            if not all([mat, sema, tema]): return

            # --- LÓGICA DE GUARDADO MEJORADA ---
            fecha = datetime.now().strftime('%Y-%m-%d')
            # Generar iniciales (omitiendo conectores comunes)
            ini_mat = "".join([p[0].upper() for p in mat.split() if p.lower() not in ["de", "la", "el", "y"]])
            # Extraer solo números de la entrada de semana
            solo_num = "".join(filter(str.isdigit, sema))
            # Construir nombre final
            nombre = f"{fecha}_{tema.replace(' ', '-')}_{ini_mat}_Semana-{solo_num or 'X'}.docx"
            # ------------------------------------

            self.archivo_docx_sesion = os.path.join(PATH_RAIZ, sem, mat, nombre)
            plantilla = os.path.join(PATH_RAIZ, sem, "Plantillas", f"{mat}.docx")
            if os.path.exists(plantilla):
                shutil.copy(plantilla, self.archivo_docx_sesion)
                os.startfile(self.archivo_docx_sesion)
                self.status_ind.setText("● EDITANDO");
                self.status_ind.setStyleSheet("color: #E1AD01; font-weight: bold;")
                self.btn_fix_word.setEnabled(True);
                self.btn_fix_pdf.setEnabled(True);
                self.actualizar_arbol()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def generar_pdf(self):
        if not os.path.exists(self.archivo_docx_sesion): return
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(self.archivo_docx_sesion)
            path_pdf = self.archivo_docx_sesion.replace(".docx", ".pdf")
            doc.SaveAs(path_pdf, FileFormat=17)
            doc.Close();
            word.Quit();
            self.actualizar_arbol()
            QMessageBox.information(self, "Éxito", "PDF Generado.")
            self.status_ind.setText("● TAREA FINALIZADA")
        except:
            QMessageBox.warning(self, "Error", "Fallo al generar PDF.")

    def reabrir_word(self):
        if os.path.exists(self.archivo_docx_sesion): os.startfile(self.archivo_docx_sesion)

    def reset_ui(self):
        self.tema_ent.clear();
        self.sem_ent.clear()
        self.status_ind.setText("● REPOSO");
        self.status_ind.setStyleSheet("color: gray; font-weight: bold;")
        self.btn_fix_word.setEnabled(False);
        self.btn_fix_pdf.setEnabled(False)

    def abrir_archivo_desde_arbol(self, item):
        if item.childCount() == 0:
            nombre_arc = item.text(0).split(" ", 1)[-1]
            padre = item.parent()

            # Si el padre es "Descargas"
            if padre and "Descargas" in padre.text(0):
                carpeta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")
                os.startfile(os.path.join(carpeta_descargas, nombre_arc))
            else:
                # Lógica original
                mat = padre.text(0).split(" ", 1)[-1]
                sem = padre.parent().text(0).split(" ", 1)[-1]
                os.startfile(os.path.join(PATH_RAIZ, sem, mat, nombre_arc))

    def cargar_ultima_sesion(self):
        u_sem = self.config.get("ultimo_semestre", "")
        if u_sem in self.obtener_semestres_raiz():
            self.sem_menu.setCurrentText(u_sem)
            self.actualizar_materias(u_sem)
            self.mat_menu.setCurrentText(self.config.get("ultima_materia", ""))

    def mostrar_menu_contextual(self, posicion):
        item = self.tree.itemAt(posicion)
        if not item: return

        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {self.fondo_card}; color: white; border: 1px solid {self.gris_borde}; }}
            QMenu::item:selected {{ background-color: {self.azul_pro}; }}
        """)

        # Identificar qué es: Semestre (Nivel 0), Materia (Nivel 1), Archivo (Nivel 2)
        accion_renombrar = menu.addAction("✏️ Renombrar")
        accion_borrar = menu.addAction("🗑️ Eliminar")

        accion = menu.exec(self.tree.viewport().mapToGlobal(posicion))

        if accion == accion_renombrar:
            self.gestionar_item_arbol(item, "renombrar")
        elif accion == accion_borrar:
            self.gestionar_item_arbol(item, "borrar")

    def gestionar_item_arbol(self, item, operacion):
        # 1. Construir la ruta dinámica según el nivel
        texto_limpio = item.text(0).split(" ", 1)[-1]

        if not item.parent():  # NIVEL SEMESTRE
            ruta = os.path.join(PATH_RAIZ, texto_limpio)
            tipo = "Semestre"
        elif not item.parent().parent():  # NIVEL MATERIA
            sem = item.parent().text(0).split(" ", 1)[-1]
            ruta = os.path.join(PATH_RAIZ, sem, texto_limpio)
            tipo = "Materia"
        else:  # NIVEL ARCHIVO
            mat = item.parent().text(0).split(" ", 1)[-1]
            sem = item.parent().parent().text(0).split(" ", 1)[-1]
            ruta = os.path.join(PATH_RAIZ, sem, mat, texto_limpio)
            tipo = "Archivo"

        # 2. Ejecutar la operación
        if operacion == "renombrar":
            nuevo_nombre, ok = QInputDialog.getText(self, f"Renombrar {tipo}", f"Nuevo nombre para {texto_limpio}:",
                                                    text=texto_limpio)
            if ok and nuevo_nombre:
                # Mantener extensiones si es un archivo
                if tipo == "Archivo" and not nuevo_nombre.lower().endswith((".docx", ".pdf")):
                    nuevo_nombre += ".docx" if texto_limpio.endswith(".docx") else ".pdf"

                nueva_ruta = os.path.join(os.path.dirname(ruta), nuevo_nombre)
                try:
                    os.rename(ruta, nueva_ruta)
                    self.actualizar_arbol()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo renombrar: {e}")

        elif operacion == "borrar":
            confirmar = QMessageBox.question(self, "Eliminar",
                                             f"¿Estás seguro de eliminar este {tipo}?\n({texto_limpio})",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirmar == QMessageBox.StandardButton.Yes:
                try:
                    if os.path.isdir(ruta):
                        shutil.rmtree(ruta)  # Borra carpeta y todo su contenido
                    else:
                        os.remove(ruta)  # Borra archivo único
                    self.actualizar_arbol()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")

    def toggle_moodle_fullscreen(self):
        # Verificamos el estado inicial
        if not hasattr(self, 'moodle_maximizado'):
            self.moodle_maximizado = False

        try:
            if not self.moodle_maximizado:
                # 1. OCULTAR TODO CON CUIDADO
                self.sidebar.hide()

                # Ocultar inputs y el cuadro de corrección
                self.card_inputs.hide()
                self.fix_box.hide()

                # Ocultar la columna de botones (iniciar, pdf, finalizar)
                # Como están en col_btns, lo más seguro es ocultar los botones directamente
                self.btn_start.hide()
                self.btn_pdf_main.hide()
                self.btn_finalizar.hide()

                # Ajustar el navegador
                self.browser_frame.setFixedHeight(900)
                self.btn_expandir.setText("⛶")
                self.moodle_maximizado = True

            else:
                # 2. MOSTRAR TODO DE NUEVO
                self.sidebar.show()
                self.card_inputs.show()
                self.fix_box.show()

                self.btn_start.show()
                self.btn_pdf_main.show()
                self.btn_finalizar.show()

                self.browser_frame.setFixedHeight(500)
                self.btn_expandir.setText("⛶")
                self.moodle_maximizado = False

            # Refrescar la interfaz para evitar pantallas negras
            self.content_widget.update()

        except Exception as e:
            print(f"Error al expandir: {e}")



    def iniciar_arrastre(self, supportedActions):
        item = self.tree.currentItem()
        if not item or item.childCount() > 0: return  # No arrastrar carpetas

        # Construir la ruta real del archivo
        texto_arc = item.text(0).split(" ", 1)[-1]
        mat = item.parent().text(0).split(" ", 1)[-1]
        sem = item.parent().parent().text(0).split(" ", 1)[-1]
        ruta_completa = os.path.abspath(os.path.join(PATH_RAIZ, sem, mat, texto_arc))

        if os.path.exists(ruta_completa):
            data = QMimeData()
            # Esto le dice al sistema que es un objeto de tipo archivo
            url = QUrl.fromLocalFile(ruta_completa)
            data.setUrls([url])

            drag = QDrag(self)
            drag.setMimeData(data)

            # Opcional: poner el icono del archivo mientras arrastras
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.transparent)
            drag.setPixmap(pixmap)

            drag.exec(Qt.DropAction.CopyAction)

    def gestionar_descarga(self, download):
        carpeta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")
        nombre_archivo = download.suggestedFileName()
        ruta_final = os.path.join(carpeta_descargas, nombre_archivo)

        # --- LÓGICA DE REEMPLAZO (como Chrome) ---
        if os.path.exists(ruta_final):
            respuesta = QMessageBox.question(
                self,
                "Archivo ya existe",
                f'"{nombre_archivo}" ya existe en Descargas.\n¿Deseas reemplazarlo?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if respuesta == QMessageBox.StandardButton.No:
                # Generar nombre alternativo como Chrome: "archivo (1).docx"
                base, ext = os.path.splitext(nombre_archivo)
                contador = 1
                while os.path.exists(os.path.join(carpeta_descargas, f"{base} ({contador}){ext}")):
                    contador += 1
                nombre_archivo = f"{base} ({contador}){ext}"

        download.setDownloadDirectory(carpeta_descargas)
        download.setDownloadFileName(nombre_archivo)
        download.accept()

        # --- MENSAJE EN BARRA DE ESTADO SIN CONGELAR ---
        self.status_bar_label.setText(f" ⬇️ Descargando: {nombre_archivo}...")

        # Cuando termine, actualizar mensaje y árbol automáticamente
        download.isFinishedChanged.connect(lambda: self._descarga_completada(nombre_archivo))

    def _descarga_completada(self, nombre_archivo):
        self.status_bar_label.setText(f" ✅ Descargado: {nombre_archivo}")
        self.actualizar_arbol()
        # Desaparece a los 4 segundos
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(4000, lambda: self.status_bar_label.setText(""))

    def abrir_archivo_desde_arbol(self, item):
        if item.childCount() == 0:
            nombre_arc = item.text(0).split(" ", 1)[-1]
            padre = item.parent()

            if padre and "Descargas" in padre.text(0):
                carpeta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")
                ruta = os.path.join(carpeta_descargas, nombre_arc)
            else:
                mat = padre.text(0).split(" ", 1)[-1]
                sem = padre.parent().text(0).split(" ", 1)[-1]
                ruta = os.path.join(PATH_RAIZ, sem, mat, nombre_arc)

            os.startfile(ruta)
            # Mensaje al abrir
            self.status_bar_label.setText(f" 📂 Abriendo: {nombre_arc}")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(4000, lambda: self.status_bar_label.setText(""))

    def createWindow(self, window_type):
        # Cuando Moodle intenta abrir en nueva pestaña, lo redirigimos
        # al mismo navegador para que active downloadRequested
        return self.browser.page()

    def navegar_url(self):
        url = self.url_bar.text().strip()
        if not url.startswith("http"):
            url = "https://" + url
        self.browser.setUrl(QUrl(url))

    def toggle_carpeta_descargas(self):
        import subprocess
        carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
        subprocess.Popen(f'explorer "{carpeta}"')

    def _descarga_completada(self, nombre_archivo):
        # Actualizar contador en botón
        self.contador_descargas += 1
        self.btn_descargas_nav.setText(f"⬇️ {self.contador_descargas}")
        self.btn_descargas_nav.setStyleSheet(f"""
            QPushButton {{
                background: #21262d; color: #27AE60;
                border: 1px solid #27AE60; border-radius: 4px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #27AE60; color: white; }}
        """)

    def toggle_panel_descargas(self):
        if self.panel_descargas.isVisible():
            self.cerrar_panel_descargas()
        else:
            self.panel_descargas.cargar_archivos()
            self.panel_descargas.show()

    def cerrar_panel_descargas(self):
        self.panel_descargas.hide()

    def abrir_explorador_descargas(self):
        explorador = ExploradorDescargas(self)
        explorador.exec()

    def browser_actual(self):
        """Devuelve el QWebEngineView de la pestaña activa"""
        for btn, pestana, fija in self.pestanas:
            if btn.property("activa"):
                return pestana.browser
        return self.pestanas[0][1].browser

    def nueva_pestana(self, url=None, titulo="Nueva pestaña", fija=False):
        if url is None:
            url = f"file:///{PATH_RAIZ}/nueva_pestana.html".replace("\\", "/")
        perfil = self.perfil_persistente if "uea.edu.ec" in url else self.perfil_google
        pestana = PestañaNavegador(perfil, self, url)

        # Botón de la pestaña
        btn_tab = QPushButton(titulo)
        btn_tab.setFixedHeight(28)
        btn_tab.setMinimumWidth(60)
        btn_tab.setMaximumWidth(110)
        btn_tab.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_tab.setStyleSheet(f"""
            QPushButton {{
                background: #21262d; color: #8B949E;
                border: 1px solid {self.gris_borde}; border-radius: 4px;
                padding: 0 8px; font-size: 11px; text-align: left;
            }}
        """)

        # Actualizar título cuando cargue
        pestana.browser.titleChanged.connect(lambda t, b=btn_tab, f=fija:
                                             b.setText(("🎓 UEA" if f else t[:20]) if t else "Nueva pestaña"))

        # Actualizar URL bar al cambiar URL
        pestana.browser.urlChanged.connect(lambda url:
                                           self.url_bar.setText(
                                               "" if url.toString().startswith("file:///") else url.toString())
                                           if self.browser_actual() == pestana.browser else None)

        if not fija:
            # Botón cerrar dentro de la pestaña
            btn_cerrar_tab = QPushButton("✕")
            btn_cerrar_tab.setFixedSize(16, 16)
            btn_cerrar_tab.setStyleSheet("background: transparent; color: #8B949E; border: none; font-size: 10px;")
            btn_cerrar_tab.clicked.connect(lambda: self.cerrar_pestana(btn_tab))

            tab_widget = QWidget()
            tab_layout = QHBoxLayout(tab_widget)
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.setSpacing(2)
            tab_layout.addWidget(btn_tab)
            tab_layout.addWidget(btn_cerrar_tab)
            self.tabs_container.addWidget(tab_widget)
        else:
            self.tabs_container.addWidget(btn_tab)

        btn_tab.clicked.connect(lambda: self.cambiar_pestana(btn_tab))
        self.pestanas.append((btn_tab, pestana, fija))

        # Agregar al stack
        self.stack_browsers.addWidget(pestana)
        self.cambiar_pestana(btn_tab)

    def cambiar_pestana(self, btn_activo):
        for btn, pestana, fija in self.pestanas:
            es_activa = btn == btn_activo
            btn.setProperty("activa", es_activa)
            pestana.setVisible(es_activa)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {'#0D1117' if es_activa else '#21262d'};
                    color: {'white' if es_activa else '#8B949E'};
                    border: {'1px solid #00A3FF' if es_activa else f'1px solid {self.gris_borde}'};
                    border-radius: 4px; padding: 0 8px;
                    font-size: 11px; text-align: left;
                }}
            """)
            if es_activa:
                url_str = pestana.browser.url().toString()
                self.url_bar.setText("" if url_str.startswith("file:///") else url_str)

    def cerrar_pestana(self, btn_tab):
        if len(self.pestanas) <= 1:
            return
        for i, (btn, pestana, fija) in enumerate(self.pestanas):
            if btn == btn_tab and not fija:
                self.pestanas.pop(i)
                # Remover widget del tab
                for j in range(self.tabs_container.count()):
                    w = self.tabs_container.itemAt(j).widget()
                    if w and btn_tab in [w] + [w.findChild(QPushButton, "") or w]:
                        self.tabs_container.takeAt(j).widget().deleteLater()
                        break
                pestana.deleteLater()
                # Activar la primera pestaña
                indice_anterior = max(0, i - 1)
                self.cambiar_pestana(self.pestanas[indice_anterior][0])
                break

    def navegar_url(self):
        url = self.url_bar.text().strip()
        if not url.startswith("http"):
            # Si no es URL, buscar en Google
            url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
        self.browser_actual().setUrl(QUrl(url))

    def abrir_archivo_desde_arbol(self, item):
        if item.childCount() == 0:
            nombre_arc = item.text(0).split(" ", 1)[-1]
            padre = item.parent()

            if padre and "Descargas" in padre.text(0):
                carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
                ruta = os.path.join(carpeta, nombre_arc)
            else:
                mat = padre.text(0).split(" ", 1)[-1]
                sem = padre.parent().text(0).split(" ", 1)[-1]
                ruta = os.path.join(PATH_RAIZ, sem, mat, nombre_arc)

            if os.path.exists(ruta):
                # Abrir el editor directamente
                os.startfile(ruta)
                self.status_bar_label.setText(f" 📂 Abriendo: {nombre_arc}")
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(4000, lambda: self.status_bar_label.setText(""))

                # Agregar pestaña si no existe ya
                self._agregar_pestana_archivo(ruta)

    def _agregar_pestana_archivo(self, ruta):
        # Evitar duplicados
        for i in range(self.zona_archivos.count()):
            w = self.zona_archivos.itemAt(i).widget()
            if w and isinstance(w, PestanaArchivo) and w.ruta == ruta:
                return

        pestana = PestanaArchivo(ruta, self)
        self.zona_archivos.addWidget(pestana)
        self.zona_archivos_label.show()
        self.zona_archivos_scroll.show()

        # Monitorear si Word/PDF se cierra
        from PyQt6.QtCore import QTimer
        timer = QTimer(self)
        timer.setInterval(2000)  # Revisar cada 2 segundos

        def verificar_si_cerrado():
            try:
                if ruta.endswith(".docx"):
                    import win32com.client
                    word = win32com.client.GetActiveObject("Word.Application")
                    nombres = [doc.FullName for doc in word.Documents]
                    if os.path.abspath(ruta) not in [os.path.abspath(n) for n in nombres]:
                        timer.stop()
                        self.cerrar_pestana_archivo(pestana)
                elif ruta.endswith(".pdf"):
                    # Buscar si algún proceso tiene el PDF abierto
                    nombre_archivo = os.path.basename(ruta).lower()
                    abierto = False
                    for proc in psutil.process_iter(['name', 'open_files']):
                        try:
                            archivos = proc.open_files()
                            for f in archivos:
                                if nombre_archivo in f.path.lower():
                                    abierto = True
                                    break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                        if abierto:
                            break
                    if not abierto:
                        timer.stop()
                        self.cerrar_pestana_archivo(pestana)
            except:
                if ruta.endswith(".docx"):
                    timer.stop()
                    self.cerrar_pestana_archivo(pestana)

        # Reemplaza todo el bloque del timer por esto:
        monitor = MonitorArchivo(ruta)
        monitor.archivo_cerrado.connect(lambda: self.cerrar_pestana_archivo(pestana))
        monitor.start()
        pestana.monitor = monitor  # Guardar referencia

    def cerrar_pestana_archivo(self, pestana):
        if hasattr(pestana, 'monitor'):
            pestana.monitor.detener()
        self.zona_archivos.removeWidget(pestana)
        pestana.deleteLater()
        if self.zona_archivos.count() == 0:
            self.zona_archivos_label.hide()
            self.zona_archivos_scroll.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AsmoRootApp()
    window.showMaximized()  # ← aquí en vez de show()
    sys.exit(app.exec())