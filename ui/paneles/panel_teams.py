"""
Panel Teams - Gestión de clases virtuales de Microsoft Teams
"""

import os
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from styles.helpers import t, label_style


class PanelTeams(QScrollArea):
    """
    Panel Teams - Muestra el horario de clases y accesos rápidos a Teams
    """

    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.setWidgetResizable(True)
        self.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QLabel { text-decoration: none; border: none; }
            QFrame { text-decoration: none; }
        """)

        self._cargar_clases()
        self._construir_panel()

    def _cargar_clases(self):
        """Carga las clases desde el archivo de configuración."""
        _cfg_path = os.path.join(os.path.expanduser("~"), "AsmoRoot_config.json")
        if os.path.exists(_cfg_path):
            with open(_cfg_path, 'r', encoding='utf-8') as _f:
                _cfg = json.load(_f)
            self.CLASES = _cfg.get("clases_teams", [])
        else:
            self.CLASES = []

    def _construir_panel(self):
        """Construye la interfaz del panel Teams."""
        if not self.CLASES:
            self._construir_panel_vacio()
            return

        inner = QWidget()
        inner.setStyleSheet("""
            QWidget { background: transparent; text-decoration: none; }
            QLabel { text-decoration: none; border: none; }
        """)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(18)

        # Header
        self._crear_header(lay)

        # Accesos rápidos
        self._crear_accesos_rapidos(lay)

        # Próxima clase
        self._crear_proxima_clase(lay)

        # Horario completo
        self._crear_horario_completo(lay)

        lay.addStretch()
        self.setWidget(inner)

    def _construir_panel_vacio(self):
        """Construye el panel cuando no hay clases configuradas."""
        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(inner)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(16)

        ic = QLabel("💜")
        ic.setStyleSheet("font-size:52px;border:none;background:transparent;")
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl1 = QLabel("No tienes clases configuradas")
        lbl1.setStyleSheet(
            "color:rgba(255,255,255,115);font-size:16px;font-weight:600;border:none;background:transparent;")
        lbl1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl2 = QLabel("Ve a ⚙️ Config → Horario Teams e importa tu Excel")
        lbl2.setStyleSheet("color:rgba(255,255,255,56);font-size:12px;border:none;background:transparent;")
        lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(ic)
        lay.addWidget(lbl1)
        lay.addWidget(lbl2)

        self.setWidget(inner)

    def _crear_header(self, parent_layout):
        """Crea el header del panel Teams."""
        hdr = QHBoxLayout()

        logo_teams = QLabel("💜")
        logo_teams.setFixedSize(48, 48)
        logo_teams.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_teams.setStyleSheet(f"""
            background: rgba(124,58,237,0.18);
            border: 1px solid rgba(124,58,237,0.35);
            border-radius: 12px;
            font-size: 22px;
        """)

        info = QVBoxLayout()
        info.setSpacing(2)
        lbl_titulo = QLabel("Microsoft Teams")
        lbl_titulo.setStyleSheet(label_style(18, "tp", "700"))
        lbl_sub = QLabel("Universidad Estatal Amazónica · Clases virtuales")
        lbl_sub.setStyleSheet(label_style(11, "tm"))
        info.addWidget(lbl_titulo)
        info.addWidget(lbl_sub)

        btn_abrir_teams = QPushButton("▶  Abrir Teams")
        btn_abrir_teams.setFixedHeight(36)
        btn_abrir_teams.setStyleSheet(f"""
            QPushButton {{
                background: rgba(124,58,237,0.22);
                color: #a78bfa;
                border: 1px solid rgba(124,58,237,0.40);
                border-radius: 9px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 600;
                font-family: Inter, -apple-system, sans-serif;
            }}
            QPushButton:hover {{ background: rgba(124,58,237,0.35); }}
        """)
        btn_abrir_teams.clicked.connect(lambda: self._abrir_link("msteams:"))

        btn_importar_excel = QPushButton("📥  Importar horario Excel")
        btn_importar_excel.setFixedHeight(36)
        btn_importar_excel.setStyleSheet("""
            QPushButton {
                background: rgba(40,200,64,0.20);
                color: #28c840;
                border: 1px solid rgba(40,200,64,0.40);
                border-radius: 9px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 600;
                font-family: Inter, -apple-system, sans-serif;
            }
            QPushButton:hover { background: rgba(40,200,64,0.35); }
        """)
        btn_importar_excel.clicked.connect(self._importar_excel_teams)

        hdr.addWidget(logo_teams)
        hdr.addSpacing(12)
        hdr.addLayout(info)
        hdr.addStretch()
        hdr.addWidget(btn_importar_excel)
        hdr.addSpacing(8)
        hdr.addWidget(btn_abrir_teams)
        parent_layout.addLayout(hdr)

    def _crear_accesos_rapidos(self, parent_layout):
        """Crea los accesos rápidos a Teams."""
        lbl_rapidos = QLabel("ACCESOS RÁPIDOS")
        lbl_rapidos.setStyleSheet(label_style(9, "tm") + "letter-spacing:1.2px;")
        parent_layout.addWidget(lbl_rapidos)

        rapidos_row = QHBoxLayout()
        rapidos_row.setSpacing(10)

        accesos = [
            ("📅", "Calendario", "msteams://teams.microsoft.com/l/calendar"),
            ("🔔", "Notificaciones", "msteams://teams.microsoft.com/l/activity"),
            ("💬", "Chat", "msteams://teams.microsoft.com/l/chat"),
            ("📋", "Tareas", "msteams://teams.microsoft.com/l/entity/com.microsoft.teamspace.tab.planner"),
        ]

        for icono, nombre, url in accesos:
            btn = QFrame()
            btn.setFixedHeight(80)
            btn.setStyleSheet(f"""
                QFrame {{
                    background: {t('card')};
                    border: 1px solid {t('brd')};
                    border-radius: 12px;
                }}
                QFrame:hover {{
                    background: {t('cardh')};
                    border-color: rgba(124,58,237,0.40);
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_lay = QVBoxLayout(btn)
            btn_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn_lay.setSpacing(5)

            ic = QLabel(icono)
            ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ic.setStyleSheet("font-size:22px;border:none;background:transparent;")

            nm = QLabel(nombre)
            nm.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nm.setStyleSheet(label_style(11, "ts", "500") + "text-decoration:none;background:transparent;")

            btn_lay.addWidget(ic)
            btn_lay.addWidget(nm)

            btn.mousePressEvent = lambda e, u=url: self._abrir_link(u)
            rapidos_row.addWidget(btn)

        parent_layout.addLayout(rapidos_row)

    def _crear_proxima_clase(self, parent_layout):
        """Crea la tarjeta de la próxima clase."""
        lbl_proxima = QLabel("PRÓXIMA CLASE")
        lbl_proxima.setStyleSheet(label_style(9, "tm") + "letter-spacing:1.2px;")
        parent_layout.addWidget(lbl_proxima)

        ahora = datetime.now()
        proxima = None
        dias_hasta_sabado = (5 - ahora.weekday()) % 7

        for clase in self.CLASES:
            hora, minuto = map(int, clase["hora_ini"].split(":"))
            fecha_clase = ahora.replace(
                hour=hora, minute=minuto, second=0, microsecond=0
            ) + timedelta(days=dias_hasta_sabado)

            if ahora.weekday() == 5 and fecha_clase < ahora:
                fecha_clase += timedelta(days=7)

            if proxima is None or fecha_clase < proxima[1]:
                proxima = (clase, fecha_clase)

        if proxima:
            clase_prox, fecha_prox = proxima
            card_prox = QFrame()
            card_prox.setStyleSheet(f"""
                QFrame {{
                    background: rgba(124,58,237,0.10);
                    border: 1px solid rgba(124,58,237,0.28);
                    border-left: 3px solid {clase_prox['color']};
                    border-radius: 12px;
                }}
            """)
            cp_lay = QHBoxLayout(card_prox)
            cp_lay.setContentsMargins(16, 14, 16, 14)
            cp_lay.setSpacing(12)

            ic_prox = QLabel(clase_prox["icono"])
            ic_prox.setStyleSheet("font-size:24px;border:none;background:transparent;")
            ic_prox.setFixedWidth(32)

            info_prox = QVBoxLayout()
            info_prox.setSpacing(3)
            lbl_mat = QLabel(clase_prox["materia"])
            lbl_mat.setStyleSheet(label_style(13, "tp", "600") + "text-decoration:none;background:transparent;")

            es_hoy = fecha_prox.date() == ahora.date()
            dias_es = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
                       "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}
            dia_en = fecha_prox.strftime("%A")
            dia_txt = "Hoy" if es_hoy else f"{dias_es[dia_en]} {fecha_prox.strftime('%d/%m')}"
            lbl_hora = QLabel(f"{dia_txt}  ·  {clase_prox['hora_ini']} — {clase_prox['hora_fin']}")
            lbl_hora.setStyleSheet(label_style(10, "tm") + "text-decoration:none;background:transparent;")

            info_prox.addWidget(lbl_mat)
            info_prox.addWidget(lbl_hora)

            btn_unirse = QPushButton("  Unirse")
            btn_unirse.setFixedHeight(34)
            btn_unirse.setFixedWidth(100)
            btn_unirse.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(124,58,237,0.25);
                    color: #a78bfa;
                    border: 1px solid rgba(124,58,237,0.45);
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 600;
                    font-family: Inter, -apple-system, sans-serif;
                }}
                QPushButton:hover {{ background: rgba(124,58,237,0.40); }}
            """)
            btn_unirse.clicked.connect(lambda _, url=clase_prox["link"]: self._abrir_link(url))

            cp_lay.addWidget(ic_prox)
            cp_lay.addLayout(info_prox)
            cp_lay.addStretch()
            cp_lay.addWidget(btn_unirse)
            parent_layout.addWidget(card_prox)

    def _crear_horario_completo(self, parent_layout):
        """Crea el horario completo de todas las clases."""
        lbl_todas = QLabel("HORARIO COMPLETO — SÁBADOS")
        lbl_todas.setStyleSheet(label_style(9, "tm") + "letter-spacing:1.2px;")
        parent_layout.addWidget(lbl_todas)

        for clase in self.CLASES:
            card = QFrame()
            card.setFixedHeight(62)
            card.setStyleSheet(f"""
                QFrame {{
                    background: {t('card')};
                    border: 1px solid {t('brd')};
                    border-left: 3px solid {clase['color']};
                    border-radius: 10px;
                }}
                QFrame:hover {{ background: {t('cardh')}; }}
            """)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(14, 0, 14, 0)
            cl.setSpacing(12)

            ic = QLabel(clase["icono"])
            ic.setFixedWidth(28)
            ic.setStyleSheet("font-size:18px;border:none;background:transparent;")

            info_cl = QVBoxLayout()
            info_cl.setSpacing(2)
            lbl_n = QLabel(clase["materia"])
            lbl_n.setStyleSheet(label_style(11, "tp", "500") + "text-decoration:none;background:transparent;")
            lbl_h = QLabel(f"{clase['hora_ini']} — {clase['hora_fin']}")
            lbl_h.setStyleSheet(label_style(10, "tm") + "text-decoration:none;background:transparent;")
            info_cl.addWidget(lbl_n)
            info_cl.addWidget(lbl_h)

            btn_join = QPushButton("Unirse →")
            btn_join.setFixedHeight(28)
            btn_join.setFixedWidth(80)
            btn_join.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: #a78bfa;
                    border: 1px solid rgba(124,58,237,0.35);
                    border-radius: 7px;
                    font-size: 11px;
                    font-weight: 600;
                    font-family: Inter, -apple-system, sans-serif;
                }}
                QPushButton:hover {{
                    background: rgba(124,58,237,0.20);
                }}
            """)
            btn_join.clicked.connect(lambda _, url=clase["link"]: self._abrir_link(url))

            cl.addWidget(ic)
            cl.addLayout(info_cl)
            cl.addStretch()
            cl.addWidget(btn_join)
            parent_layout.addWidget(card)

    def _abrir_link(self, url):
        """Abre un link de forma segura."""
        if not url or url.strip() in ("", "None", "nan"):
            if hasattr(self.parent_app, 'notificar'):
                self.parent_app.notificar("or", "Sin link", "Esta clase no tiene link configurado")
            return
        try:
            os.startfile(url)
        except Exception:
            try:
                import webbrowser
                webbrowser.open(url)
            except Exception as e:
                if hasattr(self.parent_app, 'notificar'):
                    self.parent_app.notificar("rd", "Link inválido", str(e)[:60])

    def _importar_excel_teams(self):
        """Importa el horario desde un archivo Excel."""
        MSGBOX_STYLE = f"""
            QMessageBox {{
                background: {t('sb')};
                color: {t('tp')};
                font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
                font-size: 12px;
            }}
            QMessageBox QLabel {{
                color: {t('tp')};
                font-size: 12px;
                background: transparent;
            }}
            QPushButton {{
                background: {t('acc')};
                color: white;
                border: none;
                border-radius: 7px;
                padding: 6px 20px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ border: 1px solid rgba(255,255,255,50); }}
        """

        ruta, _ = QFileDialog.getOpenFileName(
            self, "Selecciona el Excel de Teams", "", "Excel (*.xlsx *.xls)")
        if not ruta:
            return

        try:
            import openpyxl
            wb = openpyxl.load_workbook(ruta, data_only=True)
            ws = wb.active
        except Exception as e:
            mb = QMessageBox(self)
            mb.setWindowTitle("Error")
            mb.setText(f"No se pudo leer el archivo:\n{e}")
            mb.setStyleSheet(MSGBOX_STYLE)
            mb.exec()
            return

        def _hora(val):
            if val is None: return "07:00"
            if hasattr(val, 'hour'): return f"{val.hour:02d}:{val.minute:02d}"
            if hasattr(val, 'strftime'): return val.strftime("%H:%M")
            s = str(val).strip()
            if ":" in s:
                p = s.split(":")
                try:
                    return f"{int(p[0]):02d}:{int(p[1]):02d}"
                except:
                    pass
            try:
                f = float(s)
                total = round(f * 24 * 60)
                return f"{total // 60:02d}:{total % 60:02d}"
            except:
                pass
            return "07:00"

        clases_nuevas = []
        for row in ws.iter_rows(min_row=1, values_only=True):
            if not row[0]: continue
            mat = str(row[0]).strip()
            if mat.lower() in ("materia", "asignatura", "curso", "subject"): continue
            ini = _hora(row[1] if len(row) > 1 else None)
            fin = _hora(row[2] if len(row) > 2 else None)
            link = str(row[3]).strip() if len(row) > 3 and row[3] else ""
            color = str(row[4]).strip() if len(row) > 4 and row[4] else "#378ADD"
            icono = str(row[5]).strip() if len(row) > 5 and row[5] else "📘"
            clases_nuevas.append({
                "materia": mat, "hora_ini": ini, "hora_fin": fin,
                "link": link, "color": color, "icono": icono
            })

        if not clases_nuevas:
            mb = QMessageBox(self)
            mb.setWindowTitle("Aviso")
            mb.setText("No se encontraron clases en el archivo.")
            mb.setStyleSheet(MSGBOX_STYLE)
            mb.exec()
            return

        CONFIG_PATH = os.path.join(os.path.expanduser("~"), "AsmoRoot_config.json")
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            cfg["clases_teams"] = clases_nuevas
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=4, ensure_ascii=False)

        # Recargar el panel
        self.CLASES = clases_nuevas
        self._construir_panel()

        mb = QMessageBox(self)
        mb.setWindowTitle("Importado")
        mb.setText(f"✓ {len(clases_nuevas)} clase(s) importadas correctamente.")
        mb.setStyleSheet(MSGBOX_STYLE)
        mb.exec()

        if hasattr(self.parent_app, 'notificar'):
            self.parent_app.notificar("gn", "Teams actualizado", f"{len(clases_nuevas)} clases importadas")

    def recargar(self):
        """Recarga el panel desde la configuración."""
        self._cargar_clases()
        self._construir_panel()