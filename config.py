import os
from PIL import Image

# ─────────────────────────────────────────────
#  RUTAS DEL PROYECTO
# ─────────────────────────────────────────────
PATH_RAIZ      = r"C:\Users\AsmoRoot\Desktop\Universidad Estatal Amazonica"
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
    }
}
