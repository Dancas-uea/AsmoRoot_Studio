"""
Panel UEA - Navegador integrado para la plataforma educativa
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QStackedWidget, QMessageBox
)
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from styles.helpers import t, btn_style, input_style, label_style


# ─────────────────────────────────────────────
#  CLASES AUXILIARES DEL NAVEGADOR
# ─────────────────────────────────────────────
from widgets.navegador import MiPaginaWeb,PestañaNavegador


# ─────────────────────────────────────────────
#  PANEL PRINCIPAL UEA
# ─────────────────────────────────────────────
class PanelUEA(QWidget):
    def __init__(self, parent_app, path_raiz):
        super().__init__(parent_app)
        self.parent_app = parent_app          # Referencia a AsmoRootApp
        self.path_raiz = path_raiz
        self.pestanas = []                    # Lista de (btn, widget, fija)

        self._setup_ui()
        self._setup_profiles()
        self._crear_pestana_inicial()

    # ── CONSTRUCCIÓN UI ──────────────────────────
    def _setup_ui(self):
        """Construye la interfaz del panel."""
        self.setStyleSheet("background:transparent;")
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Barra de pestañas
        self._crear_barra_tabs()
        main_lay.addWidget(self.tabs_bar)

        # Barra de URL
        self._crear_barra_url()
        main_lay.addWidget(self.url_bar_frame)

        # Stack de navegadores
        self.stack_browsers = QStackedWidget()
        self.stack_browsers.setStyleSheet("background:transparent;border:none;")
        main_lay.addWidget(self.stack_browsers, 1)

    def _crear_barra_tabs(self):
        """Crea la barra con pestañas y botones de control."""
        self.tabs_bar = QFrame()
        self.tabs_bar.setFixedHeight(44)
        self.tabs_bar.setStyleSheet(f"background:{t('bar')};border-bottom:1px solid {t('brd')};")

        bar_lay = QHBoxLayout(self.tabs_bar)
        bar_lay.setContentsMargins(10, 7, 10, 7)
        bar_lay.setSpacing(5)

        # Botón toggle sidebar (conectado desde main_window)
        self.btn_sb_tog = QPushButton("☰")
        self.btn_sb_tog.setFixedSize(30, 30)
        self.btn_sb_tog.setStyleSheet(
            f"QPushButton{{background:{t('card')};border:1px solid {t('brd')};border-radius:8px;"
            f"color:{t('ts')};font-size:14px;}}"
            f"QPushButton:hover{{background:{t('cardh')};}}")
        self.btn_sb_tog.setToolTip("Mostrar/ocultar sidebar")
        bar_lay.addWidget(self.btn_sb_tog)

        # Contenedor de pestañas
        self.tabs_container = QWidget()
        self.tabs_container_lay = QHBoxLayout(self.tabs_container)
        self.tabs_container_lay.setContentsMargins(0, 0, 0, 0)
        self.tabs_container_lay.setSpacing(3)
        self.tabs_container_lay.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinimumSize)
        bar_lay.addWidget(self.tabs_container)

        # Botón nueva pestaña
        btn_new_tab = QPushButton("+")
        btn_new_tab.setFixedSize(26, 26)
        btn_new_tab.setStyleSheet(
            f"QPushButton{{background:{t('card')};color:{t('tm')};border:1px solid {t('brd')};"
            f"border-radius:50%;font-size:16px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{t('cardh')};}}")
        btn_new_tab.setToolTip("Nueva pestaña")
        btn_new_tab.clicked.connect(lambda: self.nueva_pestana())
        bar_lay.addWidget(btn_new_tab)

        bar_lay.addStretch(1)

        # Botón panel descargas (conectado desde main_window)
        self.btn_dl_nav = QPushButton("⬇  0")
        self.btn_dl_nav.setFixedHeight(28)
        self.btn_dl_nav.setStyleSheet(
            f"QPushButton{{background:{t('accd')};color:{t('acct')};"
            f"border:1px solid rgba(55,138,221,80);border-radius:7px;padding:0 11px;"
            f"font-size:11px;font-weight:600;}}"
            f"QPushButton:hover{{background:rgba(55,138,221,70);}}")
        self.btn_dl_nav.setToolTip("Panel de descargas")
        bar_lay.addWidget(self.btn_dl_nav)

    def _crear_barra_url(self):
        """Crea la barra de navegación con URL."""
        self.url_bar_frame = QFrame()
        self.url_bar_frame.setFixedHeight(40)
        self.url_bar_frame.setStyleSheet(f"background:{t('bar')};border-bottom:1px solid {t('brd')};")

        url_lay = QHBoxLayout(self.url_bar_frame)
        url_lay.setContentsMargins(10, 6, 10, 6)
        url_lay.setSpacing(5)

        # Botones de navegación
        for txt, tip, fn in [
            ("←", "Atrás",    lambda: self._browser_actual().back()),
            ("→", "Adelante", lambda: self._browser_actual().forward()),
            ("↻", "Recargar", lambda: self._browser_actual().reload()),
        ]:
            b = QPushButton(txt)
            b.setFixedSize(26, 26)
            b.setToolTip(tip)
            b.setStyleSheet(
                f"QPushButton{{background:{t('card')};border:1px solid {t('brd')};"
                f"border-radius:7px;color:{t('tm')};font-size:12px;}}"
                f"QPushButton:hover{{background:{t('cardh')};color:{t('tp')};}}")
            b.clicked.connect(fn)
            url_lay.addWidget(b)

        # Campo de URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Buscar en Google o ingresar URL…")
        self.url_input.setFixedHeight(28)
        self.url_input.setStyleSheet(
            f"QLineEdit{{background:{t('inp')};color:{t('ts')};border:1px solid {t('brd')};"
            f"border-radius:8px;padding:0 12px;font-size:11.5px;}}"
            f"QLineEdit:focus{{border:1px solid {t('acc')};background:rgba(55,138,221,10);}}")
        self.url_input.returnPressed.connect(self._navegar_url)
        url_lay.addWidget(self.url_input, 1)

    def _setup_profiles(self):
        """Configura los perfiles de navegación persistentes."""
        # Perfil para UEA (cookies persistentes)
        self.perfil_persistente = QWebEngineProfile("Storage_AsmoRoot", self)
        ruta_datos = os.path.join(self.path_raiz, "Navegador_Datos")
        self.perfil_persistente.setPersistentStoragePath(ruta_datos)
        self.perfil_persistente.setDownloadPath(os.path.join(os.path.expanduser("~"), "Downloads"))
        self.perfil_persistente.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.perfil_persistente.setHttpAcceptLanguage("es-ES,es;q=0.9")
        self.perfil_persistente.downloadRequested.connect(self._gestionar_descarga)

        # Perfil para Google (cookies separadas)
        self.perfil_google = QWebEngineProfile("Storage_Google", self)
        ruta_google = os.path.join(self.path_raiz, "Google_Datos")
        self.perfil_google.setPersistentStoragePath(ruta_google)
        self.perfil_google.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.perfil_google.setHttpAcceptLanguage("es-ES,es;q=0.9")
        self.perfil_google.downloadRequested.connect(self._gestionar_descarga)

    def _crear_pestana_inicial(self):
        """Crea la pestaña inicial con la plataforma UEA."""
        self.nueva_pestana(
            url="https://eva.pregrado.uea.edu.ec/eva2526/web/my/courses.php?lang=es",
            titulo="🎓 UEA",
            fija=True
        )

    # ── MÉTODOS PÚBLICOS ─────────────────────────
    def actualizar_contador_descargas(self, contador):
        """Actualiza el contador de descargas en el botón."""
        self.btn_dl_nav.setText(f"⬇  {contador}")

    def get_browser_actual(self):
        """Devuelve el navegador activo (para uso externo)."""
        return self._browser_actual()

    # ── MÉTODOS INTERNOS DEL NAVEGADOR ───────────
    def nueva_pestana(self, url=None, titulo="Nueva pestaña", fija=False):
        """Crea una nueva pestaña en el navegador."""
        if url is None:
            url = "https://www.google.com"

        # Seleccionar perfil según dominio
        perfil = self.perfil_persistente if "uea.edu.ec" in url else self.perfil_google
        pestana = PestañaNavegador(perfil, self, url)

        btn_tab = QPushButton(titulo[:22])
        btn_tab.setFixedHeight(26)
        btn_tab.setMinimumWidth(55)
        btn_tab.setMaximumWidth(120)
        btn_tab.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_tab.setStyleSheet(self._tab_style(False))

        # Conectar señales
        pestana.browser.titleChanged.connect(
            lambda t_txt, b=btn_tab, f=fija:
            b.setText(("🎓 UEA" if f else t_txt[:20]) if t_txt else "Nueva pestaña"))

        pestana.browser.urlChanged.connect(
            lambda url_obj:
            self.url_input.setText(
                "" if url_obj.toString().startswith("file:///") else url_obj.toString())
            if self._browser_actual() == pestana.browser else None)

        if not fija:
            btn_cerrar = QPushButton("✕")
            btn_cerrar.setFixedSize(15, 15)
            btn_cerrar.setStyleSheet(
                f"background:transparent;color:{t('tm')};border:none;font-size:9px;")
            btn_cerrar.clicked.connect(lambda: self._cerrar_pestana(btn_tab))

            tab_w = QWidget()
            tl = QHBoxLayout(tab_w)
            tl.setContentsMargins(0, 0, 0, 0)
            tl.setSpacing(2)
            tl.addWidget(btn_tab)
            tl.addWidget(btn_cerrar)
            self.tabs_container_lay.addWidget(tab_w)
        else:
            self.tabs_container_lay.addWidget(btn_tab)

        btn_tab.clicked.connect(lambda: self._cambiar_pestana(btn_tab))
        self.pestanas.append((btn_tab, pestana, fija))
        self.stack_browsers.addWidget(pestana)
        self._cambiar_pestana(btn_tab)

    def _tab_style(self, activo):
        """Estilo para las pestañas."""
        if activo:
            return (f"QPushButton{{background:{t('accd')};color:{t('acct')};"
                    f"border:1px solid rgba(55,138,221,80);border-radius:7px;"
                    f"padding:0 8px;font-size:11px;text-align:left;}}")
        return (f"QPushButton{{background:{t('card')};color:{t('ts')};"
                f"border:1px solid {t('brd')};border-radius:7px;padding:0 8px;"
                f"font-size:11px;text-align:left;}}"
                f"QPushButton:hover{{background:{t('cardh')};}}")

    def _cambiar_pestana(self, btn_activo):
        """Cambia a la pestaña seleccionada."""
        for btn, pestana, fija in self.pestanas:
            activo = (btn == btn_activo)
            btn.setProperty("activa", activo)
            btn.setStyleSheet(self._tab_style(activo))
            if activo:
                self.stack_browsers.setCurrentWidget(pestana)
                url_str = pestana.browser.url().toString()
                self.url_input.setText("" if url_str.startswith("file:///") else url_str)

    def _cerrar_pestana(self, btn_tab):
        """Cierra una pestaña del navegador."""
        if len(self.pestanas) <= 1:
            return

        for i, (btn, pestana, fija) in enumerate(self.pestanas):
            if btn == btn_tab and not fija:
                self.pestanas.pop(i)
                # Eliminar widget de la barra de tabs
                for j in range(self.tabs_container_lay.count()):
                    w = self.tabs_container_lay.itemAt(j).widget()
                    if w and (btn_tab == w or btn_tab in w.findChildren(QPushButton)):
                        self.tabs_container_lay.takeAt(j).widget().deleteLater()
                        break
                self.stack_browsers.removeWidget(pestana)
                pestana.deleteLater()
                self._cambiar_pestana(self.pestanas[max(0, i - 1)][0])
                break

    def _navegar_url(self):
        """Navega a la URL ingresada."""
        url = self.url_input.text().strip()
        if not url:
            return
        if not url.startswith("http"):
            url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
        self._browser_actual().setUrl(QUrl(url))

    def _browser_actual(self):
        """Devuelve el navegador activo actual."""
        for btn, pestana, fija in self.pestanas:
            if btn.property("activa"):
                return pestana.browser
        return self.pestanas[0][1].browser if self.pestanas else None

    def _gestionar_descarga(self, download):
        """Gestiona la descarga de archivos."""
        carpeta = os.path.join(os.path.expanduser("~"), "Downloads")
        nombre = download.suggestedFileName()
        ruta_final = os.path.join(carpeta, nombre)

        # Manejar archivos existentes
        if os.path.exists(ruta_final):
            resp = QMessageBox.question(
                self, "Archivo existe", f'"{nombre}" ya existe.\n¿Reemplazar?',
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

        # Notificar a la app principal
        if hasattr(self.parent_app, 'notificar'):
            self.parent_app.notificar("bl", "Descargando", nombre[:40])

        # Conectar señal para aumentar contador cuando termine
        def on_finished():
            if hasattr(self.parent_app, 'aumentar_contador_descargas'):
                self.parent_app.aumentar_contador_descargas()
        download.isFinishedChanged.connect(on_finished)