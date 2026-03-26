import os
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer, QPoint
)
from PyQt6.QtGui import QColor

from styles.helpers import t, label_style, btn_style
from core.monitor import MonitorArchivo

# ─────────────────────────────────────────────
#  BOTÓN CON ANIMACIÓN HOVER (macOS style)
# ─────────────────────────────────────────────


class MacButton(QPushButton):
    """Botón con efecto de escala al hover como macOS."""
    def __init__(self, texto="", parent=None):
        super().__init__(texto, parent)
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._base_geo = None

    def enterEvent(self, e):
        super().enterEvent(e)
        if self._base_geo is None:
            self._base_geo = self.geometry()
        geo = self._base_geo
        expand = 2
        self._anim.setStartValue(geo)
        self._anim.setEndValue(QRect(
            geo.x() - expand, geo.y() - expand,
            geo.width() + expand * 2, geo.height() + expand * 2
        ))
        self._anim.start()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        if self._base_geo:
            self._anim.setStartValue(self.geometry())
            self._anim.setEndValue(self._base_geo)
            self._anim.start()


# ─────────────────────────────────────────────
#  PESTAÑA ARCHIVO ABIERTO
# ─────────────────────────────────────────────


class PestanaArchivo(QFrame):
    def __init__(self, ruta, parent_app):
        super().__init__()
        self.ruta = ruta
        self.parent_app = parent_app
        self.nombre = os.path.basename(ruta)
        self.es_pdf = ruta.endswith(".pdf")
        self.setFixedHeight(42)
        self.setStyleSheet(f"""
            PestanaArchivo {{
                background: {t('card')};
                border: 1px solid {t('accd')};
                border-radius: 10px;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 0, 8, 0)
        lay.setSpacing(6)

        badge = QLabel("P" if self.es_pdf else "W")
        badge.setFixedSize(26, 26)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = "rgba(163,45,45,90)" if self.es_pdf else "rgba(24,95,165,90)"
        txt = "#F09595" if self.es_pdf else "#85B7EB"
        badge.setStyleSheet(f"background:{color};color:{txt};border-radius:6px;font-weight:700;font-size:10px;border:none;")

        info = QVBoxLayout()
        info.setSpacing(0)
        nlab = QLabel(self.nombre[:28] + "…" if len(self.nombre) > 28 else self.nombre)
        nlab.setStyleSheet(label_style(10, "tp", "600"))
        tlab = QLabel("PDF · abierto" if self.es_pdf else "Word · abierto")
        tlab.setStyleSheet(label_style(9, "acct"))
        info.addWidget(nlab)
        info.addWidget(tlab)

        btn_r = QPushButton("▶")
        btn_r.setFixedSize(20, 20)
        btn_r.setStyleSheet(f"background:transparent;color:{t('acc')};border:none;font-size:11px;")
        btn_r.clicked.connect(self.reabrir)

        btn_c = QPushButton("✕")
        btn_c.setFixedSize(16, 16)
        btn_c.setStyleSheet(f"background:transparent;color:{t('tm')};border:none;font-size:10px;")
        btn_c.clicked.connect(self.cerrar)

        lay.addWidget(badge)
        lay.addLayout(info)
        lay.addStretch()
        lay.addWidget(btn_r)
        lay.addWidget(btn_c)

    def reabrir(self):
        try:
            os.startfile(self.ruta)
        except Exception as e:
            print(f"Error reabriendo archivo: {e}")

    def cerrar(self):
        try:
            self.parent_app.cerrar_pestana_archivo(self)
        except Exception as e:
            print(f"Error cerrando pestaña: {e}")


# ─────────────────────────────────────────────
#  NOTIFICACIÓN TOAST (macOS animada)
# ─────────────────────────────────────────────


class Notificacion(QFrame):
    def __init__(self, tipo, titulo, mensaje, parent):
        super().__init__(parent)
        colores = {
            "gn": "#28c840",
            "bl": "#378ADD",
            "or": "#febc2e",
            "rd": "#ff5f57",
        }
        acc = colores.get(tipo, "#378ADD")
        self.setFixedWidth(300)
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(18,18,36,240);
                border: 1px solid {acc};
                border-left: 3px solid {acc};
                border-radius: 12px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{acc};font-size:10px;border:none;")
        dot.setFixedWidth(12)
        info = QVBoxLayout()
        info.setSpacing(2)
        tit = QLabel(titulo)
        tit.setStyleSheet(label_style(12, "tp", "600"))
        msg = QLabel(mensaje)
        msg.setStyleSheet(label_style(11, "ts"))
        info.addWidget(tit)
        info.addWidget(msg)
        btn_x = QPushButton("✕")
        btn_x.setFixedSize(18, 18)
        btn_x.setStyleSheet(f"background:transparent;color:{t('tm')};border:none;font-size:10px;")
        btn_x.clicked.connect(self.cerrar)
        lay.addWidget(dot)
        lay.addLayout(info)
        lay.addStretch()
        lay.addWidget(btn_x)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.cerrar)
        self._timer.start(4000)

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(350)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)

    def cerrar(self):
        self._timer.stop()
        anim_out = QPropertyAnimation(self, b"pos")
        anim_out.setDuration(200)
        anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        anim_out.setStartValue(self.pos())
        anim_out.setEndValue(QPoint(self.pos().x(), self.pos().y() - 30))
        anim_out.start()
        QTimer.singleShot(200, lambda: self.parent().remover_notif(self) if self.parent() else None)


class AreaNotificaciones(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.notifs = []
        self.setFixedWidth(310)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def agregar(self, tipo, titulo, mensaje):
        n = Notificacion(tipo, titulo, mensaje, self)
        self.notifs.append(n)
        n.show()
        self._reposicionar(animado=True)

    def remover_notif(self, n):
        if n in self.notifs:
            self.notifs.remove(n)
            n.hide()
            n.deleteLater()
            self._reposicionar()

    def _reposicionar(self, animado=False):
        y = 0
        for n in self.notifs:
            n.resize(300, n.sizeHint().height() + 10)
            if animado:
                n.anim.setStartValue(QPoint(0, y - 20))
                n.anim.setEndValue(QPoint(0, y))
                n.anim.start()
            else:
                n.move(0, y)
            y += n.height() + 6
        self.resize(310, max(y, 10))


# ─────────────────────────────────────────────
#  TITLEBAR macOS
# ─────────────────────────────────────────────


class TitleBar(QFrame):
    def __init__(self, parent, titulo="AsmoRoot v7"):
        super().__init__(parent)
        self.parent_win = parent
        self.setFixedHeight(44)
        self.setStyleSheet(f"background:{t('bar')};border-bottom:1px solid {t('brd')};")
        self._drag_pos = None
        self._snap_triggered = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(8)

        self.btn_tema = QPushButton("☀️")
        self.btn_tema.setFixedSize(28, 28)
        self.btn_tema.setStyleSheet(
            f"QPushButton{{background:{t('card')};border:1px solid {t('brd')};border-radius:7px;font-size:13px;}}"
            f"QPushButton:hover{{background:{t('cardh')};}}")
        self.btn_tema.clicked.connect(parent.toggle_tema)
        self.btn_tema.setToolTip("Cambiar tema")
        lay.addWidget(self.btn_tema)

        lay.addStretch()
        #Titulo icono
        ttl = QLabel(f"  {titulo}")
        ttl.setStyleSheet(label_style(12, "ts", "500"))
        lay.addWidget(ttl)

        lay.addStretch()

        # Dots macOS (derecha) — orden: verde, amarillo, rojo

        dots_w = QWidget()
        dots_lay = QHBoxLayout(dots_w)
        dots_lay.setContentsMargins(0, 0, 0, 0)
        dots_lay.setSpacing(7)

        dot_data = [
            ("#28c840", parent._toggle_maximized, "Pantalla completa"),
            ("#febc2e", parent.showMinimized,      "Minimizar"),
            ("#ff5f57", parent.close,              "Cerrar"),
        ]
        for color, fn, tip in dot_data:
            d = QPushButton()
            d.setFixedSize(13, 13)
            d.setStyleSheet(f"""
                QPushButton {{
                    background:{color};
                    border-radius:6px;
                    border:none;
                }}
                QPushButton:hover {{
                    border: 1.5px solid rgba(255,255,255,60);
                }}
            """)
            d.setToolTip(tip)
            d.clicked.connect(fn)
            dots_lay.addWidget(d)

        lay.addWidget(dots_w)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.parent_win.frameGeometry().topLeft()
            self._snap_triggered = False

    def mouseMoveEvent(self, e):
        from PyQt6.QtWidgets import QApplication
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            new_pos = e.globalPosition().toPoint() - self._drag_pos
            screen = QApplication.primaryScreen().availableGeometry()
            gx = e.globalPosition().toPoint().x()
            gy = e.globalPosition().toPoint().y()

            if gy <= 5 and not self._snap_triggered:
                self._snap_triggered = True
                self.parent_win.showMaximized()
                return
            elif gx <= 5 and not self._snap_triggered:
                self._snap_triggered = True
                self.parent_win.setGeometry(0, 0, screen.width() // 2, screen.height())
                return
            elif gx >= screen.width() - 5 and not self._snap_triggered:
                self._snap_triggered = True
                self.parent_win.setGeometry(screen.width() // 2, 0, screen.width() // 2, screen.height())
                return

            if not self._snap_triggered:
                self.parent_win.move(new_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        self._snap_triggered = False
