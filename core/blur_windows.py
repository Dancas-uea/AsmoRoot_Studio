import ctypes
import ctypes.wintypes

# ─────────────────────────────────────────────
#  BLUR REAL DE WINDOWS (Mica / Acrylic API)
# ─────────────────────────────────────────────


def aplicar_blur_windows(hwnd):
    """Aplica el efecto Acrylic blur real de Windows 10/11 a la ventana."""
    try:
        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [
                ("AccentState",   ctypes.c_int),
                ("AccentFlags",   ctypes.c_int),
                ("GradientColor", ctypes.c_int),
                ("AnimationId",   ctypes.c_int),
            ]

        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute",  ctypes.c_int),
                ("Data",       ctypes.POINTER(ctypes.c_int)),
                ("SizeOfData", ctypes.c_size_t),
            ]

        # ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
        accent = ACCENT_POLICY()
        accent.AccentState   = 4
        accent.AccentFlags   = 2
        accent.GradientColor = 0x99000000  # negro semitransparente

        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute  = 19  # WCA_ACCENT_POLICY
        data.Data       = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(ctypes.c_int))
        data.SizeOfData = ctypes.sizeof(accent)

        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
    except Exception as e:
        print(f"Blur no disponible: {e}")


def aplicar_mica(hwnd):
    """Intenta Mica (Windows 11 22H2+) como fallback premium."""
    try:
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        DWMSBT_MAINWINDOW = 2  # Mica
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(ctypes.c_int(DWMSBT_MAINWINDOW)),
            ctypes.sizeof(ctypes.c_int)
        )
    except Exception as e:
        print(f"Mica no disponible: {e}")
