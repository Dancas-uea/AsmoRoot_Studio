# core/paths.py
import sys
import os
import json

if getattr(sys, 'frozen', False):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_ASMO_CFG_PATH = os.path.join(os.path.expanduser("~"), "AsmoRoot_config.json")

if os.path.exists(_ASMO_CFG_PATH):
    with open(_ASMO_CFG_PATH, 'r', encoding='utf-8') as _f:
        _asmo_cfg = json.load(_f)
    PATH_RAIZ = _asmo_cfg.get("path_raiz", os.path.join(os.path.expanduser("~"), "AsmoRoot"))
else:
    PATH_RAIZ = os.path.join(os.path.expanduser("~"), "AsmoRoot")

# Carpeta de iconos
ICONS_DIR = os.path.join(_BASE_DIR, "assets", "icons")
PATH_LOGO = os.path.join(ICONS_DIR, "logosga.png")
PATH_ICO = os.path.join(ICONS_DIR, "logosga.ico")
PATH_PNG = PATH_LOGO
ARCHIVO_CONFIG = _ASMO_CFG_PATH