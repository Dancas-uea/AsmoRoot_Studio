import os
import json
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QFileDialog, QMessageBox,
    QTimeEdit, QComboBox
)
from PyQt6.QtCore import Qt, QTime


# ─────────────────────────────────────────────
#  HELPERS DE ESTILO (independientes del tema)
# ─────────────────────────────────────────────
BG    = "#08081a"
CARD  = "rgba(255,255,255,10)"
CARDH = "rgba(255,255,255,22)"
BRD   = "rgba(255,255,255,23)"
ACC   = "#378ADD"
ACCD  = "rgba(55,138,221,40)"
ACCT  = "#85B7EB"
TP    = "rgba(255,255,255,230)"
TS    = "rgba(255,255,255,115)"
TM    = "rgba(255,255,255,56)"
GRN   = "#28c840"
RED   = "#ff5f57"


def _lbl(size=11, color=TS, weight="normal"):
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
            f"QPushButton:pressed{{opacity:0.8;}}")


def _card_style():
    return (f"QFrame{{background:{CARD};border:1px solid {BRD};border-radius:14px;}}")


def _seccion(texto):
    lbl = QLabel(texto)
    lbl.setStyleSheet(_lbl(9, TM) + "letter-spacing:1.2px;")
    return lbl


# ─────────────────────────────────────────────
#  PANEL CONFIGURACIÓN
# ─────────────────────────────────────────────
class PanelConfiguracion(QScrollArea):
    def __init__(self, config_path, parent_app=None):
        super().__init__()
        self.config_path = config_path
        self.parent_app  = parent_app
        self.clases_widgets = []

        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea{border:none;background:transparent;}"
                           "QScrollBar:vertical{width:4px;background:transparent;}"
                           "QScrollBar::handle:vertical{background:rgba(255,255,255,40);border-radius:2px;}"
                           "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")

        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        self.lay = QVBoxLayout(inner)
        self.lay.setContentsMargins(32, 28, 32, 32)
        self.lay.setSpacing(20)

        self._build()
        self.setWidget(inner)

    def _build(self):
        config = self._cargar()

        # ── Header ────────────────────────────
        hdr = QHBoxLayout()
        ic = QLabel("⚙️")
        ic.setStyleSheet("font-size:28px;border:none;background:transparent;")
        ic.setFixedSize(44, 44)
        info = QVBoxLayout()
        info.setSpacing(2)
        t1 = QLabel("Configuración")
        t1.setStyleSheet(_lbl(18, TP, "700"))
        t2 = QLabel(f"Hola, {config.get('nombre', 'Estudiante')} · {config.get('universidad','')}")
        t2.setStyleSheet(_lbl(11, TM))
        info.addWidget(t1)
        info.addWidget(t2)
        hdr.addWidget(ic)
        hdr.addSpacing(10)
        hdr.addLayout(info)
        hdr.addStretch()
        self.lay.addLayout(hdr)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{BRD};border:none;")
        self.lay.addWidget(sep)

        # ── Sección 1: Datos personales ───────
        self.lay.addWidget(_seccion("DATOS PERSONALES"))
        card1 = QFrame()
        card1.setStyleSheet(_card_style())
        c1_lay = QVBoxLayout(card1)
        c1_lay.setContentsMargins(20, 16, 20, 16)
        c1_lay.setSpacing(12)

        for etiqueta, attr, key in [
            ("Nombre completo", "inp_nombre",      "nombre"),
            ("Universidad",     "inp_universidad",  "universidad"),
            ("Carrera",         "inp_carrera",      "carrera"),
        ]:
            lbl = QLabel(etiqueta)
            lbl.setStyleSheet(_lbl(11, TS, "500"))
            inp = QLineEdit()
            inp.setText(config.get(key, ""))
            inp.setFixedHeight(38)
            inp.setStyleSheet(_inp())
            setattr(self, attr, inp)
            c1_lay.addWidget(lbl)
            c1_lay.addWidget(inp)

        btn_guardar_datos = QPushButton("💾  Guardar datos personales")
        btn_guardar_datos.setFixedHeight(38)
        btn_guardar_datos.setStyleSheet(_btn(ACCD, ACCT, 9, "0 16px"))
        btn_guardar_datos.clicked.connect(self._guardar_datos)
        c1_lay.addWidget(btn_guardar_datos)
        self.lay.addWidget(card1)

        # ── Sección 2: Carpeta de trabajo ─────
        self.lay.addWidget(_seccion("CARPETA DE TRABAJO"))
        card2 = QFrame()
        card2.setStyleSheet(_card_style())
        c2_lay = QVBoxLayout(card2)
        c2_lay.setContentsMargins(20, 16, 20, 16)
        c2_lay.setSpacing(10)

        lbl_c = QLabel("Carpeta actual donde se guardan tus archivos:")
        lbl_c.setStyleSheet(_lbl(11, TS))
        self.lbl_carpeta_actual = QLabel(config.get("path_raiz", "No configurada"))
        self.lbl_carpeta_actual.setStyleSheet(_lbl(11, ACCT))
        self.lbl_carpeta_actual.setWordWrap(True)

        row_c = QHBoxLayout()
        self.inp_carpeta = QLineEdit()
        self.inp_carpeta.setPlaceholderText("Selecciona nueva carpeta...")
        self.inp_carpeta.setFixedHeight(38)
        self.inp_carpeta.setReadOnly(True)
        self.inp_carpeta.setStyleSheet(_inp())
        btn_browse = QPushButton("📁  Examinar")
        btn_browse.setFixedHeight(38)
        btn_browse.setStyleSheet(_btn(ACCD, ACCT, 8, "0 14px"))
        btn_browse.clicked.connect(self._elegir_carpeta)
        row_c.addWidget(self.inp_carpeta, 1)
        row_c.addWidget(btn_browse)

        btn_guardar_carpeta = QPushButton("💾  Cambiar carpeta")
        btn_guardar_carpeta.setFixedHeight(38)
        btn_guardar_carpeta.setStyleSheet(_btn(ACCD, ACCT, 9, "0 16px"))
        btn_guardar_carpeta.clicked.connect(self._guardar_carpeta)

        c2_lay.addWidget(lbl_c)
        c2_lay.addWidget(self.lbl_carpeta_actual)
        c2_lay.addLayout(row_c)
        c2_lay.addWidget(btn_guardar_carpeta)
        self.lay.addWidget(card2)

        # ── Sección 3: Horario Teams ──────────
        self.lay.addWidget(_seccion("HORARIO DE TEAMS"))
        card3 = QFrame()
        card3.setStyleSheet(_card_style())
        c3_lay = QVBoxLayout(card3)
        c3_lay.setContentsMargins(20, 16, 20, 16)
        c3_lay.setSpacing(10)

        top_teams = QHBoxLayout()
        lbl_t = QLabel("Clases actuales — puedes editar o importar nuevo Excel")
        lbl_t.setStyleSheet(_lbl(11, TS))
        btn_excel = QPushButton("📥  Importar Excel")
        btn_excel.setFixedHeight(30)
        btn_excel.setStyleSheet(_btn(f"rgba(40,200,64,35)", GRN, 7, "0 12px"))
        btn_excel.clicked.connect(self._importar_excel)
        btn_add = QPushButton("＋ Añadir")
        btn_add.setFixedHeight(30)
        btn_add.setStyleSheet(_btn(ACCD, ACCT, 7, "0 12px"))
        btn_add.clicked.connect(self._add_clase)
        top_teams.addWidget(lbl_t)
        top_teams.addStretch()
        top_teams.addWidget(btn_excel)
        top_teams.addWidget(btn_add)
        c3_lay.addLayout(top_teams)

        self.teams_container = QWidget()
        self.teams_container.setStyleSheet("background:transparent;")
        self.teams_lay = QVBoxLayout(self.teams_container)
        self.teams_lay.setSpacing(8)
        self.teams_lay.setContentsMargins(0, 0, 0, 0)
        self.teams_lay.addStretch()
        c3_lay.addWidget(self.teams_container)

        clases = config.get("clases_teams", [])
        for clase in clases:
            self._add_clase_datos(
                clase.get("materia", ""),
                clase.get("hora_ini", "07:00"),
                clase.get("hora_fin", "08:00"),
                clase.get("link", "")
            )

        btn_guardar_teams = QPushButton("💾  Guardar horario Teams")
        btn_guardar_teams.setFixedHeight(38)
        btn_guardar_teams.setStyleSheet(_btn(ACC, "white", 9, "0 16px"))
        btn_guardar_teams.clicked.connect(self._guardar_teams)
        c3_lay.addWidget(btn_guardar_teams)
        self.lay.addWidget(card3)

        # ── Sección 4: Plantillas ─────────────
        self.lay.addWidget(_seccion("PLANTILLAS POR MATERIA"))
        card_pl = QFrame()
        card_pl.setStyleSheet(_card_style())
        cpl_lay = QVBoxLayout(card_pl)
        cpl_lay.setContentsMargins(20, 16, 20, 16)
        cpl_lay.setSpacing(12)

        desc_pl = QLabel("Selecciona el semestre y sube la carátula (.docx) para cada materia.")
        desc_pl.setStyleSheet(_lbl(11, TS))
        desc_pl.setWordWrap(True)
        cpl_lay.addWidget(desc_pl)

        row_sem = QHBoxLayout()
        lbl_sem = QLabel("Semestre:")
        lbl_sem.setStyleSheet(_lbl(11, TS, "500"))
        self.combo_sem_pl = QComboBox()
        self.combo_sem_pl.setFixedHeight(36)
        self.combo_sem_pl.setStyleSheet(
            f"QComboBox{{background:{CARD};color:{TP};border:1px solid {BRD};"
            f"border-radius:8px;padding:0 12px;font-size:12px;}}"
            f"QComboBox::drop-down{{border:none;width:20px;}}"
            f"QComboBox::down-arrow{{image:none;width:0;}}")
        semestres_pl = list(config.get("semestres", {}).keys())
        self.combo_sem_pl.addItems(semestres_pl)
        self.combo_sem_pl.currentTextChanged.connect(self._cargar_materias_plantillas)
        row_sem.addWidget(lbl_sem)
        row_sem.addWidget(self.combo_sem_pl, 1)
        cpl_lay.addLayout(row_sem)

        self.pl_container = QWidget()
        self.pl_container.setStyleSheet("background:transparent;")
        self.pl_lay = QVBoxLayout(self.pl_container)
        self.pl_lay.setSpacing(6)
        self.pl_lay.setContentsMargins(0, 0, 0, 0)
        cpl_lay.addWidget(self.pl_container)
        self.lay.addWidget(card_pl)

        if semestres_pl:
            self._cargar_materias_plantillas(semestres_pl[0])

        # ── Sección 5: Zona de peligro ────────

        self.lay.addWidget(_seccion("ZONA DE PELIGRO"))
        card4 = QFrame()
        card4.setStyleSheet(f"QFrame{{background:rgba(255,95,87,8);border:1px solid rgba(255,95,87,40);border-radius:14px;}}")
        c4_lay = QVBoxLayout(card4)
        c4_lay.setContentsMargins(20, 16, 20, 16)
        c4_lay.setSpacing(8)

        lbl_reset = QLabel("Restablecer para nuevo estudiante")
        lbl_reset.setStyleSheet(_lbl(13, TP, "600"))
        lbl_reset_sub = QLabel("Borra toda la configuración. El próximo arranque mostrará el wizard inicial. "
                               "Tus archivos académicos NO se borran.")
        lbl_reset_sub.setStyleSheet(_lbl(11, TS))
        lbl_reset_sub.setWordWrap(True)

        btn_reset = QPushButton("🗑️  Restablecer configuración")
        btn_reset.setFixedHeight(40)
        btn_reset.setStyleSheet(_btn("rgba(255,95,87,35)", RED, 9, "0 16px"))
        btn_reset.clicked.connect(self._restablecer)

        c4_lay.addWidget(lbl_reset)
        c4_lay.addWidget(lbl_reset_sub)
        c4_lay.addWidget(btn_reset)
        self.lay.addWidget(card4)
        self.lay.addStretch()

    # ── HELPERS ───────────────────────────────
    def _cargar(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _guardar_config(self, updates):
        config = self._cargar()
        config.update(updates)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def _notificar(self, msg):
        if self.parent_app and hasattr(self.parent_app, 'notificar'):
            self.parent_app.notificar("gn", "Configuración", msg)

    # ── GUARDAR DATOS PERSONALES ──────────────
    def _guardar_datos(self):
        nombre = self.inp_nombre.text().strip()
        univ   = self.inp_universidad.text().strip()
        carrera = self.inp_carrera.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Requerido", "El nombre no puede estar vacío.")
            return
        self._guardar_config({
            "nombre": nombre,
            "universidad": univ,
            "carrera": carrera
        })
        self._notificar("Datos personales actualizados")

    # ── CARPETA ───────────────────────────────
    def _elegir_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona nueva carpeta")
        if carpeta:
            self.inp_carpeta.setText(carpeta)

    def _guardar_carpeta(self):
        nueva = self.inp_carpeta.text().strip()
        if not nueva:
            QMessageBox.warning(self, "Requerido", "Selecciona una carpeta primero.")
            return
        nueva_raiz = os.path.join(nueva, "AsmoRoot")
        config = self._cargar()
        vieja_raiz = config.get("path_raiz", "")

        resp = QMessageBox.question(
            self, "Cambiar carpeta",
            f"¿Mover todos tus archivos de:\n{vieja_raiz}\n\na:\n{nueva_raiz}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if resp == QMessageBox.StandardButton.Yes:
            try:
                if vieja_raiz and os.path.exists(vieja_raiz):
                    shutil.move(vieja_raiz, nueva_raiz)
                else:
                    os.makedirs(nueva_raiz, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                return

        self._guardar_config({"path_raiz": nueva_raiz})
        self.lbl_carpeta_actual.setText(nueva_raiz)
        self._notificar("Carpeta actualizada — reinicia la app")

    # ── TEAMS ─────────────────────────────────
    def _add_clase(self):
        self._add_clase_datos()

    def _add_clase_datos(self, mat="", ini="07:30", fin="08:30", link=""):
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background:{CARDH};border:1px solid {BRD};border-radius:10px;}}")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(12, 10, 12, 10)
        c_lay.setSpacing(6)

        row1 = QHBoxLayout()
        inp_mat = QLineEdit()
        inp_mat.setPlaceholderText("Nombre de la materia")
        inp_mat.setText(mat)
        inp_mat.setFixedHeight(32)
        inp_mat.setStyleSheet(_inp())
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(26, 26)
        btn_del.setStyleSheet(f"QPushButton{{background:transparent;color:{TM};border:none;font-size:13px;}}"
                              f"QPushButton:hover{{color:{RED};}}")
        btn_del.clicked.connect(lambda: self._del_clase(card))
        row1.addWidget(inp_mat, 1)
        row1.addWidget(btn_del)
        c_lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        for lbl_txt, time_str, attr_name in [("Inicio:", ini, None), ("Fin:", fin, None)]:
            lbl = QLabel(lbl_txt)
            lbl.setStyleSheet(_lbl(11, TS))
            t = QTimeEdit()
            t.setDisplayFormat("HH:mm")
            try:
                h, m = map(int, time_str.split(":"))
                t.setTime(QTime(h, m))
            except Exception:
                t.setTime(QTime(7, 30))
            t.setFixedHeight(32)
            t.setStyleSheet(f"QTimeEdit{{background:{CARD};color:{TP};border:1px solid {BRD};"
                            f"border-radius:8px;padding:0 8px;font-size:12px;}}")
            row2.addWidget(lbl)
            row2.addWidget(t)
        row2.addStretch()
        c_lay.addLayout(row2)

        inp_link = QLineEdit()
        inp_link.setPlaceholderText("Link de Teams...")
        inp_link.setText(link)
        inp_link.setFixedHeight(32)
        inp_link.setStyleSheet(_inp())
        c_lay.addWidget(inp_link)

        self.teams_lay.insertWidget(self.teams_lay.count() - 1, card)

        children = card.findChildren(QTimeEdit)
        t_ini = children[0] if len(children) > 0 else None
        t_fin = children[1] if len(children) > 1 else None
        self.clases_widgets.append((card, inp_mat, t_ini, t_fin, inp_link))

    def _del_clase(self, card):
        self.clases_widgets = [(c, m, i, f, l) for c, m, i, f, l in self.clases_widgets if c != card]
        card.deleteLater()

    def _guardar_teams(self):
        clases = []
        for _, inp_mat, t_ini, t_fin, inp_link in self.clases_widgets:
            mat = inp_mat.text().strip()
            if mat:
                clases.append({
                    "materia": mat,
                    "hora_ini": t_ini.time().toString("HH:mm") if t_ini else "07:00",
                    "hora_fin": t_fin.time().toString("HH:mm") if t_fin else "08:00",
                    "link": inp_link.text().strip(),
                    "color": "#378ADD",
                    "icono": "📘"
                })
        self._guardar_config({"clases_teams": clases})
        self._notificar(f"{len(clases)} clase(s) guardadas")

    def _importar_excel(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Selecciona el Excel de Teams", "", "Excel (*.xlsx *.xls)")
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
            mat  = str(row[0]).strip()
            ini  = str(row[1]).strip() if row[1] else "07:00"
            fin  = str(row[2]).strip() if row[2] else "08:00"
            link = str(row[3]).strip() if row[3] else ""
            if mat:
                clases_nuevas.append((mat, ini, fin, link))

        if not clases_nuevas:
            QMessageBox.warning(self, "Aviso", "No se encontraron clases en el archivo.")
            return

        if self.clases_widgets:
            resp = QMessageBox.question(
                self, "Clases existentes",
                f"Tienes {len(self.clases_widgets)} clase(s) cargada(s).\n¿Reemplazar con las del Excel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp == QMessageBox.StandardButton.Yes:
                for card, _, _, _, _ in self.clases_widgets:
                    card.deleteLater()
                self.clases_widgets = []

        for mat, ini, fin, link in clases_nuevas:
            self._add_clase_datos(mat, ini, fin, link)

        QMessageBox.information(self, "Importado",
                                f"✓ {len(clases_nuevas)} clase(s) importadas.\nPresiona 'Guardar horario Teams' para confirmar.")

    # ── PLANTILLAS ───────────────────────────────
    def _cargar_materias_plantillas(self, semestre):
        while self.pl_lay.count():
            item = self.pl_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        config = self._cargar()
        path_raiz = config.get("path_raiz", "")
        materias = config.get("semestres", {}).get(semestre, [])

        for mat in materias:
            card = QFrame()
            card.setStyleSheet(
                f"QFrame{{background:{CARDH};border:1px solid {BRD};border-radius:10px;}}")
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(14, 10, 14, 10)
            c_lay.setSpacing(10)

            ruta_plantilla = os.path.join(path_raiz, semestre, "Plantillas", f"{mat}.docx")
            tiene = os.path.exists(ruta_plantilla) and os.path.getsize(ruta_plantilla) > 0

            ic = QLabel("✅" if tiene else "📄")
            ic.setStyleSheet("font-size:16px;border:none;background:transparent;")
            ic.setFixedWidth(24)

            lbl_mat = QLabel(mat)
            lbl_mat.setStyleSheet(_lbl(12, TP, "500"))

            estado = QLabel("Plantilla cargada" if tiene else "Sin plantilla")
            estado.setStyleSheet(_lbl(10, GRN if tiene else TM))

            info = QVBoxLayout()
            info.setSpacing(2)
            info.addWidget(lbl_mat)
            info.addWidget(estado)

            btn_subir = QPushButton("📎  Subir carátula")
            btn_subir.setFixedHeight(30)
            btn_subir.setStyleSheet(_btn(ACCD, ACCT, 7, "0 12px"))
            btn_subir.clicked.connect(
                lambda _, s=semestre, m=mat, r=ruta_plantilla, c=card:
                self._subir_plantilla(s, m, r, c))

            c_lay.addWidget(ic)
            c_lay.addLayout(info, 1)
            c_lay.addWidget(btn_subir)

            if tiene:
                btn_ver = QPushButton("↗")
                btn_ver.setFixedSize(30, 30)
                btn_ver.setStyleSheet(
                    f"QPushButton{{background:transparent;color:{ACC};"
                    f"border:none;font-size:14px;}}")
                btn_ver.clicked.connect(lambda _, r=ruta_plantilla: os.startfile(r))
                c_lay.addWidget(btn_ver)

            self.pl_lay.addWidget(card)

    def _subir_plantilla(self, semestre, materia, ruta_destino, card):
        ruta_origen, _ = QFileDialog.getOpenFileName(
            self, f"Selecciona la carátula para {materia}",
            "", "Word (*.docx)")
        if not ruta_origen:
            return
        try:
            os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
            shutil.copy(ruta_origen, ruta_destino)
            self._notificar(f"Plantilla de {materia} actualizada")
            self._cargar_materias_plantillas(semestre)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ── RESTABLECER ───────────────────────────
    def _restablecer(self):
        resp = QMessageBox.warning(
            self, "Restablecer configuración",
            "¿Estás seguro? Esto borrará toda la configuración.\n"
            "El programa mostrará el wizard la próxima vez que abra.\n\n"
            "Tus archivos académicos NO se borrarán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            try:
                os.remove(self.config_path)
            except Exception:
                pass
            QMessageBox.information(
                self, "Listo",
                "Configuración eliminada.\nCierra y vuelve a abrir AsmoRoot.")