import os
from PIL import Image

# ─────────────────────────────────────────────
#  RUTAS DEL PROYECTO
# ─────────────────────────────────────────────
PATH_RAIZ      = r"C:\Users\AsmoRoot\Desktop\Universidad Estatal Amazonica"
PATH_LOGO      = os.path.join(PATH_RAIZ, "Logo", "logo.png")
PATH_ICO       = os.path.join(PATH_RAIZ, "Logo", "logo.ico")
ARCHIVO_CONFIG = os.path.join(PATH_RAIZ, "config_carrera.json")


# ─────────────────────────────────────────────
#  PALETA macOS dark / light
# ─────────────────────────────────────────────
THEME = {
    "dark": {
        "bg":        "#08081a",
        "win":       "rgba(13,13,28,200)",
        "sb":        "#0b0b18",
        "bar":       "#10101e",
        "card":      "rgba(255,255,255,10)",
        "cardh":     "rgba(255,255,255,22)",
        "inp":       "rgba(255,255,255,13)",
        "brd":       "rgba(255,255,255,23)",
        "acc":       "#378ADD",
        "accd":      "rgba(55,138,221,40)",
        "acct":      "#85B7EB",
        "tp":        "rgba(255,255,255,230)",
        "ts":        "rgba(255,255,255,115)",
        "tm":        "rgba(255,255,255,56)",
        "grn":       "#28c840",
        "red":       "#ff5f57",
        "yel":       "#febc2e",
        "browserbg": "#0d0d1a",
    },
    "light": {
        "bg":        "#c8d4e8",
        "win":       "rgba(235,240,255,210)",
        "sb":        "#dde4f5",
        "bar":       "#d4daf0",
        "card":      "rgba(255,255,255,120)",
        "cardh":     "rgba(255,255,255,180)",
        "inp":       "rgba(255,255,255,150)",
        "brd":       "rgba(0,0,0,18)",
        "acc":       "#185FA5",
        "accd":      "rgba(24,95,165,30)",
        "acct":      "#185FA5",
        "tp":        "rgba(0,0,0,224)",
        "ts":        "rgba(0,0,0,128)",
        "tm":        "rgba(0,0,0,76)",
        "grn":       "#1a8c30",
        "red":       "#d93025",
        "yel":       "#c8890a",
        "browserbg": "#f5f6fa",
    }
}


# ─────────────────────────────────────────────
#  GENERACIÓN DE ÍCONO
# ─────────────────────────────────────────────
def generar_icono_profesional():
    try:
        if os.path.exists(PATH_LOGO):
            img = Image.open(PATH_LOGO)
            img.save(PATH_ICO, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    except Exception as e:
        print(f"Icono error: {e}")
