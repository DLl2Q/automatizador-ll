"""Grabacion de eventos globales de mouse y teclado.

Cada evento grabado guarda un "delay": el tiempo (en segundos) que hay que
esperar antes de ejecutarlo, relativo al evento anterior (o al inicio de la
grabacion para el primero). Este es el mismo formato que usan las acciones
agregadas manualmente desde el panel de acciones, asi que una macro grabada
se puede editar a mano despues sin tener que recalcular nada.
"""

import threading
import time

from pynput import keyboard, mouse

from .keys import key_to_str

# Teclas reservadas como hotkeys de la aplicacion: nunca se graban.
RESERVED_KEYS = {keyboard.Key.f9, keyboard.Key.f10, keyboard.Key.esc}

# Tiempo minimo (segundos) entre dos eventos de movimiento consecutivos.
MOVE_SAMPLE_INTERVAL = 0.02


class Recorder:
    """Graba movimientos, clics, scroll y pulsaciones de teclado con su tiempo relativo."""

    def __init__(self, on_event=None, record_mouse_move=True):
        self.events = []
        self.record_mouse_move = record_mouse_move
        self.on_event = on_event

        self._last_time = None
        self._last_move_time = 0.0
        self._lock = threading.Lock()
        self._recording = False
        self._mouse_listener = None
        self._keyboard_listener = None

    @property
    def is_recording(self):
        return self._recording

    def start(self):
        self.events = []
        self._last_time = time.perf_counter()
        self._last_move_time = -1.0
        self._recording = True

        self._mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop(self):
        if not self._recording:
            return self.events
        self._recording = False
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        return self.events

    def _next_delay(self):
        now = time.perf_counter()
        delay = max(now - self._last_time, 0.0)
        self._last_time = now
        return delay

    def _add(self, event):
        with self._lock:
            event["delay"] = self._next_delay()
            self.events.append(event)
            total = len(self.events)
        if self.on_event:
            self.on_event(total)

    def _on_move(self, x, y):
        if not self.record_mouse_move:
            return
        now = time.perf_counter()
        if now - self._last_move_time < MOVE_SAMPLE_INTERVAL:
            return
        self._last_move_time = now
        self._add({"type": "move", "x": x, "y": y})

    def _on_click(self, x, y, button, pressed):
        self._add(
            {
                "type": "click",
                "x": x,
                "y": y,
                "button": button.name,
                "action": "down" if pressed else "up",
                "double": False,
            }
        )

    def _on_scroll(self, x, y, dx, dy):
        self._add({"type": "scroll", "x": x, "y": y, "dx": dx, "dy": dy})

    def _on_press(self, key):
        if key in RESERVED_KEYS:
            return
        self._add({"type": "key_down", "key": key_to_str(key)})

    def _on_release(self, key):
        if key in RESERVED_KEYS:
            return
        self._add({"type": "key_up", "key": key_to_str(key)})
