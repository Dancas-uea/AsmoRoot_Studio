import sys
import os
import json
import shutil
from datetime import datetime
import win32com.client
from PIL import Image
import os
from google import genai

from PIL import Image
# Busca esta línea al principio de tu archivo y asegúrate de que QMenu esté ahí:
from PyQt6.QtWidgets import (QApplication,QDialog, QMainWindow,QTextEdit, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QComboBox, QFrame,
                             QTreeWidget, QTreeWidgetItem, QMessageBox, QInputDialog,
                             QScrollArea, QSpacerItem, QSizePolicy, QMenu) # <--- AGREGA ESTO AQUÍ

from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView

from PyQt6.QtCore import QMimeData
from PyQt6.QtGui import QDrag


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

class AsmoRootApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AsmoRoot - Academic Management System v12.0")
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
        self.version_sistema = "v12.0"

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

        # ESPACIADOR PARA EMPUJAR EL BOTÓN ABAJO


        # Nuevo Semestre
        self.btn_new_sem = QPushButton("+ NUEVO SEMESTRE")
        self.btn_new_sem.setStyleSheet(
            f"background: {self.azul_pro}; color: white; font-weight: bold; padding: 12px; border-radius: 6px; margin: 5px 0px;")
        self.btn_new_sem.clicked.connect(self.crear_nuevo_semestre)
        sidebar_layout.addWidget(self.btn_new_sem)

        # Barra de Estado (Ubicada al final)
        self.status_bar_label = QLabel(f" Sistema AsmoRoot Listo | Versión {self.version_sistema}")
        self.status_bar_label.setStyleSheet(
            f"color: #8B949E; font-size: 11px; padding: 5px; border-top: 1px solid {self.gris_borde};")
        sidebar_layout.addWidget(self.status_bar_label)

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
        self.browser_frame = QFrame()
        self.browser_frame.setStyleSheet(
            f"background: {self.fondo_card}; border: 1px solid {self.gris_borde}; border-radius: 8px;")
        browser_vbox = QVBoxLayout(self.browser_frame)

        # Header del Navegador con Título y Botón de Expansión
        header_moodle = QHBoxLayout()
        lbl_moodle = QLabel("📅 PRÓXIMAS TAREAS (MOODLE)")
        lbl_moodle.setStyleSheet(f"color: {self.azul_pro}; font-weight: bold; border: none;")

        self.btn_expandir = QPushButton("⛶")  # Icono de pantalla completa
        self.btn_expandir.setFixedSize(35, 30)
        self.btn_expandir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_expandir.setStyleSheet(f"""
                    QPushButton {{
                        background: #21262d; 
                        color: {self.azul_pro}; 
                        font-weight: bold;
                        border: 1px solid {self.gris_borde}; 
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        background: {self.azul_pro};
                        color: white;
                    }}
                """)
        self.btn_expandir.clicked.connect(self.toggle_moodle_fullscreen)

        header_moodle.addStretch()  # Empuja el título al centro
        header_moodle.addWidget(lbl_moodle)
        header_moodle.addStretch()  # Empuja el botón a la derecha
        header_moodle.addWidget(self.btn_expandir)
        browser_vbox.addLayout(header_moodle)

        # Configuración del Perfil Persistente y Motor del Navegador
        from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

        self.perfil_persistente = QWebEngineProfile("Storage_AsmoRoot", self)
        ruta_datos = os.path.join(PATH_RAIZ, "Navegador_Datos")
        self.perfil_persistente.setPersistentStoragePath(ruta_datos)

        # Fuerza al navegador a usar tu carpeta de la Universidad como base
        self.perfil_persistente.setDownloadPath(PATH_RAIZ)

        self.perfil_persistente.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.perfil_persistente.setHttpAcceptLanguage("es-ES,es;q=0.9")

        self.web_page = QWebEnginePage(self.perfil_persistente, self)
        self.browser = QWebEngineView()
        self.browser.setPage(self.web_page)
        self.browser.setUrl(QUrl("https://eva.pregrado.uea.edu.ec/eva2526/web/my/courses.php?lang=es"))

        browser_vbox.addWidget(self.browser)
        browser_vbox.setContentsMargins(5, 5, 5, 5)
        self.browser_frame.setFixedHeight(800)
        self.content_layout.addWidget(self.browser_frame)

        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)

    # --- LÓGICA ---
    def obtener_semestres_raiz(self):
        if not os.path.exists(PATH_RAIZ): return []
        return [f for f in os.listdir(PATH_RAIZ) if os.path.isdir(os.path.join(PATH_RAIZ, f)) and f != "Logo"]

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
            mat = item.parent().text(0).split(" ", 1)[-1]
            sem = item.parent().parent().text(0).split(" ", 1)[-1]
            os.startfile(os.path.join(PATH_RAIZ, sem, mat, item.text(0).split(" ", 1)[-1]))

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



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AsmoRootApp()
    window.show()
    sys.exit(app.exec())