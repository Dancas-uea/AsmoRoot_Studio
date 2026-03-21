import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QWidget, QFileDialog,
    QTimeEdit, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QTime
from PyQt6.QtGui import QFont


# ─────────────────────────────────────────────
#  COLORES
# ─────────────────────────────────────────────
BG       = "#08081a"
CARD     = "rgba(255,255,255,10)"
CARDB    = "rgba(255,255,255,22)"
BRD      = "rgba(255,255,255,23)"
ACC      = "#378ADD"
ACCD     = "rgba(55,138,221,40)"
ACCT     = "#85B7EB"
TP       = "rgba(255,255,255,230)"
TS       = "rgba(255,255,255,115)"
TM       = "rgba(255,255,255,56)"


def _lbl(text, size=11, color=TS, weight="normal"):
    return (f"color:{color};font-size:{size}px;font-weight:{weight};"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;"
            f"border:none;text-decoration:none;background:transparent;")


def _inp():
    return (f"QLineEdit{{background:{CARD};color:{TP};border:1px solid {BRD};"
            f"border-radius:8px;padding:8px 12px;font-size:12px;"
            f"font-family:'SF Pro Display','Segoe UI',sans-serif;}}"
            f"QLineEdit:focus{{border:1px solid {ACC};background:{ACCD};}}")


def _btn(bg=ACC, fg="white", radius=8, padding="10px 18px"):
    return (f"QPushButton{{background:{bg};color:{fg};border:none;"
            f"border-radius:{radius}px;padding:{padding};font-weight:600;"
            f"font-size:12px;font-family:'SF Pro Display','Segoe UI',sans-serif;}}"
            f"QPushButton:hover{{border:1px solid rgba(255,255,255,50);}}"
            f"QPushButton:pressed{{opacity:0.8;}}"
            f"QPushButton:disabled{{opacity:0.35;}}")


# ─────────────────────────────────────────────
#  SETUP WIZARD
# ─────────────────────────────────────────────
class SetupWizard(QDialog):
    def __init__(self, config_path):
        super().__init__()
        self.config_path = config_path
        self.config = {
            "nombre": "",
            "universidad": "",
            "carrera": "",
            "path_raiz": "",
            "semestres": {},
            "clases_teams": [],
            "configurado": False
        }
        self.semestres_widgets = []
        self.clases_widgets = []

        self.setWindowTitle("AsmoRoot — Configuración inicial")
        self.setFixedSize(700, 600)
        self.setStyleSheet(f"background:{BG};color:{TP};"
                           f"font-family:'SF Pro Display','Segoe UI',sans-serif;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background:rgba(13,13,28,200);border-bottom:1px solid {BRD};")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(28, 0, 28, 0)

        ic = QLabel("🎓")
        ic.setStyleSheet("font-size:28px;border:none;background:transparent;")
        tit = QVBoxLayout()
        tit.setSpacing(2)
        t1 = QLabel("Bienvenido a AsmoRoot")
        t1.setStyleSheet(_lbl("Bienvenido a AsmoRoot", 16, TP, "700"))
        t2 = QLabel("Configura tu espacio de trabajo en 4 pasos")
        t2.setStyleSheet(_lbl("", 11, TM))
        tit.addWidget(t1)
        tit.addWidget(t2)
        h_lay.addWidget(ic)
        h_lay.addSpacing(12)
        h_lay.addLayout(tit)
        h_lay.addStretch()
        layout.addWidget(header)

        # ── Indicador de pasos ─────────────────
        self.steps_bar = QFrame()
        self.steps_bar.setFixedHeight(44)
        self.steps_bar.setStyleSheet(f"background:rgba(10,10,20,180);border-bottom:1px solid {BRD};")
        sb_lay = QHBoxLayout(self.steps_bar)
        sb_lay.setContentsMargins(28, 0, 28, 0)
        sb_lay.setSpacing(0)

        self.step_btns = []
        pasos = ["1. Datos personales", "2. Carpeta", "3. Semestres"]
        for i, nombre in enumerate(pasos):
            b = QLabel(nombre)
            b.setAlignment(Qt.AlignmentFlag.AlignCenter)
            b.setFixedHeight(44)
            b.setStyleSheet(_lbl("", 11, TM))
            sb_lay.addWidget(b, 1)
            self.step_btns.append(b)
        layout.addWidget(self.steps_bar)

        # ── Stack de páginas ───────────────────
        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_datos())
        self.stack.addWidget(self._page_carpeta())
        self.stack.addWidget(self._page_semestres())
        layout.addWidget(self.stack, 1)

        # ── Footer con botones ─────────────────
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet(f"background:rgba(13,13,28,200);border-top:1px solid {BRD};")
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(28, 0, 28, 0)
        f_lay.setSpacing(10)

        self.btn_back = QPushButton("← Atrás")
        self.btn_back.setFixedHeight(36)
        self.btn_back.setStyleSheet(_btn(ACCD, ACCT, 8, "0 20px"))
        self.btn_back.setEnabled(False)
        self.btn_back.clicked.connect(self._prev)

        self.btn_next = QPushButton("Siguiente →")
        self.btn_next.setFixedHeight(36)
        self.btn_next.setStyleSheet(_btn(ACC, "white", 8, "0 24px"))
        self.btn_next.clicked.connect(self._next)

        f_lay.addWidget(self.btn_back)
        f_lay.addStretch()
        f_lay.addWidget(self.btn_next)
        layout.addWidget(footer)

        self._actualizar_steps(0)

    # ── PÁGINA 1: Datos personales ─────────────
    def _page_datos(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(16)

        lbl_sec = QLabel("INFORMACIÓN PERSONAL")
        lbl_sec.setStyleSheet(_lbl("", 9, TM) + "letter-spacing:1.2px;")
        lay.addWidget(lbl_sec)

        for etiqueta, attr in [
            ("Nombre completo", "inp_nombre"),
            ("Universidad", "inp_universidad"),
            ("Carrera", "inp_carrera"),
        ]:
            lbl = QLabel(etiqueta)
            lbl.setStyleSheet(_lbl("", 11, TS, "500"))
            inp = QLineEdit()
            inp.setPlaceholderText(f"Ej: {'Juan Pérez' if 'Nombre' in etiqueta else etiqueta}")
            inp.setFixedHeight(40)
            inp.setStyleSheet(_inp())
            setattr(self, attr, inp)
            lay.addWidget(lbl)
            lay.addWidget(inp)

        lay.addStretch()
        return page

    # ── PÁGINA 2: Carpeta ──────────────────────
    def _page_carpeta(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(16)

        lbl_sec = QLabel("CARPETA DE TRABAJO")
        lbl_sec.setStyleSheet(_lbl("", 9, TM) + "letter-spacing:1.2px;")
        lay.addWidget(lbl_sec)

        desc = QLabel("Aquí se guardarán todos tus semestres, materias y archivos.")
        desc.setStyleSheet(_lbl("", 11, TS))
        desc.setWordWrap(True)
        lay.addWidget(desc)

        row = QHBoxLayout()
        self.inp_carpeta = QLineEdit()
        self.inp_carpeta.setPlaceholderText("Selecciona una carpeta...")
        self.inp_carpeta.setFixedHeight(40)
        self.inp_carpeta.setReadOnly(True)
        self.inp_carpeta.setStyleSheet(_inp())

        btn_browse = QPushButton("📁  Examinar")
        btn_browse.setFixedHeight(40)
        btn_browse.setStyleSheet(_btn(ACCD, ACCT, 8, "0 16px"))
        btn_browse.clicked.connect(self._elegir_carpeta)

        row.addWidget(self.inp_carpeta, 1)
        row.addWidget(btn_browse)
        lay.addLayout(row)

        self.lbl_preview = QLabel("")
        self.lbl_preview.setStyleSheet(_lbl("", 11, ACCT))
        self.lbl_preview.setWordWrap(True)
        lay.addWidget(self.lbl_preview)

        lay.addStretch()
        return page

    # ── PÁGINA 3: Semestres ────────────────────
    def _page_semestres(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 20, 40, 20)
        lay.setSpacing(10)

        top = QHBoxLayout()
        lbl_sec = QLabel("SEMESTRES Y MATERIAS")
        lbl_sec.setStyleSheet(_lbl("", 9, TM) + "letter-spacing:1.2px;")
        btn_add = QPushButton("＋ Añadir semestre")
        btn_add.setFixedHeight(30)
        btn_add.setStyleSheet(_btn(ACCD, ACCT, 7, "0 12px"))
        btn_add.clicked.connect(self._add_semestre)
        top.addWidget(lbl_sec)
        top.addStretch()
        top.addWidget(btn_add)
        lay.addLayout(top)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}"
                             "QScrollBar:vertical{width:4px;background:transparent;}"
                             "QScrollBar::handle:vertical{background:rgba(255,255,255,40);border-radius:2px;}"
                             "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        self.sem_container = QWidget()
        self.sem_container.setStyleSheet("background:transparent;")
        self.sem_lay = QVBoxLayout(self.sem_container)
        self.sem_lay.setSpacing(8)
        self.sem_lay.setContentsMargins(0, 0, 0, 0)
        self.sem_lay.addStretch()
        scroll.setWidget(self.sem_container)
        lay.addWidget(scroll, 1)

        self._add_semestre()
        return page

    def _add_semestre(self):
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background:{CARD};border:1px solid {BRD};border-radius:10px;}}")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(14, 10, 14, 10)
        c_lay.setSpacing(8)

        row1 = QHBoxLayout()
        inp_sem = QLineEdit()
        inp_sem.setPlaceholderText("Nombre del semestre (ej: Primer Semestre)")
        inp_sem.setFixedHeight(36)
        inp_sem.setStyleSheet(_inp())

        btn_del = QPushButton("✕")
        btn_del.setFixedSize(30, 30)
        btn_del.setStyleSheet(f"QPushButton{{background:transparent;color:{TM};border:none;font-size:14px;}}"
                              f"QPushButton:hover{{color:#ff5f57;}}")
        btn_del.clicked.connect(lambda: self._del_semestre(card))
        row1.addWidget(inp_sem, 1)
        row1.addWidget(btn_del)
        c_lay.addLayout(row1)

        inp_mats = QLineEdit()
        inp_mats.setPlaceholderText("Materias separadas por coma (ej: Matemáticas, Física, Programación)")
        inp_mats.setFixedHeight(36)
        inp_mats.setStyleSheet(_inp())
        c_lay.addWidget(inp_mats)

        self.sem_lay.insertWidget(self.sem_lay.count() - 1, card)
        self.semestres_widgets.append((card, inp_sem, inp_mats))

    def _del_semestre(self, card):
        self.semestres_widgets = [(c, s, m) for c, s, m in self.semestres_widgets if c != card]
        card.deleteLater()

    # ── PÁGINA 4: Teams ────────────────────────
    def _page_teams(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 20, 40, 20)
        lay.setSpacing(10)

        top = QHBoxLayout()
        lbl_sec = QLabel("CLASES DE TEAMS")
        lbl_sec.setStyleSheet(_lbl("", 9, TM) + "letter-spacing:1.2px;")
        btn_add = QPushButton("＋ Añadir clase")
        btn_add.setFixedHeight(30)
        btn_add.setStyleSheet(_btn(ACCD, ACCT, 7, "0 12px"))
        btn_add.clicked.connect(self._add_clase)
        top.addWidget(lbl_sec)
        top.addStretch()
        top.addWidget(btn_add)
        lay.addLayout(top)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}"
                             "QScrollBar:vertical{width:4px;background:transparent;}"
                             "QScrollBar::handle:vertical{background:rgba(255,255,255,40);border-radius:2px;}"
                             "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        self.teams_container = QWidget()
        self.teams_container.setStyleSheet("background:transparent;")
        self.teams_lay = QVBoxLayout(self.teams_container)
        self.teams_lay.setSpacing(8)
        self.teams_lay.setContentsMargins(0, 0, 0, 0)
        self.teams_lay.addStretch()
        scroll.setWidget(self.teams_container)
        lay.addWidget(scroll, 1)

        self._add_clase()
        return page

    def _add_clase(self):
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background:{CARD};border:1px solid {BRD};border-radius:10px;}}")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(14, 10, 14, 10)
        c_lay.setSpacing(8)

        row1 = QHBoxLayout()
        inp_mat = QLineEdit()
        inp_mat.setPlaceholderText("Nombre de la materia")
        inp_mat.setFixedHeight(34)
        inp_mat.setStyleSheet(_inp())

        btn_del = QPushButton("✕")
        btn_del.setFixedSize(28, 28)
        btn_del.setStyleSheet(f"QPushButton{{background:transparent;color:{TM};border:none;font-size:13px;}}"
                              f"QPushButton:hover{{color:#ff5f57;}}")
        btn_del.clicked.connect(lambda: self._del_clase(card))
        row1.addWidget(inp_mat, 1)
        row1.addWidget(btn_del)
        c_lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_ini = QLabel("Inicio:")
        lbl_ini.setStyleSheet(_lbl("", 11, TS))
        t_ini = QTimeEdit()
        t_ini.setDisplayFormat("HH:mm")
        t_ini.setTime(QTime(7, 30))
        t_ini.setFixedHeight(34)
        t_ini.setStyleSheet(f"QTimeEdit{{background:{CARD};color:{TP};border:1px solid {BRD};"
                            f"border-radius:8px;padding:0 8px;font-size:12px;}}")

        lbl_fin = QLabel("Fin:")
        lbl_fin.setStyleSheet(_lbl("", 11, TS))
        t_fin = QTimeEdit()
        t_fin.setDisplayFormat("HH:mm")
        t_fin.setTime(QTime(8, 30))
        t_fin.setFixedHeight(34)
        t_fin.setStyleSheet(f"QTimeEdit{{background:{CARD};color:{TP};border:1px solid {BRD};"
                            f"border-radius:8px;padding:0 8px;font-size:12px;}}")

        row2.addWidget(lbl_ini)
        row2.addWidget(t_ini)
        row2.addWidget(lbl_fin)
        row2.addWidget(t_fin)
        row2.addStretch()
        c_lay.addLayout(row2)

        inp_link = QLineEdit()
        inp_link.setPlaceholderText("Link de Teams (https://teams.microsoft.com/meet/...)")
        inp_link.setFixedHeight(34)
        inp_link.setStyleSheet(_inp())
        c_lay.addWidget(inp_link)

        self.teams_lay.insertWidget(self.teams_lay.count() - 1, card)
        self.clases_widgets.append((card, inp_mat, t_ini, t_fin, inp_link))

    def _del_clase(self, card):
        self.clases_widgets = [(c, m, i, f, l) for c, m, i, f, l in self.clases_widgets if c != card]
        card.deleteLater()

    # ── NAVEGACIÓN ─────────────────────────────
    def _actualizar_steps(self, idx):
        for i, b in enumerate(self.step_btns):
            if i == idx:
                b.setStyleSheet(_lbl("", 12, ACCT, "600") +
                                f"border-bottom:2px solid {ACC};")
            elif i < idx:
                b.setStyleSheet(_lbl("", 11, TS))
            else:
                b.setStyleSheet(_lbl("", 11, TM))
        self.btn_back.setEnabled(idx > 0)
        self.btn_next.setText("Finalizar ✓" if idx == 2 else "Siguiente →")

    def _prev(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
            self._actualizar_steps(idx - 1)

    def _next(self):
        idx = self.stack.currentIndex()
        if not self._validar(idx):
            return
        if idx == 2:
            self._guardar()
            self.accept()
        else:
            self.stack.setCurrentIndex(idx + 1)
            self._actualizar_steps(idx + 1)

    def _elegir_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona carpeta de trabajo")
        if carpeta:
            self.inp_carpeta.setText(carpeta)
            self.lbl_preview.setText(f"✓ Tus archivos se guardarán en: {carpeta}/AsmoRoot/")

    # ── VALIDACIÓN ─────────────────────────────
    def _validar(self, idx):
        if idx == 0:
            if not self.inp_nombre.text().strip():
                QMessageBox.warning(self, "Campo requerido", "Ingresa tu nombre completo.")
                return False
            if not self.inp_universidad.text().strip():
                QMessageBox.warning(self, "Campo requerido", "Ingresa tu universidad.")
                return False
            if not self.inp_carrera.text().strip():
                QMessageBox.warning(self, "Campo requerido", "Ingresa tu carrera.")
                return False
        elif idx == 1:
            if not self.inp_carpeta.text().strip():
                QMessageBox.warning(self, "Campo requerido", "Selecciona una carpeta de trabajo.")
                return False
        elif idx == 2:
            if not self.semestres_widgets:
                QMessageBox.warning(self, "Campo requerido", "Agrega al menos un semestre.")
                return False
            for _, inp_sem, inp_mats in self.semestres_widgets:
                if not inp_sem.text().strip():
                    QMessageBox.warning(self, "Campo requerido", "Escribe el nombre del semestre.")
                    return False
                if not inp_mats.text().strip():
                    QMessageBox.warning(self, "Campo requerido", "Agrega al menos una materia.")
                    return False
        return True

    # ── GUARDAR CONFIG Y CREAR CARPETAS ────────
    def _guardar(self):
        raiz = os.path.join(self.inp_carpeta.text().strip(), "AsmoRoot")

        semestres = {}
        for _, inp_sem, inp_mats in self.semestres_widgets:
            sem = inp_sem.text().strip()
            mats = [m.strip() for m in inp_mats.text().split(",") if m.strip()]
            semestres[sem] = mats
            ruta_sem = os.path.join(raiz, sem)
            os.makedirs(os.path.join(ruta_sem, "Plantillas"), exist_ok=True)
            for mat in mats:
                os.makedirs(os.path.join(ruta_sem, mat), exist_ok=True)
                plantilla = os.path.join(ruta_sem, "Plantillas", f"{mat}.docx")
                if not os.path.exists(plantilla):
                    with open(plantilla, 'wb'): pass



        self.config = {
            "nombre": self.inp_nombre.text().strip(),
            "universidad": self.inp_universidad.text().strip(),
            "carrera": self.inp_carrera.text().strip(),
            "path_raiz": raiz,
            "semestres": semestres,
            "clases_teams": [],
            "ultimo_semestre": "",
            "ultima_materia": "",
            "configurado": True
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def _importar_excel(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Selecciona la plantilla Excel", "",
            "Excel (*.xlsx *.xls)")
        if not ruta:
            return

        try:
            import openpyxl
            wb = openpyxl.load_workbook(ruta, data_only=True)
            ws = wb.active
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo:\n{e}")
            return

        clases_nuevas = []
        for row in ws.iter_rows(min_row=5, values_only=True):
            if not row[0]:
                continue
            mat  = str(row[0]).strip() if row[0] else ""
            ini  = str(row[1]).strip() if row[1] else "07:00"
            fin  = str(row[2]).strip() if row[2] else "08:00"
            link = str(row[3]).strip() if row[3] else ""
            color= str(row[4]).strip() if row[4] else "#378ADD"
            icono= str(row[5]).strip() if row[5] else "📘"
            if mat:
                clases_nuevas.append((mat, ini, fin, link, color, icono))

        if not clases_nuevas:
            QMessageBox.warning(self, "Aviso", "No se encontraron clases en el archivo.")
            return

        if self.clases_widgets:
            resp = QMessageBox.question(
                self, "Clases existentes",
                f"Ya tienes {len(self.clases_widgets)} clase(s) cargada(s).\n¿Reemplazar con las del Excel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp == QMessageBox.StandardButton.Yes:
                for card, _, _, _, _ in self.clases_widgets:
                    card.deleteLater()
                self.clases_widgets = []

        for mat, ini, fin, link, color, icono in clases_nuevas:
            self._add_clase_datos(mat, ini, fin, link)

        QMessageBox.information(
            self, "Importado",
            f"✓ Se importaron {len(clases_nuevas)} clase(s) correctamente.")

    def _add_clase_datos(self, mat="", ini="07:30", fin="08:30", link=""):
        from PyQt6.QtCore import QTime
        card = self._crear_card_clase()
        card_data = self.clases_widgets[-1]
        _, inp_mat, t_ini, t_fin, inp_link = card_data
        inp_mat.setText(mat)
        try:
            h_ini, m_ini = map(int, ini.split(":"))
            h_fin, m_fin = map(int, fin.split(":"))
            t_ini.setTime(QTime(h_ini, m_ini))
            t_fin.setTime(QTime(h_fin, m_fin))
        except Exception:
            pass
        inp_link.setText(link)

    def _crear_card_clase(self):
        from PyQt6.QtCore import QTime
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background:{CARD};border:1px solid {BRD};border-radius:10px;}}")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(14, 10, 14, 10)
        c_lay.setSpacing(8)

        row1 = QHBoxLayout()
        inp_mat = QLineEdit()
        inp_mat.setPlaceholderText("Nombre de la materia")
        inp_mat.setFixedHeight(34)
        inp_mat.setStyleSheet(_inp())
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(28, 28)
        btn_del.setStyleSheet(f"QPushButton{{background:transparent;color:{TM};border:none;font-size:13px;}}"
                              f"QPushButton:hover{{color:#ff5f57;}}")
        btn_del.clicked.connect(lambda: self._del_clase(card))
        row1.addWidget(inp_mat, 1)
        row1.addWidget(btn_del)
        c_lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        lbl_ini = QLabel("Inicio:")
        lbl_ini.setStyleSheet(_lbl("", 11, TS))
        t_ini = QTimeEdit()
        t_ini.setDisplayFormat("HH:mm")
        t_ini.setTime(QTime(7, 30))
        t_ini.setFixedHeight(34)
        t_ini.setStyleSheet(f"QTimeEdit{{background:{CARD};color:{TP};border:1px solid {BRD};"
                            f"border-radius:8px;padding:0 8px;font-size:12px;}}")
        lbl_fin = QLabel("Fin:")
        lbl_fin.setStyleSheet(_lbl("", 11, TS))
        t_fin = QTimeEdit()
        t_fin.setDisplayFormat("HH:mm")
        t_fin.setTime(QTime(8, 30))
        t_fin.setFixedHeight(34)
        t_fin.setStyleSheet(f"QTimeEdit{{background:{CARD};color:{TP};border:1px solid {BRD};"
                            f"border-radius:8px;padding:0 8px;font-size:12px;}}")
        row2.addWidget(lbl_ini)
        row2.addWidget(t_ini)
        row2.addWidget(lbl_fin)
        row2.addWidget(t_fin)
        row2.addStretch()
        c_lay.addLayout(row2)

        inp_link = QLineEdit()
        inp_link.setPlaceholderText("Link de Teams (https://teams.microsoft.com/meet/...)")
        inp_link.setFixedHeight(34)
        inp_link.setStyleSheet(_inp())
        c_lay.addWidget(inp_link)

        self.teams_lay.insertWidget(self.teams_lay.count() - 1, card)
        self.clases_widgets.append((card, inp_mat, t_ini, t_fin, inp_link))
        return card
