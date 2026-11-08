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


def load_macro(name):
    with open(macro_path(name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def delete_macro(name):
    path = macro_path(name)
    if os.path.exists(path):
        os.remove(path)
