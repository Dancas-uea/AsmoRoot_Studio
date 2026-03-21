import os
import shutil
from datetime import datetime

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QDialog, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QInputDialog, QMenu, QLineEdit
)
from PyQt6.QtCore import Qt

from config import PATH_RAIZ
from styles.helpers import t, btn_style, label_style

# ─────────────────────────────────────────────
#  PANEL DE DESCARGAS (sidebar)
# ─────────────────────────────────────────────


class PanelDescargas(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.setFixedWidth(290)
        self.setStyleSheet(
            f"PanelDescargas{{background:{t('sb')};border-left:1px solid {t('brd')};}}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        hdr = QFrame()
        hdr.setFixedHeight(44)
        hdr.setStyleSheet(f"background:{t('bar')};border-bottom:1px solid {t('brd')};")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(12, 0, 12, 0)
        ttl = QLabel("⬇  Descargas")
        ttl.setStyleSheet(label_style(12, "tp", "600"))
        btn_ver = QPushButton("Ver todas")
        btn_ver.setFixedHeight(26)
        btn_ver.setStyleSheet(btn_style(t('accd'), t('acct'), 6, "4px 10px"))
        btn_ver.clicked.connect(lambda: self.parent_app.abrir_explorador_descargas())
        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(24, 24)
        btn_cerrar.setStyleSheet(
            f"background:transparent;color:{t('tm')};border:none;font-size:13px;")
        btn_cerrar.clicked.connect(lambda: self.parent_app.cerrar_panel_descargas())
        hdr_lay.addWidget(ttl)
        hdr_lay.addStretch()
        hdr_lay.addWidget(btn_ver)
        hdr_lay.addWidget(btn_cerrar)
        lay.addWidget(hdr)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border:none;background:transparent;")
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
            key=lambda x: os.path.getmtime(os.path.join(carpeta, x)), reverse=True
        )[:15]
        for arc in archivos:
            ruta = os.path.join(carpeta, arc)
            kb = os.path.getsize(ruta) // 1024
            es_docx = arc.endswith(".docx")
            card = QFrame()
            card.setStyleSheet(
                f"QFrame{{background:{t('card')};border:1px solid {t('brd')};border-radius:10px;}}"
                f"QFrame:hover{{border:1px solid {t('acc')};}}")
            cl = QHBoxLayout(card)
            cl.setContentsMargins(10, 8, 10, 8)
            cl.setSpacing(8)
            badge = QLabel("W" if es_docx else "P")
            badge.setFixedSize(34, 34)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bg = "rgba(24,95,165,80)" if es_docx else "rgba(163,45,45,80)"
            fg = "#85B7EB" if es_docx else "#F09595"
            badge.setStyleSheet(
                f"background:{bg};color:{fg};border-radius:8px;font-weight:700;font-size:11px;border:none;")
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
            btn_open.setStyleSheet(
                f"background:transparent;color:{t('acc')};border:none;font-size:14px;")
            btn_open.clicked.connect(lambda _, r=ruta: os.startfile(r))
            cl.addWidget(badge)
            cl.addLayout(info)
            cl.addStretch()
            cl.addWidget(btn_open)
            self.lista_lay.insertWidget(self.lista_lay.count() - 1, card)


# ─────────────────────────────────────────────
#  EXPLORADOR DE DESCARGAS (diálogo completo)
# ─────────────────────────────────────────────


class ExploradorDescargas(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
        self.setWindowTitle("Explorador de Descargas")
        self.resize(680, 460)
        self.setStyleSheet(
            f"background:{t('sb')};color:{t('tp')};font-family:'SF Pro Display','Segoe UI',sans-serif;")
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 16, 16, 16)

        hdr = QHBoxLayout()
        lbl = QLabel("📁  Explorador de Descargas")
        lbl.setStyleSheet(label_style(14, "tp", "600"))
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("🔍  Buscar archivo…")
        self.buscador.setFixedHeight(32)
        self.buscador.setStyleSheet(
            f"QLineEdit{{background:{t('inp')};color:{t('tp')};border:1px solid {t('brd')};"
            f"border-radius:8px;padding:0 12px;font-size:12px;}}")
        self.buscador.textChanged.connect(self.cargar_archivos)
        hdr.addWidget(lbl)
        hdr.addStretch()
        hdr.addWidget(self.buscador)
        lay.addLayout(hdr)

        self.tabla = QTreeWidget()
        self.tabla.setHeaderLabels(["Nombre", "Tipo", "Tamaño", "Modificado"])
        self.tabla.setColumnWidth(0, 300)
        self.tabla.setColumnWidth(1, 60)
        self.tabla.setColumnWidth(2, 80)
        self.tabla.setColumnWidth(3, 160)
        self.tabla.setStyleSheet(f"""
            QTreeWidget {{background:{t('card')};color:{t('tp')};border:1px solid {t('brd')};
                border-radius:10px;outline:none;font-size:12px;}}
            QTreeWidget::item:hover {{background:{t('cardh')};}}
            QTreeWidget::item:selected {{background:{t('accd')};color:{t('acct')};}}
            QHeaderView::section {{background:{t('bar')};color:{t('ts')};border:none;
                padding:6px;font-weight:600;font-size:11px;}}
        """)
        self.tabla.itemDoubleClicked.connect(self.abrir_archivo)
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.menu_contextual)
        lay.addWidget(self.tabla)

        btns = QHBoxLayout()
        for txt, color, fn in [
            ("↗ Abrir",           "#238636", self.abrir_archivo),
            ("📁 Mover al semestre", "#1F6FEB", self.mover_archivo),
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
        if not os.path.exists(self.carpeta):
            return
        archivos = sorted(
            [f for f in os.listdir(self.carpeta)
             if f.endswith((".docx", ".pdf")) and query in f.lower()],
            key=lambda x: os.path.getmtime(os.path.join(self.carpeta, x)), reverse=True
        )
        for arc in archivos:
            ruta = os.path.join(self.carpeta, arc)
            item = QTreeWidgetItem([
                arc,
                "DOCX" if arc.endswith(".docx") else "PDF",
                f"{os.path.getsize(ruta) // 1024} KB",
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
        if ruta:
            os.startfile(ruta)

    def eliminar_archivo(self):
        nombre, ruta = self._item_actual()
        if not ruta:
            return
        if QMessageBox.question(
            self, "Eliminar", f"¿Eliminar {nombre}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            os.remove(ruta)
            self.cargar_archivos()
            self.parent_app.actualizar_arbol()

    def renombrar_archivo(self):
        nombre, ruta = self._item_actual()
        if not ruta:
            return
        nuevo, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=nombre)
        if ok and nuevo:
            if not nuevo.endswith((".docx", ".pdf")):
                nuevo += ".docx" if nombre.endswith(".docx") else ".pdf"
            os.rename(ruta, os.path.join(self.carpeta, nuevo))
            self.cargar_archivos()
            self.parent_app.actualizar_arbol()

    def mover_archivo(self):
        nombre, ruta = self._item_actual()
        if not ruta:
            return
        semestres = self.parent_app.obtener_semestres_raiz()
        sem, ok1 = QInputDialog.getItem(self, "Mover", "Semestre:", semestres, 0, False)
        if not ok1:
            return
        materias = [m for m in os.listdir(os.path.join(PATH_RAIZ, sem))
                    if os.path.isdir(os.path.join(PATH_RAIZ, sem, m)) and m != "Plantillas"]
        mat, ok2 = QInputDialog.getItem(self, "Mover", "Materia:", materias, 0, False)
        if not ok2:
            return
        shutil.move(ruta, os.path.join(PATH_RAIZ, sem, mat, nombre))
        self.cargar_archivos()
        self.parent_app.actualizar_arbol()
        QMessageBox.information(self, "Éxito", f"Movido → {sem} / {mat}")

    def menu_contextual(self, pos):
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{background:{t('sb')};color:{t('tp')};border:1px solid {t('brd')};
                border-radius:10px;padding:4px;font-size:12px;}}
            QMenu::item {{padding:7px 16px;border-radius:6px;}}
            QMenu::item:selected {{background:{t('accd')};color:{t('acct')};}}
        """)
        menu.addAction("↗ Abrir").triggered.connect(self.abrir_archivo)
        menu.addAction("📁 Mover").triggered.connect(self.mover_archivo)
        menu.addAction("✏️ Renombrar").triggered.connect(self.renombrar_archivo)
        menu.addAction("🗑️ Eliminar").triggered.connect(self.eliminar_archivo)
        menu.exec(self.tabla.viewport().mapToGlobal(pos))
