import sys
import os
import json
import shutil
from datetime import datetime
import ctypes
import ctypes.wintypes

import psutil
from PIL import Image

from PyQt6.QtWidgets import (
    QApplication, QDialog, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QFrame,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QInputDialog,
    QScrollArea, QSizeGrip, QFileDialog, QMenu,
    QGraphicsDropShadowEffect, QStackedWidget
)
from PyQt6.QtCore import (Qt, QUrl, QPropertyAnimation, QPoint, QEasingCurve,
                          QThread, pyqtSignal, QTimer, QRect)
from PyQt6.QtGui import (QIcon, QPixmap, QColor, QDrag)
from PyQt6.QtCore import QMimeData
import win32com.client

from ui.paneles.panel_configuracion import PanelConfiguracion
from ui.paneles.panel_uea import PanelUEA
from ui.paneles.panel_teams import PanelTeams
from ui.paneles.panel_gestion import PanelGestion
from core.blur_windows import aplicar_blur_windows, aplicar_mica
from styles.helpers import t, btn_style, input_style, label_style, mac_tooltip

# --Descargas--#
from widgets.descargas import PanelDescargas, ExploradorDescargas

# --core/monitor.py--#
from core.monitor import MonitorArchivo

# --Botones Mac-Pestaña archivo abierto-notificacion--#
from widgets.botonesmac_botonluzdia import MacButton, PestanaArchivo, Notificacion, AreaNotificaciones, TitleBar

# ── Ruta base relativa al .exe (funciona para todos los usuarios) ──
if getattr(sys, 'frozen', False):
    # Corriendo como .exe compilado con PyInstaller
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    # Corriendo como script .py en desarrollo
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_ASMO_CFG_PATH = os.path.join(os.path.expanduser("~"), "AsmoRoot_config.json")
if os.path.exists(_ASMO_CFG_PATH):
    with open(_ASMO_CFG_PATH, 'r', encoding='utf-8') as _f:
        _asmo_cfg = json.load(_f)
    PATH_RAIZ = _asmo_cfg.get("path_raiz", os.path.join(os.path.expanduser("~"), "AsmoRoot"))
else:
    PATH_RAIZ = os.path.join(os.path.expanduser("~"), "AsmoRoot")

# Logo busca primero junto al .exe, luego en la carpeta del proyecto
PATH_LOGO = os.path.join(_BASE_DIR, "logo.ico")
PATH_ICO = os.path.join(_BASE_DIR, "logo.ico")

ARCHIVO_CONFIG = _ASMO_CFG_PATH


def generar_icono_profesional():
    try:
        if os.path.exists(PATH_LOGO):
            img = Image.open(PATH_LOGO)
            img.save(PATH_ICO, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    except Exception as e:
        print(f"Icono error: {e}")


generar_icono_profesional()

# ─────────────────────────────────────────────
#  PALETA macOS dark/light
# ─────────────────────────────────────────────
THEME = {
    "dark": {
        "bg": "#08081a",
        "win": "rgba(13,13,28,200)",
        "sb": "#0b0b18",
        "bar": "#10101e",
        "card": "rgba(255,255,255,10)",
        "cardh": "rgba(255,255,255,22)",
        "inp": "rgba(255,255,255,13)",
        "brd": "rgba(255,255,255,23)",
        "acc": "#378ADD",
        "accd": "rgba(55,138,221,40)",
        "acct": "#85B7EB",
        "tp": "rgba(255,255,255,230)",
        "ts": "rgba(255,255,255,115)",
        "tm": "rgba(255,255,255,56)",
        "grn": "#28c840",
        "red": "#ff5f57",
        "yel": "#febc2e",
        "browserbg": "#0d0d1a",
    },
    "light": {
        "bg": "#c8d4e8",
        "win": "rgba(235,240,255,210)",
        "sb": "#dde4f5",
        "bar": "#d4daf0",
        "card": "rgba(255,255,255,120)",
        "cardh": "rgba(255,255,255,180)",
        "inp": "rgba(255,255,255,150)",
        "brd": "rgba(0,0,0,18)",
        "acc": "#185FA5",
        "accd": "rgba(24,95,165,30)",
        "acct": "#185FA5",
        "tp": "rgba(0,0,0,224)",
        "ts": "rgba(0,0,0,128)",
        "tm": "rgba(0,0,0,76)",
        "grn": "#1a8c30",
        "red": "#d93025",
        "yel": "#c8890a",
        "browserbg": "#f5f6fa",
    }
}


# ─────────────────────────────────────────────
#  APP PRINCIPAL
# ─────────────────────────────────────────────
class AsmoRootApp(QMainWindow):
    CURRENT_THEME = THEME["dark"]

    def __init__(self):
        super().__init__()
        self.version_sistema = "v2.6"
        self.tema_actual = "dark"
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

    def showEvent(self, e):
        super().showEvent(e)
        # Aplicar blur real de Windows al mostrar la ventana
        hwnd = int(self.winId())
        aplicar_mica(hwnd)
        aplicar_blur_windows(hwnd)

    # ── Config ────────────────────────────────
    def cargar_config(self):
        if not os.path.exists(PATH_RAIZ):
            os.makedirs(PATH_RAIZ, exist_ok=True)
        if os.path.exists(ARCHIVO_CONFIG):
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {"semestres": {}, "ultimo_semestre": "", "ultima_materia": ""}
            self.guardar_config()

    def guardar_config(self):
        with open(ARCHIVO_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=4)

    # ── Build UI ──────────────────────────────
    def _build_ui(self):
        self.root = QFrame(self)
        self.root.setObjectName("root_frame")
        self.setCentralWidget(self.root)
        root_lay = QVBoxLayout(self.root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        self.titlebar = TitleBar(self)
        root_lay.addWidget(self.titlebar)

        self.mtabs_bar = QFrame()
        self.mtabs_bar.setFixedHeight(46)
        mtabs_lay = QHBoxLayout(self.mtabs_bar)
        mtabs_lay.setContentsMargins(14, 7, 14, 7)
        mtabs_lay.setSpacing(4)
        self.btn_tab_uea = self._make_mtab("🌐  UEA", "uea")
        self.btn_tab_panel = self._make_mtab("📚  Gestión", "panel")
        self.btn_tab_teams = self._make_mtab("💜  Teams", "teams")
        self.btn_tab_config = self._make_mtab("⚙️  Config", "config")
        mtabs_lay.addWidget(self.btn_tab_uea)
        mtabs_lay.addWidget(self.btn_tab_panel)
        mtabs_lay.addWidget(self.btn_tab_teams)
        mtabs_lay.addWidget(self.btn_tab_config)
        mtabs_lay.addStretch()
        root_lay.addWidget(self.mtabs_bar)

        self.body_widget = QWidget()
        self.body_lay = QHBoxLayout(self.body_widget)
        self.body_lay.setContentsMargins(0, 0, 0, 0)
        self.body_lay.setSpacing(0)
        root_lay.addWidget(self.body_widget, 1)

        self._build_sidebar()

        self.stack = QStackedWidget()
        self.body_lay.addWidget(self.stack, 1)

        # Crear panel UEA (separado)
        self.panel_uea = PanelUEA(self, PATH_RAIZ)
        self.stack.addWidget(self.panel_uea)  # index 0
        self.panel_uea.btn_sb_tog.clicked.connect(self.toggle_sidebar)
        self.panel_uea.btn_dl_nav.clicked.connect(self.toggle_panel_descargas)

        # Panel Gestión (separado) - REEMPLAZAR ESTA LÍNEA
        self.panel_gestion = PanelGestion(self, PATH_RAIZ)
        self.stack.addWidget(self.panel_gestion)  # index 1

        # Panel Teams (separado)
        self.panel_teams = PanelTeams(self)
        self.stack.addWidget(self.panel_teams)  # index 2

        self._build_panel_config()  # index 3

        self.panel_descargas = PanelDescargas(self)
        self.panel_descargas.hide()
        self.body_lay.addWidget(self.panel_descargas)

        self._build_statusbar()
        root_lay.addWidget(self.statusbar_frame)

        self.notif_area = AreaNotificaciones(self.root)
        self.notif_area.move(self.root.width() - 320, 60)
        self.notif_area.raise_()

        self._switch_main("uea")

    def _make_mtab(self, texto, tab_id):
        btn = QPushButton(texto)
        btn.setFixedHeight(30)
        btn.setCheckable(True)
        btn.setObjectName(f"mtab_{tab_id}")
        btn.setStyleSheet(self._mtab_style(False))
        btn.clicked.connect(lambda: self._switch_main(tab_id))
        return btn

    def _switch_main(self, tab_id):
        map_ = {"uea": (self.btn_tab_uea, 0),
                "panel": (self.btn_tab_panel, 1),
                "teams": (self.btn_tab_teams, 2),
                "config": (self.btn_tab_config, 3)}
        for k, (btn, idx) in map_.items():
            btn.setStyleSheet(self._mtab_style(k == tab_id))
        self.stack.setCurrentIndex(map_[tab_id][1])
        # Sidebar: en UEA respeta el estado, en Gestión/Teams siempre visible
        if tab_id == "uea":
            self.sidebar.setVisible(self.sidebar_visible)
        else:
            self.sidebar.show()
        if tab_id in ("teams", "config"):
            self.sb_tabs.hide()
            self.sb_tree_frame.hide()
            self.sb_dl_frame.hide()
            self.btn_new_sem.hide()
            self.sb_calendar_frame.show() if tab_id == "teams" else self.sb_calendar_frame.hide()
        else:
            self.sb_tabs.show()
            self.sb_tree_frame.show()
            self.btn_new_sem.show()
            self.sb_calendar_frame.hide()
            self._sb_mode("tree")

    def _mtab_style(self, activo):
        if activo:
            return (f"QPushButton{{background:{t('accd')};color:{t('acct')};"
                    f"border:1px solid rgba(55,138,221,80);border-radius:8px;"
                    f"padding:0 14px;font-size:12px;font-weight:500;"
                    f"font-family:'SF Pro Display','Segoe UI',sans-serif;}}")
        return (f"QPushButton{{background:transparent;color:{t('tm')};"
                f"border:1px solid transparent;border-radius:8px;padding:0 14px;"
                f"font-size:12px;font-family:'SF Pro Display','Segoe UI',sans-serif;}}"
                f"QPushButton:hover{{background:{t('cardh')};color:{t('tp')};}}")

    # ── SIDEBAR ───────────────────────────────
    def _build_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(230)
        self.sidebar_lay = QVBoxLayout(self.sidebar)
        self.sidebar_lay.setContentsMargins(0, 0, 0, 0)
        self.sidebar_lay.setSpacing(0)
        self.sidebar_visible = True

        # Logo
        logo_frame = QFrame()
        logo_frame.setFixedHeight(110)
        logo_frame.setStyleSheet(f"border-bottom:1px solid {t('brd')};background:transparent;")
        logo_lay = QVBoxLayout(logo_frame)
        logo_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label = QLabel()
        if os.path.exists(PATH_LOGO):
            pix = QPixmap(PATH_LOGO).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText("🎓")
            self.logo_label.setStyleSheet("font-size:30px;")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Sombra en logo
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(55, 138, 221, 100))
        shadow.setOffset(0, 0)
        self.logo_label.setGraphicsEffect(shadow)

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

        # Tabs árbol/descargas
        self.sb_tabs = QFrame()
        self.sb_tabs.setFixedHeight(34)
        self.sb_tabs.setStyleSheet(f"border-bottom:1px solid {t('brd')};background:transparent;")
        st_lay = QHBoxLayout(self.sb_tabs)
        st_lay.setContentsMargins(0, 0, 0, 0)
        st_lay.setSpacing(0)
        self.sbt_tree = QPushButton("Árbol")
        self.sbt_dl = QPushButton("Descargas")
        for b in [self.sbt_tree, self.sbt_dl]:
            b.setStyleSheet(self._sbt_style(False))
            st_lay.addWidget(b)
        self.sbt_tree.clicked.connect(lambda: self._sb_mode("tree"))
        self.sbt_dl.clicked.connect(lambda: self._sb_mode("dl"))
        self.sidebar_lay.addWidget(self.sb_tabs)

        # Árbol frame
        self.sb_tree_frame = QWidget()
        sb_tree_lay = QVBoxLayout(self.sb_tree_frame)
        sb_tree_lay.setContentsMargins(0, 0, 0, 0)
        sb_tree_lay.setSpacing(0)

        btn_refresh = QPushButton("↻  Actualizar sistema")
        btn_refresh.setFixedHeight(30)
        btn_refresh.setStyleSheet(
            f"background:{t('card')};color:{t('ts')};border:none;border-bottom:1px solid {t('brd')};"
            f"font-size:11px;font-family:'SF Pro Display','Segoe UI',sans-serif;")
        btn_refresh.clicked.connect(self.actualizar_arbol)
        sb_tree_lay.addWidget(btn_refresh)

        self.search_ent = QLineEdit()
        self.search_ent.setPlaceholderText("🔍  Filtrar archivos…")
        self.search_ent.setFixedHeight(32)
        self.search_ent.setStyleSheet(
            f"QLineEdit{{background:{t('inp')};color:{t('tp')};border:none;"
            f"border-bottom:1px solid {t('brd')};padding:0 12px;font-size:11px;"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;}}")
        self.search_ent.textChanged.connect(self.actualizar_arbol)
        sb_tree_lay.addWidget(self.search_ent)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background:transparent;border:none;
                color:{t('tp')};font-size:11.5px;
                font-family:'SF Pro Display','Segoe UI',sans-serif;
                outline:none;
            }}
            QTreeWidget::item {{padding:5px 8px;border-radius:7px;margin:1px 4px;}}
            QTreeWidget::item:hover {{background:{t('cardh')};}}
            QTreeWidget::item:selected {{background:{t('accd')};color:{t('acct')};}}
            QScrollBar:vertical{{background:transparent;width:4px;border-radius:2px;}}
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

        self.zona_archivos_label = QLabel("ARCHIVOS ABIERTOS")
        self.zona_archivos_label.setStyleSheet(
            f"color:{t('tm')};font-size:9px;letter-spacing:1.2px;padding:6px 12px 2px;border:none;"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;")
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

        # Descargas frame
        self.sb_dl_frame = QWidget()
        self.sb_dl_frame.hide()
        sb_dl_lay = QVBoxLayout(self.sb_dl_frame)
        sb_dl_lay.setContentsMargins(0, 0, 0, 0)
        sb_dl_lay.setSpacing(0)
        dl_srch = QLineEdit()
        dl_srch.setPlaceholderText("🔍  Buscar archivo…")
        dl_srch.setFixedHeight(32)
        dl_srch.setStyleSheet(
            f"QLineEdit{{background:{t('inp')};color:{t('tp')};border:none;"
            f"border-bottom:1px solid {t('brd')};padding:0 12px;font-size:11px;"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;}}")
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
        dl_scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollBar:vertical{width:3px;background:transparent;}"
            "QScrollBar::handle:vertical{background:rgba(255,255,255,40);border-radius:2px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        sb_dl_lay.addWidget(dl_scroll, 1)
        btn_back = QPushButton("← Volver al árbol")
        btn_back.setFixedHeight(34)
        btn_back.setStyleSheet(
            f"background:{t('card')};color:{t('ts')};border:none;"
            f"border-top:1px solid {t('brd')};font-size:11px;"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;")
        btn_back.clicked.connect(lambda: self._sb_mode("tree"))
        sb_dl_lay.addWidget(btn_back)
        self.sidebar_lay.addWidget(self.sb_dl_frame)
        dl_srch.textChanged.connect(lambda q: self._cargar_dl_sidebar(q))

        # Botón nuevo semestre
        self.btn_new_sem = QPushButton("＋  Nuevo Semestre")
        self.btn_new_sem.setFixedHeight(40)
        self.btn_new_sem.setStyleSheet(
            f"QPushButton{{background:{t('acc')};color:white;border:none;border-radius:0;"
            f"border-top:1px solid {t('brd')};font-size:12px;font-weight:600;"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;}}"
            f"QPushButton:hover{{background:#4a9de0;}}")
        self.btn_new_sem.clicked.connect(self.crear_nuevo_semestre)
        self.sidebar_lay.addWidget(self.btn_new_sem)
        self.sb_calendar_frame = self._build_sidebar_calendar()
        self.sb_calendar_frame.hide()
        self.sidebar_lay.addWidget(self.sb_calendar_frame, 1)
        self.body_lay.addWidget(self.sidebar)
        self._sb_mode("tree")

    def _build_sidebar_calendar(self):
        import calendar as cal_mod
        frame = QWidget()
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 14, 10, 10)
        lay.setSpacing(8)

        ahora = datetime.now()
        meses_es = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

        lbl_mes = QLabel(f"{meses_es[ahora.month]} {ahora.year}")
        lbl_mes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_mes.setStyleSheet(label_style(13, "tp", "600") + "text-decoration:none;background:transparent;")
        lay.addWidget(lbl_mes)

        # Días semana
        dias_row = QHBoxLayout()
        dias_row.setSpacing(2)
        for d in ["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sá"]:
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(28)
            lbl.setStyleSheet(label_style(9, "tm", "600") + "text-decoration:none;background:transparent;")
            dias_row.addWidget(lbl)
        lay.addLayout(dias_row)

        # Grid días
        hoy = ahora.day
        for semana in cal_mod.monthcalendar(ahora.year, ahora.month):
            row = QHBoxLayout()
            row.setSpacing(2)
            for dia in semana:
                if dia == 0:
                    sp = QLabel("")
                    sp.setFixedSize(28, 28)
                    sp.setStyleSheet("background:transparent;border:none;")
                    row.addWidget(sp)
                else:
                    es_hoy = (dia == hoy)
                    es_sabado = (semana.index(dia) == 6)
                    btn = QPushButton(str(dia))
                    btn.setFixedSize(28, 28)
                    if es_hoy:
                        estilo = f"""QPushButton{{
                            background:{t('acc')};color:white;
                            border-radius:14px;border:none;
                            font-size:11px;font-weight:700;
                        }}"""
                    elif es_sabado:
                        estilo = f"""QPushButton{{
                            background:rgba(124,58,237,0.25);color:#a78bfa;
                            border-radius:14px;
                            border:1px solid rgba(124,58,237,0.40);
                            font-size:11px;font-weight:600;
                        }}
                        QPushButton:hover{{background:rgba(124,58,237,0.40);}}"""
                    else:
                        estilo = f"""QPushButton{{
                            background:transparent;color:{t('ts')};
                            border-radius:14px;border:none;font-size:11px;
                        }}
                        QPushButton:hover{{background:{t('cardh')};}}"""
                    btn.setStyleSheet(estilo)
                    row.addWidget(btn)
            lay.addLayout(row)

        lbl_nota = QLabel("💜 Sábados = clases Teams")
        lbl_nota.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_nota.setStyleSheet(label_style(9, "tm") + "text-decoration:none;background:transparent;padding-top:6px;")
        lay.addWidget(lbl_nota)
        lay.addStretch()
        return frame

    def _sbt_style(self, activo):
        if activo:
            return (f"QPushButton{{background:transparent;color:{t('acct')};"
                    f"border:none;border-bottom:2px solid {t('acc')};"
                    f"font-size:11px;font-weight:500;"
                    f"font-family:'SF Pro Display','Segoe UI',sans-serif;padding:0 12px;}}")
        return (f"QPushButton{{background:transparent;color:{t('tm')};"
                f"border:none;border-bottom:2px solid transparent;"
                f"font-size:11px;font-family:'SF Pro Display','Segoe UI',sans-serif;padding:0 12px;}}"
                f"QPushButton:hover{{color:{t('ts')};background:{t('card')};}}")

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
        while self.dl_lista_lay.count() > 1:
            item = self.dl_lista_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(carpeta):
            self.dl_count_lbl.setText("0 archivos")
            return
        archivos = sorted(
            [f for f in os.listdir(carpeta)
             if f.endswith((".docx", ".pdf")) and query.lower() in f.lower()],
            key=lambda x: os.path.getmtime(os.path.join(carpeta, x)), reverse=True
        )[:15]
        self.dl_count_lbl.setText(
            f"{len(archivos)} archivo{'s' if len(archivos) != 1 else ''} · clic para opciones")
        for arc in archivos:
            ruta = os.path.join(carpeta, arc)
            es_docx = arc.endswith(".docx")
            kb = os.path.getsize(ruta) // 1024
            card = QFrame()
            card.setStyleSheet(
                f"QFrame{{background:{t('card')};border:1px solid {t('brd')};border-radius:10px;}}"
                f"QFrame:hover{{border:1px solid {t('acc')};}}")
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
            badge.setStyleSheet(
                f"background:{bg};color:{fg};border-radius:7px;font-weight:700;font-size:10px;border:none;")
            info = QVBoxLayout()
            info.setSpacing(1)
            n = QLabel(arc[:22] + "…" if len(arc) > 22 else arc)
            n.setStyleSheet(label_style(10, "tp", "500"))
            s = QLabel(f"{kb} KB")
            s.setStyleSheet(label_style(9, "tm"))
            info.addWidget(n)
            info.addWidget(s)
            arr = QLabel("▾")
            arr.setStyleSheet(label_style(11, "tm"))
            row_lay.addWidget(badge)
            row_lay.addLayout(info)
            row_lay.addStretch()
            row_lay.addWidget(arr)
            card_lay.addWidget(row)
            actions = QFrame()
            actions.setStyleSheet("background:transparent;border:none;")
            actions.hide()
            act_lay = QHBoxLayout(actions)
            act_lay.setContentsMargins(8, 0, 8, 8)
            act_lay.setSpacing(4)
            for txt, style, fn in [
                ("↗ Abrir",
                 "background:rgba(40,200,64,35);color:#28c840;border:1px solid rgba(40,200,64,50);",
                 lambda _, r=ruta: os.startfile(r)),
                ("📁 Mover",
                 f"background:{t('accd')};color:{t('acct')};border:1px solid rgba(55,138,221,50);",
                 lambda _, r=ruta, a=arc: self._dl_mover(r, a)),
                ("✏️ Renombrar",
                 "background:rgba(254,188,46,35);color:#febc2e;border:1px solid rgba(254,188,46,50);",
                 lambda _, r=ruta, a=arc: self._dl_renombrar(r, a)),
                ("🗑️ Eliminar",
                 "background:rgba(255,95,87,35);color:#ff5f57;border:1px solid rgba(255,95,87,50);",
                 lambda _, r=ruta, a=arc: self._dl_eliminar(r, a)),
            ]:
                b = QPushButton(txt)
                b.setFixedHeight(24)
                b.setStyleSheet(
                    f"QPushButton{{{style}border-radius:6px;font-size:10px;"
                    f"font-family:'SF Pro Display','Segoe UI',sans-serif;padding:0 7px;}}"
                    f"QPushButton:hover{{opacity:0.75;}}")
                b.clicked.connect(fn)
                act_lay.addWidget(b)
            card_lay.addWidget(actions)

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
            os.rename(ruta, os.path.join(os.path.dirname(ruta), nuevo))
            self._cargar_dl_sidebar()
            self.actualizar_arbol()

    def _dl_eliminar(self, ruta, nombre):
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar {nombre}?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            os.remove(ruta)
            self._cargar_dl_sidebar()
            self.actualizar_arbol()

    # ── STATUS BAR ────────────────────────────
    def _build_statusbar(self):
        self.statusbar_frame = QFrame()
        self.statusbar_frame.setFixedHeight(28)
        self.statusbar_frame.setStyleSheet(
            f"background:{t('bar')};border-top:1px solid {t('brd')};")
        sb_lay = QHBoxLayout(self.statusbar_frame)
        sb_lay.setContentsMargins(14, 0, 14, 0)
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

        # Grip nativo de resize — funciona en FramelessWindowHint
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        sb_lay.addWidget(grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

    # ── TEMA ──────────────────────────────────
    def toggle_tema(self):
        self.tema_actual = "light" if self.tema_actual == "dark" else "dark"
        AsmoRootApp.CURRENT_THEME = THEME[self.tema_actual]
        self._aplicar_tema()
        self.titlebar.btn_tema.setText("🌙" if self.tema_actual == "light" else "☀️")

    def _aplicar_tema(self):
        T = AsmoRootApp.CURRENT_THEME
        self.setStyleSheet(
            f"background:{T['bg']};font-family:'SF Pro Display','Segoe UI',sans-serif;"
            f"QComboBox{{background:{T['inp']};color:{T['tp']};border:1px solid {T['brd']};"
            f"border-radius:8px;padding:8px 12px;font-size:12px;}}"
            f"QComboBox QAbstractItemView{{background:{T['sb']};color:{T['tp']};"
            f"border:1px solid {T['brd']};selection-background-color:{T['accd']};"
            f"selection-color:{T['acct']};outline:none;}}"
        )
        self.root.setStyleSheet(f"""
            #root_frame {{
                background: {T['win']};
                border-radius: 14px;
                border: 1px solid {T['brd']};
            }}
        """)
        self.titlebar.setStyleSheet(
            f"background:{T['bar']};border-bottom:1px solid {T['brd']};")
        self.mtabs_bar.setStyleSheet(
            f"background:{T['bar']};border-bottom:1px solid {T['brd']};")
        self.sidebar.setStyleSheet(
            f"background:{T['sb']};border-right:1px solid {T['brd']};")
        self.statusbar_frame.setStyleSheet(
            f"background:{T['bar']};border-top:1px solid {T['brd']};")
        self.btn_tab_uea.setStyleSheet(self._mtab_style(self.stack.currentIndex() == 0))
        self.btn_tab_panel.setStyleSheet(self._mtab_style(self.stack.currentIndex() == 1))

        # Re-aplicar blur al cambiar tema
        hwnd = int(self.winId())
        aplicar_mica(hwnd)
        aplicar_blur_windows(hwnd)

    # ── SIDEBAR TOGGLE ────────────────────────
    def toggle_sidebar(self):
        # Solo funciona en panel UEA
        if self.stack.currentIndex() != 0:
            return
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.setVisible(self.sidebar_visible)

    # ── ÁRBOL ─────────────────────────────────
    def obtener_semestres_raiz(self):
        if not os.path.exists(PATH_RAIZ):
            return []
        return [f for f in os.listdir(PATH_RAIZ)
                if os.path.isdir(os.path.join(PATH_RAIZ, f))
                and f not in ["Logo", "Navegador_Datos", "Google_Datos"]]

    def crear_nuevo_semestre(self):
        from PyQt6.QtWidgets import QDialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Nuevo Semestre")
        dlg.setFixedWidth(420)
        dlg.setStyleSheet(
            f"background:{t('sb')};color:{t('tp')};"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        ttl = QLabel("＋  Crear nuevo semestre")
        ttl.setStyleSheet(label_style(15, "tp", "700"))
        lay.addWidget(ttl)

        lbl1 = QLabel("Nombre del semestre:")
        lbl1.setStyleSheet(label_style(11, "ts", "500"))
        inp_sem = QLineEdit()
        inp_sem.setPlaceholderText("Ej: Quinto Semestre 2025")
        inp_sem.setFixedHeight(38)
        inp_sem.setStyleSheet(input_style())
        lay.addWidget(lbl1)
        lay.addWidget(inp_sem)

        lbl2 = QLabel("Materias (separadas por coma):")
        lbl2.setStyleSheet(label_style(11, "ts", "500"))
        inp_mats = QLineEdit()
        inp_mats.setPlaceholderText("Ej: Matemáticas, Física, Química")
        inp_mats.setFixedHeight(38)
        inp_mats.setStyleSheet(input_style())
        lay.addWidget(lbl2)
        lay.addWidget(inp_mats)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(36)
        btn_cancel.setStyleSheet(btn_style(t('card'), t('ts'), 8, "0 18px"))
        btn_cancel.clicked.connect(dlg.reject)
        btn_ok = QPushButton("✓  Crear semestre")
        btn_ok.setFixedHeight(36)
        btn_ok.setStyleSheet(btn_style(t('acc'), "white", 8, "0 18px"))
        btn_ok.clicked.connect(dlg.accept)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        sem = inp_sem.text().strip()
        mats_raw = inp_mats.text().strip()
        if not sem or not mats_raw:
            return
        ruta_sem = os.path.join(PATH_RAIZ, sem)
        os.makedirs(os.path.join(ruta_sem, "Plantillas"), exist_ok=True)
        for mat in [m.strip() for m in mats_raw.split(",") if m.strip()]:
            os.makedirs(os.path.join(ruta_sem, mat), exist_ok=True)
            with open(os.path.join(ruta_sem, "Plantillas", f"{mat}.docx"), 'wb'): pass
        self.actualizar_arbol()
        self.sem_menu.clear()
        self.sem_menu.addItems(self.obtener_semestres_raiz())
        self.notificar("gn", "Semestre creado", sem)
        if hasattr(self, 'panel_gestion'):
            self.panel_gestion.actualizar_semestres(self.obtener_semestres_raiz())

    def actualizar_arbol(self):
        self.tree.clear()
        query = self.search_ent.text().lower()
        orden = {
            "primer": 1, "1er": 1, "segundo": 2, "2do": 2, "tercer": 3, "3er": 3,
            "cuarto": 4, "4to": 4, "quinto": 5, "5to": 5, "sexto": 6, "6to": 6,
            "septimo": 7, "7mo": 7, "octavo": 8, "8vo": 8, "noveno": 9, "decimo": 10
        }

        def peso(n):
            nl = n.lower()
            for k, v in orden.items():
                if k in nl: return v
            return 99

        for sem in sorted(self.obtener_semestres_raiz(), key=peso):
            try:
                sem_node = QTreeWidgetItem([f"📂  {sem}"])
                ruta_sem = os.path.join(PATH_RAIZ, sem)
                materias = sorted([m for m in os.listdir(ruta_sem)
                                   if os.path.isdir(os.path.join(ruta_sem, m))])
                for mat in materias:
                    try:
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
                    except Exception:
                        pass
                if sem_node.childCount() > 0:
                    self.tree.addTopLevelItem(sem_node)
            except Exception:
                pass

        carpeta_dl = os.path.join(os.path.expanduser("~"), "Downloads")
        nodo_dl = QTreeWidgetItem(["⬇️  Descargas"])
        try:
            if os.path.exists(carpeta_dl):
                for arc in sorted(
                        [f for f in os.listdir(carpeta_dl) if f.endswith((".docx", ".pdf"))],
                        key=lambda x: os.path.getmtime(os.path.join(carpeta_dl, x)), reverse=True):
                    if query in arc.lower() or query == "":
                        icon = "📝" if arc.endswith(".docx") else "📕"
                        nodo_dl.addChild(QTreeWidgetItem([f"{icon}  {arc}"]))
        except Exception:
            pass
        self.tree.addTopLevelItem(nodo_dl)

    def cargar_ultima_sesion(self):
        u_sem = self.config.get("ultimo_semestre", "")
        if u_sem in self.obtener_semestres_raiz():
            if hasattr(self, 'panel_gestion'):
                self.panel_gestion.cargar_ultima_sesion(u_sem, self.config.get("ultima_materia", ""))
    # ── LÓGICA ACADÉMICA ──────────────────────


    # ── ÁRBOL: seleccionar / abrir ─────────────
    # ── ÁRBOL: seleccionar / abrir ─────────────
    def seleccionar_desde_arbol(self, item):
        """Selecciona un archivo desde el árbol."""
        if item.parent() and item.parent().parent():
            nombre_arc = item.text(0).split("  ", 1)[-1]
            if not nombre_arc.endswith(".docx"):
                return
            materia = item.parent().text(0).split("  ", 1)[-1]
            semestre = item.parent().parent().text(0).split("  ", 1)[-1]

            # Delegar al panel gestión
            if hasattr(self, 'panel_gestion'):
                self.panel_gestion.seleccionar_desde_arbol(semestre, materia, nombre_arc)

    def abrir_archivo_desde_arbol(self, item):
        try:
            if item.childCount() > 0:
                return

            nombre_arc = item.text(0).split("  ", 1)[-1]
            padre = item.parent()

            if not padre:
                return

            # Determinar la ruta del archivo
            if "Descargas" in padre.text(0):
                carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
                ruta = os.path.join(carpeta, nombre_arc)
            else:
                if not padre.parent():
                    return
                mat = padre.text(0).split("  ", 1)[-1]
                sem = padre.parent().text(0).split("  ", 1)[-1]
                ruta = os.path.join(PATH_RAIZ, sem, mat, nombre_arc)

            # Verificar que el archivo existe
            if not os.path.exists(ruta):
                self.notificar("or", "Archivo no encontrado", nombre_arc[:40])
                return

            # Para archivos Word
            if ruta.endswith(".docx"):
                try:
                    # Abrir el archivo con el programa asociado
                    os.startfile(ruta)

                    # Actualizar status bar
                    self.sb_lbl.setText(f"📂 Abriendo: {nombre_arc}")
                    QTimer.singleShot(4000, lambda: self.sb_lbl.setText("Sistema listo"))

                    # Agregar a pestañas de archivos abiertos
                    self._agregar_pestana_archivo(ruta)

                    # Notificar
                    self.notificar("bl", "Word abierto", nombre_arc[:40])

                except Exception as e:
                    self.notificar("rd", "Error al abrir", str(e)[:60])
                    print(f"Error abriendo Word: {e}")

            # Para archivos PDF
            elif ruta.endswith(".pdf"):
                try:
                    os.startfile(ruta)
                    self.sb_lbl.setText(f"📂 Abriendo: {nombre_arc}")
                    QTimer.singleShot(4000, lambda: self.sb_lbl.setText("Sistema listo"))
                    self._agregar_pestana_archivo(ruta)
                except Exception:
                    # Fallback con subprocess
                    import subprocess
                    subprocess.Popen(f'start "" "{ruta}"', shell=True)

            # Actualizar el panel gestión si estamos en esa pestaña
            if self.stack.currentIndex() == 1 and ruta.endswith(".docx"):
                try:
                    sem = sem if 'sem' in locals() else ""
                    mat = mat if 'mat' in locals() else ""
                    if sem and mat:
                        self.panel_gestion.seleccionar_desde_arbol(sem, mat, nombre_arc)
                except Exception as e:
                    print(f"Error actualizando panel gestión: {e}")

        except Exception as e:
            print(f"Error general abriendo archivo: {e}")
            self.notificar("rd", "Error", str(e)[:60])

    def mostrar_menu_contextual(self, posicion):
        item = self.tree.itemAt(posicion)
        if not item: return
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background:{t('sb')};color:{t('tp')};
                border:1px solid {t('brd')};border-radius:10px;
                padding:4px;font-size:12px;
                font-family:'SF Pro Display','Segoe UI',sans-serif;
            }}
            QMenu::item {{padding:7px 16px;border-radius:6px;}}
            QMenu::item:selected {{background:{t('accd')};color:{t('acct')};}}
        """)
        menu.addAction("✏️  Renombrar").triggered.connect(
            lambda: self.gestionar_item_arbol(item, "renombrar"))
        menu.addAction("🗑️  Eliminar").triggered.connect(
            lambda: self.gestionar_item_arbol(item, "borrar"))
        menu.exec(self.tree.viewport().mapToGlobal(posicion))

    def actualizar_panel_gestion(self):
        """Actualiza los combobox del panel gestión."""
        if hasattr(self, 'panel_gestion'):
            self.panel_gestion.actualizar_semestres(self.obtener_semestres_raiz())
    def gestionar_item_arbol(self, item, operacion):
        texto = item.text(0).split("  ", 1)[-1]
        if not item.parent():
            ruta = os.path.join(PATH_RAIZ, texto)
            tipo = "Semestre"
        elif not item.parent().parent():
            sem = item.parent().text(0).split("  ", 1)[-1]
            ruta = os.path.join(PATH_RAIZ, sem, texto)
            tipo = "Materia"
        else:
            mat = item.parent().text(0).split("  ", 1)[-1]
            sem = item.parent().parent().text(0).split("  ", 1)[-1]
            ruta = os.path.join(PATH_RAIZ, sem, mat, texto)
            tipo = "Archivo"

        if operacion == "renombrar":
            nuevo, ok = QInputDialog.getText(self, f"Renombrar {tipo}", "Nuevo nombre:", text=texto)
            if ok and nuevo:
                if tipo == "Archivo" and not nuevo.lower().endswith((".docx", ".pdf")):
                    nuevo += ".docx" if texto.endswith(".docx") else ".pdf"
                try:
                    os.rename(ruta, os.path.join(os.path.dirname(ruta), nuevo))
                    self.actualizar_arbol()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
        elif operacion == "borrar":
            if QMessageBox.question(self, "Eliminar", f"¿Eliminar {tipo}?\n({texto})",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                    ) == QMessageBox.StandardButton.Yes:
                try:
                    shutil.rmtree(ruta) if os.path.isdir(ruta) else os.remove(ruta)
                    self.actualizar_arbol()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))

    # ── ARCHIVOS ABIERTOS ──────────────────────
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
        try:
            if hasattr(pestana, 'monitor'):
                pestana.monitor.detener()
            self.zona_archivos.removeWidget(pestana)
            pestana.deleteLater()
            if self.zona_archivos.count() == 0:
                self.zona_archivos_label.hide()
                self.zona_archivos_scroll.hide()
        except Exception as e:
            print(f"Error cerrando pestaña de archivo: {e}")

    def aumentar_contador_descargas(self):
        """Aumenta el contador de descargas y actualiza el panel UEA."""
        self.contador_descargas += 1
        # Actualizar en el panel UEA
        if hasattr(self, 'panel_uea'):
            self.panel_uea.actualizar_contador_descargas(self.contador_descargas)

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

    # ── DRAG & DROP ───────────────────────────
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

    # ── SNAP / RESIZE / TOGGLE ────────────────
    def _toggle_maximized(self):
        if self.windowState() & Qt.WindowState.WindowMaximized:
            self.setWindowState(Qt.WindowState.WindowNoState)
            self.showNormal()
        else:
            self.setWindowState(Qt.WindowState.WindowMaximized)

    # ── PANEL CONFIGURACIÓN ───────────────────
    def _build_panel_config(self):
        CONFIG_PATH = os.path.join(os.path.expanduser("~"), "AsmoRoot_config.json")
        self.panel_config = PanelConfiguracion(CONFIG_PATH, self)
        self.stack.addWidget(self.panel_config)  # index 3


    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'notif_area') and hasattr(self, 'root'):
            self.notif_area.move(self.root.width() - 320, 60)