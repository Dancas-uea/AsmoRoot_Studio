from PyQt6.QtWidgets import QPushButton

# ─────────────────────────────────────────────
#  HELPERS DE ESTILO
#  Importar: from styles.helpers import t, btn_style, input_style, label_style, mac_tooltip
# ─────────────────────────────────────────────


def t(key):
    """Devuelve el color del tema activo por clave."""
    from ui.main_window import AsmoRootApp
    return AsmoRootApp.CURRENT_THEME.get(key, "#ffffff")


def btn_style(bg="#378ADD", color="white", radius=8, padding="10px 18px"):
    return f"""
        QPushButton {{
            background: {bg};
            color: {color};
            border: none;
            border-radius: {radius}px;
            padding: {padding};
            font-weight: 600;
            font-size: 12px;
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}
        QPushButton:hover {{
            background: {bg};
            border: 1px solid rgba(255,255,255,50);
        }}
        QPushButton:pressed {{ opacity: 0.8; }}
        QPushButton:disabled {{ opacity: 0.35; }}
    """


def input_style():
    return f"""
        QLineEdit, QComboBox {{
            background: {t('inp')};
            color: {t('tp')};
            border: 1px solid {t('brd')};
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {t('acc')};
            background: rgba(55,138,221,15);
        }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox::down-arrow {{ image: none; width: 0; }}
    """


def label_style(size=11, color_key="ts", weight="normal"):
    return (
        f"color: {t(color_key)}; font-size: {size}px; font-weight: {weight}; "
        f"font-family: 'SF Pro Display', 'Segoe UI', sans-serif; "
        f"border: none; text-decoration: none;"
    )


def mac_tooltip(widget, texto):
    """Aplica tooltip estilo macOS a cualquier widget."""
    widget.setToolTip(texto)
    widget.setStyleSheet(widget.styleSheet() + """
        QToolTip {
            background: rgba(30,30,46,240);
            color: rgba(255,255,255,200);
            border: 1px solid rgba(255,255,255,30);
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 11px;
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }
    """)
