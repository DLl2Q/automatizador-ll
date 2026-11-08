"""Utilidades compartidas para serializar y mostrar teclas de pynput."""

from pynput import keyboard

# Nombres de teclas especiales disponibles para elegir manualmente en el
# panel de acciones (ordenados para mostrarlos en un combobox).
SPECIAL_KEY_NAMES = sorted(name for name in dir(keyboard.Key) if not name.startswith("_"))


def key_to_str(key):
    """Serializa una tecla de pynput a texto para poder guardarla en JSON."""
    if isinstance(key, keyboard.KeyCode):
        if key.char is not None:
            return f"char:{key.char}"
        return f"vk:{key.vk}"
    return f"special:{key.name}"


def str_to_key(value):
    """Reconstruye una tecla de pynput a partir del texto generado por key_to_str."""
    if value.startswith("char:"):
        return keyboard.KeyCode.from_char(value[5:])
    if value.startswith("vk:"):
        return keyboard.KeyCode.from_vk(int(value[3:]))
    if value.startswith("special:"):
        return getattr(keyboard.Key, value[8:])
    raise ValueError(f"Tecla desconocida: {value!r}")


def key_to_display(key):
    """Convierte una tecla de pynput en el texto corto que se usa en la UI
    (un caracter suelto, o el nombre de una tecla especial)."""
    if isinstance(key, keyboard.KeyCode):
        if key.char is not None:
            return key.char
        return f"vk:{key.vk}"
    return key.name


def display_to_key_str(value):
    """Convierte el texto corto mostrado en la UI al formato de key_to_str."""
    if value is None:
        raise ValueError("Debes indicar una tecla.")
    value = value.strip()
    if not value:
        raise ValueError("Debes indicar una tecla.")
    if value.startswith("vk:"):
        return value
    if len(value) == 1:
        return f"char:{value}"
    if hasattr(keyboard.Key, value):
        return f"special:{value}"
    raise ValueError(f"Tecla desconocida: {value!r}")


def key_str_to_display(value):
    """Convierte un valor guardado (formato key_to_str) al texto corto de la UI."""
    try:
        return key_to_display(str_to_key(value))
    except (ValueError, AttributeError):
        return value
