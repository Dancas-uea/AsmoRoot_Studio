# core/utils.py
import os
from PIL import Image

def generar_icono_profesional(path_logo, path_ico):
    try:
        if os.path.exists(path_logo):
            img = Image.open(path_logo)
            img.save(path_ico, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    except Exception as e:
        print(f"Icono error: {e}")