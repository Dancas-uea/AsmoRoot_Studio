import os
import shutil

from PyQt6.QtWidgets import ( QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame, QMessageBox, QInputDialog, QMenu, QStackedWidget
)
from PyQt6.QtCore import (Qt, QUrl, QTimer, QSize, )
from PyQt6.QtGui import (QIcon, QPixmap, QDrag)
from PyQt6.QtCore import QMimeData
import qtawesome as qta

from ui.paneles.panel_uea import PanelUEA
from ui.paneles.panel_gestion import PanelGestion
from ui.paneles.panel_teams import PanelTeams
from ui.paneles.panel_configuracion import PanelConfiguracion
from core.blur_windows import aplicar_blur_windows, aplicar_mica
from core.paths import PATH_RAIZ, PATH_LOGO, PATH_ICO, ARCHIVO_CONFIG, PATH_PNG
from core.config import ConfigManager
from core.utils import generar_icono_profesional
from styles.helpers import t, btn_style, input_style, label_style
from styles.theme import THEME
from widgets.descargas import PanelDescargas, ExploradorDescargas
from widgets.sidebar import Sidebar
from widgets.statusbar import StatusBar
from widgets.botonesmac_botonluzdia import AreaNotificaciones, TitleBar

generar_icono_profesional(PATH_LOGO, PATH_ICO)


class AsmoRootApp(QMainWindow):
    CURRENT_THEME = THEME["dark"]

    def __init__(self):
        super().__init__()
        # ── Solo cambias esta línea para cada release ──
        self.version_sistema = "v2.8"

        self.tema_actual = "dark"
        self.contador_descargas = 0

        self.config_manager = ConfigManager(ARCHIVO_CONFIG, PATH_RAIZ)
        self.config = self.config_manager.config

        self.setWindowTitle("AsmoRoot")
        self.resize(1380, 960)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if os.path.exists(PATH_ICO):
            self.setWindowIcon(QIcon(PATH_ICO))
        elif os.path.exists(PATH_PNG):
            self.setWindowIcon(QIcon(PATH_PNG))

        self._build_ui()
        self.actualizar_arbol()
        self.cargar_ultima_sesion()
        self._aplicar_tema()

    def showEvent(self, e):
        super().showEvent(e)
        hwnd = int(self.winId())
        aplicar_mica(hwnd)
        aplicar_blur_windows(hwnd)

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
        self.btn_tab_uea    = self._make_mtab("  UEA",           "uea",    "mdi.web")
        self.btn_tab_panel  = self._make_mtab("  Gestión",       "panel",  "mdi.folder")
        self.btn_tab_teams  = self._make_mtab("  Teams",         "teams",  "mdi.account-group")
        self.btn_tab_config = self._make_mtab("  Configuración", "config", "mdi.cog")
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

        self.sidebar = Sidebar(self, PATH_RAIZ, PATH_PNG, self.version_sistema)
        self.sidebar_visible = True
        self.body_lay.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.body_lay.addWidget(self.stack, 1)

        self.panel_uea = PanelUEA(self, PATH_RAIZ)
        self.stack.addWidget(self.panel_uea)
        self.panel_uea.btn_sb_tog.clicked.connect(self.toggle_sidebar)
        self.panel_uea.btn_dl_nav.clicked.connect(self.toggle_panel_descargas)

        self.panel_gestion = PanelGestion(self, PATH_RAIZ)
        self.stack.addWidget(self.panel_gestion)

        self.panel_teams = PanelTeams(self)
        self.stack.addWidget(self.panel_teams)

        self.panel_config = PanelConfiguracion(ARCHIVO_CONFIG, self)
        self.stack.addWidget(self.panel_config)

        self.panel_descargas = PanelDescargas(self)
        self.panel_descargas.hide()
        self.body_lay.addWidget(self.panel_descargas)

        self.statusbar = StatusBar(self, self.version_sistema)
        root_lay.addWidget(self.statusbar)

        self.notif_area = AreaNotificaciones(self.root)
        self.notif_area.move(self.root.width() - 320, 60)
        self.notif_area.raise_()

        self._switch_main("uea")

    def _make_mtab(self, texto, tab_id, icon_name=None):
        btn = QPushButton(texto)
        btn.setFixedHeight(30)
        btn.setCheckable(True)
        btn.setObjectName(f"mtab_{tab_id}")
        btn.setStyleSheet(self._mtab_style(False))
        if icon_name:
            try:
                icon = qta.icon(icon_name, color=t('acct'))
                btn.setIcon(icon)
                btn.setIconSize(QSize(18, 18))
            except Exception as e:
                print(f"Error cargando icono {icon_name}: {e}")
        btn.clicked.connect(lambda: self._switch_main(tab_id))
        return btn

    def _switch_main(self, tab_id):
        map_ = {"uea":    (self.btn_tab_uea,    0),
                "panel":  (self.btn_tab_panel,  1),
                "teams":  (self.btn_tab_teams,  2),
                "config": (self.btn_tab_config, 3)}
        for k, (btn, idx) in map_.items():
            btn.setStyleSheet(self._mtab_style(k == tab_id))
        self.stack.setCurrentIndex(map_[tab_id][1])

        if tab_id == "uea":
            self.sidebar.setVisible(self.sidebar_visible)
        else:
            self.sidebar.show()

        if tab_id in ("teams", "config"):
            self.sidebar.sb_tabs.hide()
            self.sidebar.sb_tree_frame.hide()
            self.sidebar.sb_dl_frame.hide()
            self.sidebar.btn_new_sem.hide()
            self.sidebar.sb_calendar_frame.setVisible(tab_id == "teams")
        else:
            self.sidebar.sb_tabs.show()
            self.sidebar.sb_tree_frame.show()
            self.sidebar.btn_new_sem.show()
            self.sidebar.sb_calendar_frame.hide()
            self.sidebar._sb_mode("tree")

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
            f"selection-color:{T['tp']};outline:none;}}"
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

        # ── Actualizar todos los paneles ──────
        if hasattr(self, 'statusbar'):
            self.statusbar.actualizar_tema()
        if hasattr(self, 'panel_gestion'):
            self.panel_gestion.actualizar_tema()
        if hasattr(self, 'panel_teams'):
            self.panel_teams.actualizar_tema()
        if hasattr(self, 'panel_config'):
            self.panel_config.actualizar_tema()

        self.btn_tab_uea.setStyleSheet(self._mtab_style(self.stack.currentIndex() == 0))
        self.btn_tab_panel.setStyleSheet(self._mtab_style(self.stack.currentIndex() == 1))
        self.btn_tab_teams.setStyleSheet(self._mtab_style(self.stack.currentIndex() == 2))
        self.btn_tab_config.setStyleSheet(self._mtab_style(self.stack.currentIndex() == 3))

        hwnd = int(self.winId())
        aplicar_mica(hwnd)
        aplicar_blur_windows(hwnd)

    # ── SIDEBAR TOGGLE ────────────────────────
    def toggle_sidebar(self):
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
        if hasattr(self, 'panel_gestion'):
            self.panel_gestion.actualizar_semestres(self.obtener_semestres_raiz())
        self.notificar("gn", "Semestre creado", sem)

    def actualizar_arbol(self):
        if hasattr(self, 'sidebar'):
            semestres = self.obtener_semestres_raiz()
            query = self.sidebar.get_search_query()
            self.sidebar.actualizar_arbol(semestres, query)

    def cargar_ultima_sesion(self):
        u_sem = self.config_manager.get("ultimo_semestre", "")
        if u_sem in self.obtener_semestres_raiz():
            if hasattr(self, 'panel_gestion'):
                self.panel_gestion.cargar_ultima_sesion(
                    u_sem, self.config_manager.get("ultima_materia", ""))

    # ── ÁRBOL: seleccionar / abrir ─────────────
    def seleccionar_desde_arbol(self, item):
        if item.parent() and item.parent().parent():
            nombre_arc = item.text(0).split("  ", 1)[-1]
            if not nombre_arc.endswith(".docx"):
                return
            materia  = item.parent().text(0).split("  ", 1)[-1]
            semestre = item.parent().parent().text(0).split("  ", 1)[-1]
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
            if "Descargas" in padre.text(0):
                carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
                ruta = os.path.join(carpeta, nombre_arc)
            else:
                if not padre.parent():
                    return
                mat = padre.text(0).split("  ", 1)[-1]
                sem = padre.parent().text(0).split("  ", 1)[-1]
                ruta = os.path.join(PATH_RAIZ, sem, mat, nombre_arc)

            if not os.path.exists(ruta):
                self.notificar("or", "Archivo no encontrado", nombre_arc[:40])
                return

            if ruta.endswith(".docx"):
                try:
                    os.startfile(ruta)
                    self.statusbar.set_mensaje_principal(f"📂 Abriendo: {nombre_arc}")
                    QTimer.singleShot(4000, lambda: self.statusbar.set_mensaje_principal("Sistema listo"))
                    self._agregar_pestana_archivo(ruta)
                    self.notificar("bl", "Word abierto", nombre_arc[:40])
                except Exception as e:
                    self.notificar("rd", "Error al abrir", str(e)[:60])
            elif ruta.endswith(".pdf"):
                try:
                    os.startfile(ruta)
                    self.statusbar.set_mensaje_principal(f"📂 Abriendo: {nombre_arc}")
                    QTimer.singleShot(4000, lambda: self.statusbar.set_mensaje_principal("Sistema listo"))
                    self._agregar_pestana_archivo(ruta)
                except Exception:
                    import subprocess
                    subprocess.Popen(f'start "" "{ruta}"', shell=True)

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
        item = self.sidebar.tree.itemAt(posicion) if hasattr(self.sidebar, 'tree') else None
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
            QMenu::item:selected {{background:{t('accd')};color:{t('tp')};}}
        """)
        menu.addAction("✏️  Renombrar").triggered.connect(
            lambda: self.gestionar_item_arbol(item, "renombrar"))
        menu.addAction("🗑️  Eliminar").triggered.connect(
            lambda: self.gestionar_item_arbol(item, "borrar"))
        menu.exec(self.sidebar.tree.viewport().mapToGlobal(posicion))

    def gestionar_item_arbol(self, item, operacion):
        texto = item.text(0).split("  ", 1)[-1]
        if not item.parent():
            ruta = os.path.join(PATH_RAIZ, texto)
            tipo = "Semestre"
        elif not item.parent().parent():
            sem  = item.parent().text(0).split("  ", 1)[-1]
            ruta = os.path.join(PATH_RAIZ, sem, texto)
            tipo = "Materia"
        else:
            mat  = item.parent().text(0).split("  ", 1)[-1]
            sem  = item.parent().parent().text(0).split("  ", 1)[-1]
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
            if QMessageBox.question(
                self, "Eliminar", f"¿Eliminar {tipo}?\n({texto})",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                try:
                    shutil.rmtree(ruta) if os.path.isdir(ruta) else os.remove(ruta)
                    self.actualizar_arbol()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))

    # ── ARCHIVOS ABIERTOS ──────────────────────
    def _agregar_pestana_archivo(self, ruta):
        if hasattr(self, 'sidebar'):
            self.sidebar.agregar_pestana_archivo(ruta)

    def cerrar_pestana_archivo(self, pestana):
        if hasattr(self, 'sidebar'):
            self.sidebar.cerrar_pestana_archivo(pestana)

    # ── DESCARGAS ─────────────────────────────
    def aumentar_contador_descargas(self):
        self.contador_descargas += 1
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
        item = self.sidebar.tree.currentItem() if hasattr(self.sidebar, 'tree') else None
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

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'notif_area') and hasattr(self, 'root'):
            self.notif_area.move(self.root.width() - 320, 60)