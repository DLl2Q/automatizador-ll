"""Catalogo de tipos de accion disponibles en el panel de acciones.

Cada accion de una macro es un diccionario con, al menos:
    - "type": uno de las claves de ACTION_TYPES.
    - "delay": segundos de espera ANTES de ejecutar la accion (float >= 0).
    - el resto de campos propios de ese tipo (ver "fields" de cada tipo).

Esto permite construir una macro a mano desde la interfaz, igual que en el
programa original: eligiendo una accion de una lista (mover mouse, clic,
arrastrar, rueda, tecla abajo/arriba, presionar tecla, escribir texto,
pausa, ejecutar programa, abrir URL, mostrar mensaje) y completando sus
parametros, sin necesidad de grabarla.
"""

from . import keys

# Tipos de campo soportados por el dialogo de edicion (core/action_dialog.py):
#   "int"      -> numero entero
#   "float"    -> numero decimal
#   "text"     -> texto de una linea
#   "textarea" -> texto de varias lineas
#   "choice"   -> lista desplegable (choices)
#   "bool"     -> casilla de verificacion
#   "key"      -> selector/captura de tecla
#   "path"     -> ruta de archivo (con boton "Elegir...")

ACTION_TYPES = {
    "move": {
        "label": "Mover mouse",
        "fields": [
            ("x", "Posicion X", "int", 0, None),
            ("y", "Posicion Y", "int", 0, None),
        ],
    },
    "click": {
        "label": "Clic de mouse",
        "fields": [
            ("x", "Posicion X", "int", 0, None),
            ("y", "Posicion Y", "int", 0, None),
            ("button", "Boton", "choice", "left", ["left", "right", "middle"]),
            ("action", "Accion", "choice", "click", ["click", "down", "up"]),
            ("double", "Doble clic", "bool", False, None),
        ],
    },
    "mouse_drag": {
        "label": "Arrastrar mouse",
        "fields": [
            ("x1", "Desde X", "int", 0, None),
            ("y1", "Desde Y", "int", 0, None),
            ("x2", "Hasta X", "int", 0, None),
            ("y2", "Hasta Y", "int", 0, None),
            ("button", "Boton", "choice", "left", ["left", "right", "middle"]),
            ("duration", "Duracion del arrastre (s)", "float", 0.3, None),
        ],
    },
    "scroll": {
        "label": "Rueda del mouse",
        "fields": [
            ("x", "Posicion X", "int", 0, None),
            ("y", "Posicion Y", "int", 0, None),
            ("dx", "Desplazamiento horizontal", "int", 0, None),
            ("dy", "Desplazamiento vertical", "int", 1, None),
        ],
    },
    "capture_image": {
        "label": "Capturar imagen de pantalla",
        "fields": [
            ("save_path", "Guardar captura en", "save_path", "", None),
            ("x", "Region X (0 = pantalla completa)", "int", 0, None),
            ("y", "Region Y", "int", 0, None),
            ("width", "Ancho de la region (0 = pantalla completa)", "int", 0, None),
            ("height", "Alto de la region", "int", 0, None),
        ],
    },
    "find_image": {
        "label": "Buscar imagen en pantalla",
        "fields": [
            ("image_path", "Imagen de referencia", "image_path", "", None),
            ("confidence", "Confianza (0.1 a 1.0)", "float", 0.8, None),
            ("x", "Region X (0 = pantalla completa)", "int", 0, None),
            ("y", "Region Y", "int", 0, None),
            ("width", "Ancho de la region (0 = pantalla completa)", "int", 0, None),
            ("height", "Alto de la region", "int", 0, None),
            (
                "found_action",
                "Si se encuentra: accion de mouse",
                "choice",
                "click",
                ["click", "double_click", "right_click", "move", "none"],
            ),
            ("offset_x", "Desplazamiento X desde el centro encontrado", "int", 0, None),
            ("offset_y", "Desplazamiento Y desde el centro encontrado", "int", 0, None),
            ("not_found_wait", "Si no se encuentra: esperar (s)", "float", 1.0, None),
            (
                "not_found_goto",
                "Si no se encuentra: ir al paso # (0 = continuar)",
                "int",
                0,
                None,
            ),
        ],
    },
    "find_ocr": {
        "label": "Buscar texto en pantalla (OCR)",
        "fields": [
            ("text", "Texto a buscar", "text", "", None),
            ("case_sensitive", "Distinguir mayusculas/minusculas", "bool", False, None),
            ("lang", "Idioma del OCR (codigo Tesseract)", "text", "eng", None),
            ("x", "Region X (0 = pantalla completa)", "int", 0, None),
            ("y", "Region Y", "int", 0, None),
            ("width", "Ancho de la region (0 = pantalla completa)", "int", 0, None),
            ("height", "Alto de la region", "int", 0, None),
            (
                "found_action",
                "Si se encuentra: accion de mouse",
                "choice",
                "click",
                ["click", "double_click", "right_click", "move", "none"],
            ),
            ("offset_x", "Desplazamiento X desde el centro encontrado", "int", 0, None),
            ("offset_y", "Desplazamiento Y desde el centro encontrado", "int", 0, None),
            ("not_found_wait", "Si no se encuentra: esperar (s)", "float", 1.0, None),
            (
                "not_found_goto",
                "Si no se encuentra: ir al paso # (0 = continuar)",
                "int",
                0,
                None,
            ),
        ],
    },
    "key_down": {
        "label": "Tecla abajo (mantener)",
        "fields": [
            ("key", "Tecla", "key", "", None),
        ],
    },
    "key_up": {
        "label": "Tecla arriba (soltar)",
        "fields": [
            ("key", "Tecla", "key", "", None),
        ],
    },
    "key_press": {
        "label": "Presionar tecla",
        "fields": [
            ("key", "Tecla", "key", "", None),
        ],
    },
    "type_text": {
        "label": "Escribir texto",
        "fields": [
            ("text", "Texto a escribir", "textarea", "", None),
            ("interval", "Intervalo entre teclas (s)", "float", 0.02, None),
        ],
    },
    "wait": {
        "label": "Esperar / pausa",
        "fields": [],
    },
    "run_program": {
        "label": "Ejecutar programa",
        "fields": [
            ("path", "Programa o archivo", "path", "", None),
            ("args", "Argumentos (opcional)", "text", "", None),
        ],
    },
    "open_url": {
        "label": "Abrir pagina web",
        "fields": [
            ("url", "URL", "text", "https://", None),
        ],
    },
    "message": {
        "label": "Mostrar mensaje",
        "fields": [
            ("title", "Titulo", "text", "Automatizador", None),
            ("text", "Mensaje", "textarea", "", None),
        ],
    },
}

# Orden en el que se muestran los tipos en el selector "Agregar accion".
ACTION_ORDER = [
    "move",
    "click",
    "mouse_drag",
    "scroll",
    "capture_image",
    "find_image",
    "find_ocr",
    "key_press",
    "key_down",
    "key_up",
    "type_text",
    "wait",
    "run_program",
    "open_url",
    "message",
]


def label_for(action_type):
    return ACTION_TYPES.get(action_type, {}).get("label", action_type)


def fields_for(action_type):
    return ACTION_TYPES.get(action_type, {}).get("fields", [])


def default_event(action_type):
    """Crea un evento con los valores por defecto de ese tipo de accion."""
    event = {"type": action_type, "delay": 0.0}
    for name, _label, _kind, default, _choices in fields_for(action_type):
        event[name] = default
    if action_type == "wait":
        event["delay"] = 1.0
    return event


def _key_display(event):
    return keys.key_str_to_display(event.get("key", ""))


def describe(event):
    """Genera una descripcion corta y legible de un evento para la lista."""
    kind = event.get("type")
    if kind == "move":
        return f"Mover a ({event.get('x', 0)}, {event.get('y', 0)})"
    if kind == "click":
        accion = {"click": "Clic", "down": "Presionar", "up": "Soltar"}.get(
            event.get("action", "click"), "Clic"
        )
        boton = {"left": "izquierdo", "right": "derecho", "middle": "central"}.get(
            event.get("button", "left"), event.get("button", "left")
        )
        extra = " (doble)" if event.get("double") else ""
        return f"{accion} {boton}{extra} en ({event.get('x', 0)}, {event.get('y', 0)})"
    if kind == "mouse_drag":
        boton = {"left": "izquierdo", "right": "derecho", "middle": "central"}.get(
            event.get("button", "left"), event.get("button", "left")
        )
        return (
            f"Arrastrar ({event.get('x1', 0)}, {event.get('y1', 0)}) -> "
            f"({event.get('x2', 0)}, {event.get('y2', 0)}) con boton {boton}"
        )
    if kind == "scroll":
        return (
            f"Rueda en ({event.get('x', 0)}, {event.get('y', 0)}) "
            f"dx={event.get('dx', 0)} dy={event.get('dy', 0)}"
        )
    if kind in ("key_down", "key_up", "key_press"):
        return f"Tecla '{_key_display(event)}'"
    if kind == "type_text":
        text = event.get("text", "")
        preview = text if len(text) <= 40 else text[:37] + "..."
        return f"Escribir: {preview!r}"
    if kind == "wait":
        return f"Pausa de {event.get('delay', 0)} s"
    if kind == "capture_image":
        width, height = event.get("width", 0), event.get("height", 0)
        region = f"region ({event.get('x', 0)}, {event.get('y', 0)}) {width}x{height}"
        zona = region if width and height else "pantalla completa"
        return f"Capturar {zona} -> {event.get('save_path', '')}"
    if kind == "find_image":
        etiqueta_accion = {
            "click": "clic",
            "double_click": "doble clic",
            "right_click": "clic derecho",
            "move": "mover el mouse",
            "none": "nada",
        }.get(event.get("found_action", "click"), event.get("found_action", "click"))
        goto = event.get("not_found_goto", 0)
        destino = f"ir al paso {goto}" if goto else "continuar"
        return (
            f"Buscar '{event.get('image_path', '')}' (conf={event.get('confidence', 0.8)}): "
            f"si se encuentra -> {etiqueta_accion}; "
            f"si no -> esperar {event.get('not_found_wait', 0)}s y {destino}"
        )
    if kind == "find_ocr":
        etiqueta_accion = {
            "click": "clic",
            "double_click": "doble clic",
            "right_click": "clic derecho",
            "move": "mover el mouse",
            "none": "nada",
        }.get(event.get("found_action", "click"), event.get("found_action", "click"))
        goto = event.get("not_found_goto", 0)
        destino = f"ir al paso {goto}" if goto else "continuar"
        return (
            f"Buscar texto (OCR) {event.get('text', '')!r}: "
            f"si se encuentra -> {etiqueta_accion}; "
            f"si no -> esperar {event.get('not_found_wait', 0)}s y {destino}"
        )
    if kind == "run_program":
        args = event.get("args", "")
        return f"Ejecutar: {event.get('path', '')} {args}".strip()
    if kind == "open_url":
        return f"Abrir: {event.get('url', '')}"
    if kind == "message":
        return f"Mensaje: {event.get('title', '')} - {event.get('text', '')}"
    return str(event)
