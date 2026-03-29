from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QUrl

# ─────────────────────────────────────────────
#  NAVEGADOR INTEGRADO
# ─────────────────────────────────────────────


class MiPaginaWeb(QWebEnginePage):
    def createWindow(self, _type):
        self._url_anterior = self.url()
        self.loadFinished.connect(self._volver)
        return self

    def _volver(self, ok):
        self.loadFinished.disconnect(self._volver)
        if hasattr(self, '_url_anterior'):
            self.setUrl(self._url_anterior)

    def javaScriptConsoleMessage(self, level, message, line, source):
        # Silenciar errores molestos del sitio de la UEA que ensucian la consola
        if "TypeError" in message or "null" in message or "eva.pregrado" in source:
            return
        super().javaScriptConsoleMessage(level, message, line, source)


class PestañaNavegador(QWidget):
    def __init__(self, perfil, parent=None, url="https://www.google.com"):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.web_page = MiPaginaWeb(perfil, parent)
        self.browser = QWebEngineView()
        self.browser.setPage(self.web_page)
        self.browser.settings().setAttribute(
            self.browser.settings().WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.browser.settings().setAttribute(
            self.browser.settings().WebAttribute.LocalStorageEnabled, True)
        self.browser.setUrl(QUrl(url))
        lay.addWidget(self.browser)
