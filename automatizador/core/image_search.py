"""Captura de pantalla y busqueda de imagenes en pantalla.

Usa 'pyautogui' (y Pillow) para tomar capturas y 'pyautogui.locateOnScreen'
para buscar una imagen de referencia en la pantalla. El parametro de
confianza ("confidence") solo funciona si ademas esta instalado
'opencv-python'; si no lo esta, se hace una busqueda exacta de pixeles.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "images")


def ensure_images_dir():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    return IMAGES_DIR


def _import_pyautogui():
    try:
        import pyautogui
    except ImportError as exc:
        raise RuntimeError(
            "Esta funcion necesita la libreria 'pyautogui' (incluye Pillow).\n"
            "Instalala con:\n"
            "py -3 -m pip install -r requirements.txt"
        ) from exc
    return pyautogui


def _normalize_region(region):
    """Convierte (x, y, w, h) en una region valida para pyautogui, o None
    si representa 'pantalla completa' (ancho o alto en 0)."""
    if not region:
        return None
    x, y, w, h = region
    if w and w > 0 and h and h > 0:
        return (int(x), int(y), int(w), int(h))
    return None


def grab_region(region=None):
    """Toma una captura de pantalla completa, o de una region (x, y, w, h)."""
    pyautogui = _import_pyautogui()
    normalized = _normalize_region(region)
    if normalized:
        return pyautogui.screenshot(region=normalized)
    return pyautogui.screenshot()


def save_capture(path, region=None):
    """Captura la pantalla (o 'region') y la guarda como archivo de imagen."""
    if not path:
        raise ValueError("Indica donde guardar la captura.")
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    image = grab_region(region)
    image.save(path)
    return path


def _try_locate(pyautogui, path, **kwargs):
    try:
        return pyautogui.locateOnScreen(path, **kwargs)
    except Exception:  # noqa: BLE001 - imagen no encontrada o sin opencv
        return None


def locate_image(path, region=None, confidence=0.8):
    """Busca la imagen 'path' en pantalla (o en 'region').

    Devuelve (x, y) con el centro de la coincidencia, o None si no se
    encontro. Intenta primero con el nivel de 'confidence' indicado (requiere
    opencv-python); si no esta disponible, reintenta con una busqueda exacta.
    """
    if not path or not os.path.isfile(path):
        return None
    pyautogui = _import_pyautogui()
    kwargs = {}
    normalized = _normalize_region(region)
    if normalized:
        kwargs["region"] = normalized

    box = None
    if confidence is not None:
        box = _try_locate(pyautogui, path, confidence=confidence, **kwargs)
    if box is None:
        box = _try_locate(pyautogui, path, **kwargs)
    if box is None:
        return None
    center = pyautogui.center(box)
    return (center.x, center.y)
