"""Guardado y carga de macros en disco, como archivos JSON."""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MACROS_DIR = os.path.join(BASE_DIR, "macros")

_SAFE_NAME = re.compile(r"[^A-Za-z0-9 _\-\.]+")


def ensure_dir():
    os.makedirs(MACROS_DIR, exist_ok=True)


def sanitize_name(name):
    name = name.strip()
    name = _SAFE_NAME.sub("_", name)
    return name or "macro"


def list_macros():
    ensure_dir()
    files = [f[:-5] for f in os.listdir(MACROS_DIR) if f.endswith(".json")]
    return sorted(files, key=str.lower)


def macro_path(name):
    return os.path.join(MACROS_DIR, f"{sanitize_name(name)}.json")


def save_macro(name, events):
    ensure_dir()
    path = macro_path(name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(events, fh, indent=2, ensure_ascii=False)
    return path


def _migrate_legacy_events(events):
    """Convierte macros antiguas (con "time" absoluto y "pressed" booleano)
    al formato actual, basado en "delay" relativo por accion."""
    migrated = []
    last_time = 0.0
    for event in events:
        new_event = dict(event)
        if "time" in new_event:
            new_event["delay"] = max(new_event.pop("time") - last_time, 0.0)
            last_time += new_event["delay"]
        else:
            new_event.setdefault("delay", 0.0)
        if new_event.get("type") == "click" and "pressed" in new_event:
            new_event["action"] = "down" if new_event.pop("pressed") else "up"
            new_event.setdefault("double", False)
        migrated.append(new_event)
    return migrated


def load_macro(name):
    with open(macro_path(name), "r", encoding="utf-8") as fh:
        events = json.load(fh)
    return _migrate_legacy_events(events)


def delete_macro(name):
    path = macro_path(name)
    if os.path.exists(path):
        os.remove(path)
