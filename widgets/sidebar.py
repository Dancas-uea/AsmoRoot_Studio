"""
Sidebar - Panel lateral con árbol de archivos, descargas y calendario
"""

import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QTreeWidget, QTreeWidgetItem, QInputDialog,
    QScrollArea, QMessageBox, QMenu, QGraphicsDropShadowEffect, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, QMimeData, QUrl
from PyQt6.QtGui import QIcon, QPixmap, QColor, QDrag, QAction

from styles.helpers import t, label_style, input_style, btn_style
from core.monitor import MonitorArchivo
from widgets.botonesmac_botonluzdia import PestanaArchivo


class Sidebar(QFrame):
    """Panel lateral con árbol de archivos, descargas y calendario."""

    def __init__(self, parent_app, path_raiz, path_logo, version_sistema):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.path_raiz = path_raiz
        self.path_logo = path_logo
        self.version_sistema = version_sistema

        self.sidebar_visible = True

        self.setFixedWidth(230)
        self.setStyleSheet(f"background:{t('sb')};border-right:1px solid {t('brd')};")

        self._setup_ui()
        self._sb_mode("tree")

    def _setup_ui(self):
        """Construye la interfaz del sidebar."""
        self.sidebar_lay = QVBoxLayout(self)
        self.sidebar_lay.setContentsMargins(0, 0, 0, 0)
        self.sidebar_lay.setSpacing(0)

        # Logo
        self._crear_logo()

        # Tabs árbol/descargas
        self._crear_tabs()

        # Árbol frame
        self._crear_arbol_frame()

        # Descargas frame
        self._crear_descargas_frame()

        # Botón nuevo semestre
        self._crear_boton_nuevo_semestre()

        # Calendario
        self._crear_calendario()

        self._sb_mode("tree")

    def _crear_logo(self):
        """Crea la sección del logo."""
        logo_frame = QFrame()
        logo_frame.setFixedHeight(110)
        logo_frame.setStyleSheet(f"border-bottom:1px solid {t('brd')};background:transparent;")
        logo_lay = QVBoxLayout(logo_frame)
        logo_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo_label = QLabel()
        if os.path.exists(self.path_logo):
            pix = QPixmap(self.path_logo).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
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

    def _crear_tabs(self):
        """Crea los tabs para cambiar entre árbol y descargas."""
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

    def _crear_arbol_frame(self):
        """Crea el frame del árbol de archivos."""
        self.sb_tree_frame = QWidget()
        sb_tree_lay = QVBoxLayout(self.sb_tree_frame)
        sb_tree_lay.setContentsMargins(0, 0, 0, 0)
        sb_tree_lay.setSpacing(0)

        # Botón actualizar
        btn_refresh = QPushButton("↻  Actualizar sistema")
        btn_refresh.setFixedHeight(30)
        btn_refresh.setStyleSheet(
            f"background:{t('card')};color:{t('ts')};border:none;border-bottom:1px solid {t('brd')};"
            f"font-size:11px;font-family:'SF Pro Display','Segoe UI',sans-serif;")
        btn_refresh.clicked.connect(lambda: self.parent_app.actualizar_arbol())
        sb_tree_lay.addWidget(btn_refresh)

        # Buscador
        self.search_ent = QLineEdit()
        self.search_ent.setPlaceholderText("🔍  Filtrar archivos…")
        self.search_ent.setFixedHeight(32)
        self.search_ent.setStyleSheet(
            f"QLineEdit{{background:{t('inp')};color:{t('tp')};border:none;"
            f"border-bottom:1px solid {t('brd')};padding:0 12px;font-size:11px;"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;}}")
        self.search_ent.textChanged.connect(lambda: self.parent_app.actualizar_arbol())
        sb_tree_lay.addWidget(self.search_ent)

        # ÁRBOL - CON SCROLL HORIZONTAL
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)

        # Configuración para nombres largos
        self.tree.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree.header().setStretchLastSection(False)

        # CORRECCIÓN: Usar QHeaderView.ResizeMode.ResizeToContents
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

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
            QScrollBar:vertical{{
                background:transparent;
                width:6px;
                border-radius:3px;
            }}
            QScrollBar::handle:vertical{{
                background:rgba(255,255,255,80);
                border-radius:3px;
                min-height:20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{{
                height:0px;
            }}
            QScrollBar:horizontal{{
                background:transparent;
                height:6px;
                border-radius:3px;
            }}
            QScrollBar::handle:horizontal{{
                background:rgba(255,255,255,80);
                border-radius:3px;
                min-width:20px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal{{
                width:0px;
            }}
        """)

        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._mostrar_menu_contextual)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)
        self.tree.startDrag = self._iniciar_arrastre
        sb_tree_lay.addWidget(self.tree, 1)

        # Archivos abiertos
        self._crear_seccion_archivos_abiertos(sb_tree_lay)

        self.sidebar_lay.addWidget(self.sb_tree_frame, 1)

    def _crear_seccion_archivos_abiertos(self, parent_layout):
        """Crea la sección de archivos abiertos en el sidebar."""
        self.zona_archivos_label = QLabel("ARCHIVOS ABIERTOS")
        self.zona_archivos_label.setStyleSheet(
            f"color:{t('tm')};font-size:9px;letter-spacing:1.2px;padding:6px 12px 2px;border:none;"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;")
        self.zona_archivos_label.hide()
        parent_layout.addWidget(self.zona_archivos_label)

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
        parent_layout.addWidget(self.zona_archivos_scroll)

    def _crear_descargas_frame(self):
        """Crea el frame de descargas."""
        self.sb_dl_frame = QWidget()
        self.sb_dl_frame.hide()
        sb_dl_lay = QVBoxLayout(self.sb_dl_frame)
        sb_dl_lay.setContentsMargins(0, 0, 0, 0)
        sb_dl_lay.setSpacing(0)

        # Buscador de descargas
        self.dl_srch = QLineEdit()
        self.dl_srch.setPlaceholderText("🔍  Buscar archivo…")
        self.dl_srch.setFixedHeight(32)
        self.dl_srch.setStyleSheet(
            f"QLineEdit{{background:{t('inp')};color:{t('tp')};border:none;"
            f"border-bottom:1px solid {t('brd')};padding:0 12px;font-size:11px;"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;}}")
        sb_dl_lay.addWidget(self.dl_srch)

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

        self.dl_srch.textChanged.connect(lambda q: self._cargar_dl_sidebar(q))
        self.sidebar_lay.addWidget(self.sb_dl_frame)

    def _crear_boton_nuevo_semestre(self):
        """Crea el botón para crear nuevo semestre."""
        self.btn_new_sem = QPushButton("＋  Nuevo Semestre")
        self.btn_new_sem.setFixedHeight(40)
        self.btn_new_sem.setStyleSheet(
            f"QPushButton{{background:{t('acc')};color:white;border:none;border-radius:0;"
            f"border-top:1px solid {t('brd')};font-size:12px;font-weight:600;"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;}}"
            f"QPushButton:hover{{background:#4a9de0;}}")
        self.btn_new_sem.clicked.connect(lambda: self.parent_app.crear_nuevo_semestre())
        self.sidebar_lay.addWidget(self.btn_new_sem)

    def _crear_calendario(self):
        """Crea el calendario del sidebar."""
        import calendar as cal_mod
        self.sb_calendar_frame = QWidget()
        self.sb_calendar_frame.hide()
        lay = QVBoxLayout(self.sb_calendar_frame)
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
        self.sidebar_lay.addWidget(self.sb_calendar_frame, 1)

    def _sbt_style(self, activo):
        """Estilo para los tabs del sidebar."""
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
        """Cambia entre modo árbol y modo descargas."""
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
        """Carga los archivos de descargas en el sidebar."""
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

            # Acciones
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
        """Mueve un archivo de descargas a un semestre/materia."""
        sems = self.parent_app.obtener_semestres_raiz()
        sem, ok1 = QInputDialog.getItem(self, "Mover", "Semestre:", sems, 0, False)
        if not ok1: return

        mats = [m for m in os.listdir(os.path.join(self.path_raiz, sem))
                if os.path.isdir(os.path.join(self.path_raiz, sem, m)) and m != "Plantillas"]
        mat, ok2 = QInputDialog.getItem(self, "Mover", "Materia:", mats, 0, False)
        if not ok2: return

        shutil.move(ruta, os.path.join(self.path_raiz, sem, mat, nombre))
        self._cargar_dl_sidebar()
        self.parent_app.actualizar_arbol()
        self.parent_app.notificar("gn", "Movido", f"→ {sem} / {mat}")

    def _dl_renombrar(self, ruta, nombre):
        """Renombra un archivo en descargas."""
        nuevo, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=nombre)
        if ok and nuevo:
            if not nuevo.endswith((".docx", ".pdf")):
                nuevo += ".docx" if nombre.endswith(".docx") else ".pdf"
            os.rename(ruta, os.path.join(os.path.dirname(ruta), nuevo))
            self._cargar_dl_sidebar()
            self.parent_app.actualizar_arbol()

    def _dl_eliminar(self, ruta, nombre):
        """Elimina un archivo de descargas."""
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar {nombre}?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            os.remove(ruta)
            self._cargar_dl_sidebar()
            self.parent_app.actualizar_arbol()

    def _on_item_clicked(self, item):
        """Maneja el click en un item del árbol."""
        self.parent_app.seleccionar_desde_arbol(item)

    def _on_item_double_clicked(self, item):
        """Maneja el doble click en un item del árbol."""
        self.parent_app.abrir_archivo_desde_arbol(item)

    def _mostrar_menu_contextual(self, posicion):
        """Muestra el menú contextual del árbol."""
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
            lambda: self.parent_app.gestionar_item_arbol(item, "renombrar"))
        menu.addAction("🗑️  Eliminar").triggered.connect(
            lambda: self.parent_app.gestionar_item_arbol(item, "borrar"))
        menu.exec(self.tree.viewport().mapToGlobal(posicion))

    def _iniciar_arrastre(self, supportedActions):
        """Inicia el arrastre de un archivo desde el árbol."""
        item = self.tree.currentItem()
        if not item or item.childCount() > 0: return

        texto_arc = item.text(0).split("  ", 1)[-1]
        try:
            mat = item.parent().text(0).split("  ", 1)[-1]
            sem = item.parent().parent().text(0).split("  ", 1)[-1]
            ruta = os.path.abspath(os.path.join(self.path_raiz, sem, mat, texto_arc))
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

    # ── Métodos públicos para ser llamados desde main_window ──
    def actualizar_arbol(self, semestres, query=""):
        """Actualiza el árbol con los semestres y archivos."""
        self.tree.clear()

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

        for sem in sorted(semestres, key=peso):
            try:
                sem_node = QTreeWidgetItem([f"📂  {sem}"])
                ruta_sem = os.path.join(self.path_raiz, sem)
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

        # Nodo de descargas
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

    def agregar_pestana_archivo(self, ruta):
        """Agrega una pestaña de archivo abierto."""
        for i in range(self.zona_archivos.count()):
            w = self.zona_archivos.itemAt(i).widget()
            if w and isinstance(w, PestanaArchivo) and w.ruta == ruta:
                return

        pestana = PestanaArchivo(ruta, self.parent_app)
        self.zona_archivos.addWidget(pestana)
        self.zona_archivos_label.show()
        self.zona_archivos_scroll.show()

        monitor = MonitorArchivo(ruta)
        monitor.archivo_cerrado.connect(lambda: self.cerrar_pestana_archivo(pestana))
        monitor.start()
        pestana.monitor = monitor

    def cerrar_pestana_archivo(self, pestana):
        """Cierra una pestaña de archivo abierto."""
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

    def toggle_sidebar(self):
        """Alterna la visibilidad del sidebar."""
        self.sidebar_visible = not self.sidebar_visible
        self.setVisible(self.sidebar_visible)

    def get_search_query(self):
        """Devuelve el texto de búsqueda actual."""
        return self.search_ent.text().lower()

    def show_calendar(self, show):
        """Muestra u oculta el calendario."""
        self.sb_calendar_frame.setVisible(show)

    def hide_descargas_mode(self):
        """Oculta el modo descargas."""
        self._sb_mode("tree")

    def actualizar_descargas(self):
        """Actualiza la lista de descargas."""
        self._cargar_dl_sidebar(self.dl_srch.text() if hasattr(self, 'dl_srch') else "")

    def get_tree(self):
        """Devuelve el widget del árbol."""
        return self.tree