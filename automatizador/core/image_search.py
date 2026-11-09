"""Captura de pantalla y busqueda de imagenes/texto en pantalla.

Usa 'pyautogui' (y Pillow) para tomar capturas y 'pyautogui.locateOnScreen'
para buscar una imagen de referencia en la pantalla. El parametro de
confianza ("confidence") solo funciona si ademas esta instalado
'opencv-python'; si no lo esta, se hace una busqueda exacta de pixeles.

Tambien incluye busqueda de texto en pantalla por OCR usando 'pytesseract',
que a su vez necesita el motor Tesseract OCR instalado en el sistema
(https://github.com/tesseract-ocr/tesseract).
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


def _import_pytesseract():
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "Esta funcion necesita la libreria 'pytesseract'.\n"
            "Instalala con:\n"
            "py -3 -m pip install -r requirements.txt\n"
            "Ademas necesitas tener instalado el motor Tesseract OCR:\n"
            "https://github.com/tesseract-ocr/tesseract"
        ) from exc
    return pytesseract


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


def locate_image_box(path, region=None, confidence=0.8):
    """Busca la imagen 'path' en pantalla (o en 'region').

    Devuelve (left, top, width, height) en coordenadas absolutas de
    pantalla con el area de la coincidencia, o None si no se encontro.
    Intenta primero con el nivel de 'confidence' indicado (requiere
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
    return (int(box.left), int(box.top), int(box.width), int(box.height))


def locate_image(path, region=None, confidence=0.8):
    """Busca la imagen 'path' en pantalla (o en 'region').

    Devuelve (x, y) con el centro de la coincidencia, o None si no se
    encontro."""
    box = locate_image_box(path, region=region, confidence=confidence)
    if box is None:
        return None
    left, top, width, height = box
    return (left + width // 2, top + height // 2)


def locate_text_box(text, region=None, lang="eng", case_sensitive=False):
    """Busca 'text' en la pantalla (o en 'region') usando OCR.

    Soporta busquedas de varias palabras (compara secuencias consecutivas
    de palabras detectadas). Devuelve (left, top, width, height) en
    coordenadas absolutas de pantalla con el area del texto encontrado, o
    None si no se encontro."""
    needle = (text or "").strip()
    if not needle:
        return None

    pytesseract = _import_pytesseract()
    normalized = _normalize_region(region)
    origin_x, origin_y = (normalized[0], normalized[1]) if normalized else (0, 0)

    image = grab_region(region)
    data = pytesseract.image_to_data(
        image, lang=lang or "eng", output_type=pytesseract.Output.DICT
    )

    words = needle.split()
    needle_cmp = words if case_sensitive else [w.lower() for w in words]
    count = len(needle_cmp)

    raw_words = data.get("text", [])
    total = len(raw_words)
    for start in range(total - count + 1):
        chunk = raw_words[start : start + count]
        if any(not w.strip() for w in chunk):
            continue
        chunk_cmp = chunk if case_sensitive else [w.lower() for w in chunk]
        if chunk_cmp != needle_cmp:
            continue
        lefts = data["left"][start : start + count]
        tops = data["top"][start : start + count]
        rights = [
            data["left"][i] + data["width"][i] for i in range(start, start + count)
        ]
        bottoms = [
            data["top"][i] + data["height"][i] for i in range(start, start + count)
        ]
        x0, y0 = min(lefts), min(tops)
        x1, y1 = max(rights), max(bottoms)
        return (origin_x + x0, origin_y + y0, x1 - x0, y1 - y0)
    return None


def locate_text(text, region=None, lang="eng", case_sensitive=False):
    """Busca 'text' en la pantalla (o en 'region') usando OCR.

    Devuelve (x, y) con el centro del texto encontrado (coordenadas
    absolutas de pantalla), o None si no se encontro."""
    box = locate_text_box(text, region=region, lang=lang, case_sensitive=case_sensitive)
    if box is None:
        return None
    left, top, width, height = box
    return (left + width // 2, top + height // 2)

