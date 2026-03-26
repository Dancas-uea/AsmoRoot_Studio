"""
StatusBar - Barra de estado inferior de la aplicación
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizeGrip
from PyQt6.QtCore import Qt
from styles.helpers import t, label_style


class StatusBar(QFrame):
    """Barra de estado inferior con información del sistema y grip de redimensionamiento."""

    def __init__(self, parent, version_sistema):
        super().__init__(parent)
        self.parent = parent
        self.version_sistema = version_sistema

        self.setFixedHeight(28)
        self.setStyleSheet(f"background:{t('bar')};border-top:1px solid {t('brd')};")

        self._setup_ui()

    def _setup_ui(self):
        """Construye la interfaz de la barra de estado."""
        sb_lay = QHBoxLayout(self)
        sb_lay.setContentsMargins(14, 0, 14, 0)
        sb_lay.setSpacing(10)

        # Indicador de estado (punto verde)
        self.dot = QLabel("●")
        self.dot.setStyleSheet(f"color:{t('grn')};font-size:9px;border:none;")

        # Mensaje principal
        self.sb_lbl = QLabel("Sistema listo")
        self.sb_lbl.setStyleSheet(label_style(10, "ts"))

        # Separador
        sep = QLabel("·")
        sep.setStyleSheet(label_style(10, "tm"))

        # Mensaje secundario
        self.sb_lbl2 = QLabel("")
        self.sb_lbl2.setStyleSheet(label_style(10, "ts"))

        # Versión
        ver = QLabel(f"AsmoRoot {self.version_sistema}")
        ver.setStyleSheet(label_style(10, "tm"))

        sb_lay.addWidget(self.dot)
        sb_lay.addWidget(self.sb_lbl)
        sb_lay.addWidget(sep)
        sb_lay.addWidget(self.sb_lbl2)
        sb_lay.addStretch()
        sb_lay.addWidget(ver)

        # Grip nativo de resize
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        sb_lay.addWidget(grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

    def set_mensaje_principal(self, mensaje):
        """Establece el mensaje principal de la barra de estado."""
        self.sb_lbl.setText(mensaje)

    def set_mensaje_secundario(self, mensaje):
        """Establece el mensaje secundario de la barra de estado."""
        self.sb_lbl2.setText(mensaje)

    def set_estado(self, estado, color="grn"):
        """Cambia el estado visual (punto de color)."""
        self.dot.setStyleSheet(f"color:{t(color)};font-size:9px;border:none;")
        self.set_mensaje_principal(estado)

    def limpiar_mensajes(self):
        """Limpia los mensajes de la barra de estado."""
        self.sb_lbl.setText("Sistema listo")
        self.sb_lbl2.setText("")
        self.dot.setStyleSheet(f"color:{t('grn')};font-size:9px;border:none;")

    def actualizar_tema(self):
        """Actualiza los estilos cuando cambia el tema."""
        self.setStyleSheet(f"background:{t('bar')};border-top:1px solid {t('brd')};")
        self.dot.setStyleSheet(f"color:{t('grn')};font-size:9px;border:none;")
        self.sb_lbl.setStyleSheet(label_style(10, "ts"))
        self.sb_lbl2.setStyleSheet(label_style(10, "ts"))