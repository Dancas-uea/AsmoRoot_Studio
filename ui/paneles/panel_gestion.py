"""
Panel Gestión - Centro de gestión académica para crear tareas y generar PDFs
"""

import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt
from styles.helpers import t, btn_style, input_style, label_style
import win32com.client


class PanelGestion(QScrollArea):
    def __init__(self, parent_app, path_raiz):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.path_raiz = path_raiz
        self.archivo_docx_sesion = ""
        self.archivo_pdf_sesion = ""

        self.setWidgetResizable(True)
        self.setStyleSheet("border:none;background:transparent;")

        self._construir_panel()
        self._cargar_semestres()

    def _cargar_semestres(self):
        if hasattr(self.parent_app, 'obtener_semestres_raiz'):
            semestres = self.parent_app.obtener_semestres_raiz()
            self.sem_menu.clear()
            self.sem_menu.addItems(semestres)
            if hasattr(self.parent_app, 'config'):
                u_sem = self.parent_app.config.get("ultimo_semestre", "")
                if u_sem and u_sem in semestres:
                    self.sem_menu.setCurrentText(u_sem)
                    self._actualizar_materias(u_sem)
                    self.mat_menu.setCurrentText(self.parent_app.config.get("ultima_materia", ""))

    def _construir_panel(self):
        self.inner = QWidget()
        self.inner.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self.inner)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(20)

        ttl = QLabel("CENTRO DE GESTIÓN ACADÉMICA")
        ttl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ttl.setStyleSheet(label_style(22, "tp", "600"))
        lay.addWidget(ttl)

        mid = QHBoxLayout()
        mid.setSpacing(16)
        self._crear_card_inputs(mid)
        self._crear_botones_principales(mid)
        lay.addLayout(mid)

        self._crear_modo_recuperacion(lay)
        lay.addStretch()
        self.setWidget(self.inner)

    def _crear_card_inputs(self, parent_layout):
        self.card_inputs = QFrame()
        self.card_inputs.setStyleSheet(
            f"QFrame{{background:{t('card')};border:1px solid {t('brd')};border-radius:14px;}}")
        form_lay = QVBoxLayout(self.card_inputs)
        form_lay.setContentsMargins(20, 18, 20, 18)
        form_lay.setSpacing(12)

        lbl_sem = QLabel("Seleccione el semestre")
        lbl_sem.setStyleSheet(label_style(11, "tm", "500"))
        self.sem_menu = QComboBox()
        self.sem_menu.setFixedHeight(40)
        self.sem_menu.setStyleSheet(input_style())
        self.sem_menu.currentTextChanged.connect(self._actualizar_materias)
        form_lay.addWidget(lbl_sem)
        form_lay.addWidget(self.sem_menu)

        lbl_mat = QLabel("Seleccione la materia")
        lbl_mat.setStyleSheet(label_style(11, "tm", "500"))
        self.mat_menu = QComboBox()
        self.mat_menu.setFixedHeight(40)
        self.mat_menu.setStyleSheet(input_style())
        self.mat_menu.currentTextChanged.connect(self._guardar_materia_seleccionada)
        form_lay.addWidget(lbl_mat)
        form_lay.addWidget(self.mat_menu)

        lbl_semana = QLabel("Semana de trabajo")
        lbl_semana.setStyleSheet(label_style(11, "tm", "500"))
        self.sem_ent = QLineEdit()
        self.sem_ent.setPlaceholderText("Ej: Semana 10")
        self.sem_ent.setFixedHeight(40)
        self.sem_ent.setStyleSheet(input_style())
        form_lay.addWidget(lbl_semana)
        form_lay.addWidget(self.sem_ent)

        lbl_tema = QLabel("Tema de la tarea")
        lbl_tema.setStyleSheet(label_style(11, "tm", "500"))
        self.tema_ent = QLineEdit()
        self.tema_ent.setPlaceholderText("Escriba el título de la tarea…")
        self.tema_ent.setFixedHeight(40)
        self.tema_ent.setStyleSheet(input_style())
        form_lay.addWidget(lbl_tema)
        form_lay.addWidget(self.tema_ent)

        parent_layout.addWidget(self.card_inputs, 3)

    def _crear_botones_principales(self, parent_layout):
        col_btns = QVBoxLayout()
        col_btns.setSpacing(10)

        botones = [
            ("🚀  Iniciar Nueva Tarea", t('acc'), self._iniciar_flujo),
            ("📄  Generar PDF",         "#21618C", self._generar_pdf),
            ("✅  Finalizar",           "#7f0000", self._reset_ui),
        ]

        for txt, color, func in botones:
            b = QPushButton(txt)
            b.setFixedHeight(58)
            b.setStyleSheet(
                f"QPushButton{{background:{color};color:white;border:none;border-radius:12px;"
                f"padding:0 20px;font-size:14px;font-weight:600;"
                f"font-family:'SF Pro Display','Segoe UI',sans-serif;}}"
                f"QPushButton:hover{{border:1px solid rgba(255,255,255,50);}}"
                f"QPushButton:pressed{{opacity:0.8;}}")
            b.clicked.connect(func)
            col_btns.addWidget(b)

        self.btn_start     = col_btns.itemAt(0).widget()
        self.btn_pdf_main  = col_btns.itemAt(1).widget()
        self.btn_finalizar = col_btns.itemAt(2).widget()

        col_btns.addStretch()
        parent_layout.addLayout(col_btns, 1)

    def _crear_modo_recuperacion(self, parent_layout):
        self.fix_box = QFrame()
        self.fix_box.setStyleSheet(
            f"QFrame{{background:{t('card')};border:1px solid {t('brd')};border-radius:14px;}}")
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
        self.btn_fix_word.clicked.connect(self._reabrir_word)

        self.btn_fix_pdf = QPushButton("📄  Actualizar PDF Histórico")
        self.btn_fix_pdf.setFixedHeight(38)
        self.btn_fix_pdf.setStyleSheet(btn_style(t('acc'), "white", 9, "0 16px"))
        self.btn_fix_pdf.setEnabled(False)
        self.btn_fix_pdf.clicked.connect(self._generar_pdf)

        btns_fix.addWidget(self.btn_fix_word)
        btns_fix.addWidget(self.btn_fix_pdf)
        fix_lay.addLayout(btns_fix)
        parent_layout.addWidget(self.fix_box)

    # ── TEMA ─────────────────────────────────
    def actualizar_tema(self):
        """Reaaplica estilos con el tema activo."""
        self.card_inputs.setStyleSheet(
            f"QFrame{{background:{t('card')};border:1px solid {t('brd')};border-radius:14px;}}")
        self.fix_box.setStyleSheet(
            f"QFrame{{background:{t('card')};border:1px solid {t('brd')};border-radius:14px;}}")
        self.sem_menu.setStyleSheet(input_style())
        self.mat_menu.setStyleSheet(input_style())
        self.sem_ent.setStyleSheet(input_style())
        self.tema_ent.setStyleSheet(input_style())

    # ── SEMESTRES / MATERIAS ──────────────────
    def actualizar_semestres(self, semestres):
        self.sem_menu.clear()
        self.sem_menu.addItems(semestres)
        if hasattr(self.parent_app, 'config'):
            u_sem = self.parent_app.config.get("ultimo_semestre", "")
            if u_sem and u_sem in semestres:
                self.sem_menu.setCurrentText(u_sem)

    def cargar_ultima_sesion(self, ultimo_semestre, ultima_materia):
        if ultimo_semestre:
            items = [self.sem_menu.itemText(i) for i in range(self.sem_menu.count())]
            if ultimo_semestre in items:
                self.sem_menu.setCurrentText(ultimo_semestre)
                self._actualizar_materias(ultimo_semestre)
                if ultima_materia:
                    self.mat_menu.setCurrentText(ultima_materia)

    def seleccionar_desde_arbol(self, semestre, materia, archivo):
        self.sem_menu.setCurrentText(semestre)
        self._actualizar_materias(semestre)
        self.mat_menu.setCurrentText(materia)
        self.archivo_docx_sesion = os.path.join(self.path_raiz, semestre, materia, archivo)

        try:
            nombre_sin_ext = os.path.splitext(archivo)[0]
            partes = nombre_sin_ext.split('_')
            semana = ""
            tema = ""
            for i, parte in enumerate(partes):
                if "Semana" in parte:
                    semana = parte.replace("Semana-", "")
                    tema_partes = partes[1:i]
                    tema = " ".join(tema_partes).replace("-", " ")
                    break
            if not semana:
                semana = archivo.split("_")[-1].replace(".docx", "").replace("Semana-", "")
            if not tema:
                tema = archivo.split("_")[1] if len(archivo.split("_")) > 1 else "Tarea"
            self.sem_ent.setText(f"Semana {semana}")
            self.tema_ent.setText(tema)
        except Exception:
            pass

        self.status_ind.setText("● TAREA DETECTADA")
        self.status_ind.setStyleSheet(label_style(11, "acc", "600"))
        self.btn_fix_word.setEnabled(True)
        self.btn_fix_pdf.setEnabled(True)

        if hasattr(self.parent_app, 'notificar'):
            self.parent_app.notificar("bl", "Archivo cargado", archivo[:40])

    def _actualizar_materias(self, semestre):
        if not semestre:
            return
        self.mat_menu.clear()
        ruta = os.path.join(self.path_raiz, semestre)
        if os.path.exists(ruta):
            mats = sorted([m for m in os.listdir(ruta)
                           if os.path.isdir(os.path.join(ruta, m)) and m != "Plantillas"])
            self.mat_menu.addItems(mats)
            if hasattr(self.parent_app, 'guardar_config') and hasattr(self.parent_app, 'config'):
                self.parent_app.config["ultimo_semestre"] = semestre
                self.parent_app.guardar_config()

    def _guardar_materia_seleccionada(self, mat):
        if mat and hasattr(self.parent_app, 'guardar_config') and hasattr(self.parent_app, 'config'):
            self.parent_app.config["ultima_materia"] = mat
            self.parent_app.guardar_config()

    def _iniciar_flujo(self):
        try:
            sem   = self.sem_menu.currentText()
            mat   = self.mat_menu.currentText()
            sema  = self.sem_ent.text()
            tema  = self.tema_ent.text()

            if not all([mat, sema, tema]):
                if hasattr(self.parent_app, 'notificar'):
                    self.parent_app.notificar("or", "Campos incompletos", "Rellena todos los campos")
                return

            fecha    = datetime.now().strftime('%Y-%m-%d')
            ini_mat  = "".join([p[0].upper() for p in mat.split() if p.lower() not in ["de", "la", "el", "y"]])
            solo_num = "".join(filter(str.isdigit, sema))
            nombre   = f"{fecha}_{tema.replace(' ', '-')}_{ini_mat}_Semana-{solo_num or 'X'}.docx"

            self.archivo_docx_sesion = os.path.join(self.path_raiz, sem, mat, nombre)
            plantilla = os.path.join(self.path_raiz, sem, "Plantillas", f"{mat}.docx")

            if os.path.exists(plantilla):
                shutil.copy(plantilla, self.archivo_docx_sesion)
                os.startfile(self.archivo_docx_sesion)
                self.status_ind.setText("● EDITANDO")
                self.status_ind.setStyleSheet(label_style(11, "yel", "600"))
                self.btn_fix_word.setEnabled(True)
                self.btn_fix_pdf.setEnabled(True)
                if hasattr(self.parent_app, 'actualizar_arbol'):
                    self.parent_app.actualizar_arbol()
                if hasattr(self.parent_app, '_agregar_pestana_archivo'):
                    self.parent_app._agregar_pestana_archivo(self.archivo_docx_sesion)
                if hasattr(self.parent_app, 'notificar'):
                    self.parent_app.notificar("bl", "Nueva Tarea", f"Iniciando en {mat}")
            else:
                if hasattr(self.parent_app, 'notificar'):
                    self.parent_app.notificar("or", "Sin plantilla", f"No hay plantilla para {mat}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _generar_pdf(self):
        if not os.path.exists(self.archivo_docx_sesion):
            if hasattr(self.parent_app, 'notificar'):
                self.parent_app.notificar("or", "Sin documento", "Inicia una tarea primero")
            return
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(self.archivo_docx_sesion)
            path_pdf = self.archivo_docx_sesion.replace(".docx", ".pdf")
            doc.SaveAs(path_pdf, FileFormat=17)
            doc.Close()
            word.Quit()
            if hasattr(self.parent_app, 'actualizar_arbol'):
                self.parent_app.actualizar_arbol()
            self.status_ind.setText("● TAREA FINALIZADA")
            self.status_ind.setStyleSheet(label_style(11, "grn", "600"))
            if hasattr(self.parent_app, 'notificar'):
                self.parent_app.notificar("gn", "PDF generado", "Guardado correctamente")
        except Exception as e:
            if hasattr(self.parent_app, 'notificar'):
                self.parent_app.notificar("rd", "Error PDF", str(e)[:60])

    def _reabrir_word(self):
        if os.path.exists(self.archivo_docx_sesion):
            os.startfile(self.archivo_docx_sesion)
            if hasattr(self.parent_app, 'notificar'):
                self.parent_app.notificar("bl", "Word abierto", os.path.basename(self.archivo_docx_sesion)[:40])

    def _reset_ui(self):
        self.tema_ent.clear()
        self.sem_ent.clear()
        self.status_ind.setText("● REPOSO")
        self.status_ind.setStyleSheet(label_style(11, "tm", "600"))
        self.btn_fix_word.setEnabled(False)
        self.btn_fix_pdf.setEnabled(False)
        self.archivo_docx_sesion = ""
        if hasattr(self.parent_app, 'notificar'):
            self.parent_app.notificar("or", "Finalizado", "Tarea archivada")