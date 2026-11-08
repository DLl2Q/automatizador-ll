"""Reproduccion de macros (grabadas o armadas a mano) respetando los tiempos."""

import shlex
import subprocess
import threading
import time
import webbrowser

from pynput import keyboard, mouse

from . import image_search
from .keys import str_to_key


class Player:
    """Reproduce una lista de eventos generada por Recorder o por el panel de acciones."""

    def __init__(self, on_progress=None, on_finished=None, on_message=None):
        self.on_progress = on_progress
        self.on_finished = on_finished
        # on_message(title, text): se invoca para mostrar un cuadro de dialogo;
        # quien registre el callback es responsable de hacerlo en el hilo de UI.
        self.on_message = on_message

        self._mouse = mouse.Controller()
        self._keyboard = keyboard.Controller()
        self._stop_flag = threading.Event()
        self._thread = None

    @property
    def is_playing(self):
        return self._thread is not None and self._thread.is_alive()

    def play(self, events, speed=1.0, repeat=1, start_index=0):
        """Inicia la reproduccion en un hilo aparte.

        speed: multiplicador de velocidad (2.0 = el doble de rapido).
        repeat: numero de repeticiones; 0 o negativo significa infinito.
        start_index: indice (0-based) de la primera accion a ejecutar; permite
            reproducir "desde la accion seleccionada" en vez de desde el inicio.
            Por defecto 0, es decir, el comportamiento de siempre (toda la lista).
        """
        if self.is_playing or not events:
            return
        events = list(events)
        if start_index and 0 < start_index < len(events):
            events = events[start_index:]
        if not events:
            return
        self._stop_flag.clear()
        self._thread = threading.Thread(
            target=self._run, args=(events, speed, repeat), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop_flag.set()

    def _run(self, events, speed, repeat):
        try:
            done = 0
            while not self._stop_flag.is_set() and (repeat <= 0 or done < repeat):
                self._play_once(events, speed)
                done += 1
        finally:
            if self.on_finished:
                self.on_finished()

    def _play_once(self, events, speed):
        speed = max(speed, 0.01)
        total = len(events)
        index = 0
        while index < total:
            if self._stop_flag.is_set():
                return
            event = events[index]
            delay = max(event.get("delay", 0.0), 0.0) / speed
            if not self._sleep(delay):
                return
            jump_to = self._apply(event, speed)
            if self.on_progress:
                self.on_progress(index + 1, total)
            if self._stop_flag.is_set():
                return
            if jump_to is not None and jump_to > 0:
                index = max(0, min(jump_to - 1, total - 1))
            else:
                index += 1

    def _sleep(self, seconds):
        """Duerme 'seconds', revisando la bandera de parada. True si termino sin interrupcion."""
        end = time.perf_counter() + seconds
        while True:
            remaining = end - time.perf_counter()
            if remaining <= 0:
                return True
            if self._stop_flag.is_set():
                return False
            time.sleep(min(remaining, 0.01))

    def _apply(self, event, speed=1.0):
        kind = event["type"]
        if kind == "move":
            self._mouse.position = (event["x"], event["y"])
        elif kind == "click":
            self._do_click(event)
        elif kind == "mouse_drag":
            self._do_drag(event, speed)
        elif kind == "scroll":
            self._mouse.position = (event["x"], event["y"])
            self._mouse.scroll(event["dx"], event["dy"])
        elif kind == "key_down":
            self._keyboard.press(str_to_key(event["key"]))
        elif kind == "key_up":
            self._keyboard.release(str_to_key(event["key"]))
        elif kind == "key_press":
            key = str_to_key(event["key"])
            self._keyboard.press(key)
            self._keyboard.release(key)
        elif kind == "type_text":
            self._do_type_text(event, speed)
        elif kind == "wait":
            pass
        elif kind == "run_program":
            self._do_run_program(event)
        elif kind == "open_url":
            webbrowser.open(event.get("url", ""))
        elif kind == "message":
            if self.on_message:
                self.on_message(event.get("title", ""), event.get("text", ""))
        elif kind == "capture_image":
            self._do_capture_image(event)
        elif kind == "find_image":
            return self._do_find_image(event, speed)
        elif kind == "find_ocr":
            return self._do_find_ocr(event, speed)
        return None

    def _do_click(self, event):
        self._mouse.position = (event["x"], event["y"])
        button = getattr(mouse.Button, event.get("button", "left"))
        action = event.get("action", "click")
        times = 2 if event.get("double") else 1
        for _ in range(times):
            if action == "down":
                self._mouse.press(button)
            elif action == "up":
                self._mouse.release(button)
            else:
                self._mouse.click(button)

    def _do_drag(self, event, speed):
        button = getattr(mouse.Button, event.get("button", "left"))
        x1, y1 = event["x1"], event["y1"]
        x2, y2 = event["x2"], event["y2"]
        duration = max(event.get("duration", 0.3), 0.0) / max(speed, 0.01)
        self._mouse.position = (x1, y1)
        self._mouse.press(button)
        steps = max(int(duration / 0.02), 1)
        for step in range(1, steps + 1):
            if self._stop_flag.is_set():
                break
            fraction = step / steps
            self._mouse.position = (
                x1 + (x2 - x1) * fraction,
                y1 + (y2 - y1) * fraction,
            )
            time.sleep(duration / steps)
        self._mouse.position = (x2, y2)
        self._mouse.release(button)

    def _do_type_text(self, event, speed):
        interval = max(event.get("interval", 0.02), 0.0) / max(speed, 0.01)
        for char in event.get("text", ""):
            if self._stop_flag.is_set():
                return
            if char == "\n":
                key = keyboard.Key.enter
            else:
                key = char
            self._keyboard.press(key)
            self._keyboard.release(key)
            if interval:
                time.sleep(interval)

    def _do_run_program(self, event):
        path = event.get("path", "")
        if not path:
            return
        args = shlex.split(event.get("args", ""), posix=False)
        try:
            subprocess.Popen([path, *args], shell=False)
        except OSError:
            subprocess.Popen(f'"{path}" {event.get("args", "")}', shell=True)

    def _region_of(self, event):
        return (
            event.get("x", 0),
            event.get("y", 0),
            event.get("width", 0),
            event.get("height", 0),
        )

    def _do_capture_image(self, event):
        path = event.get("save_path", "")
        if not path:
            return
        try:
            image_search.save_capture(path, region=self._region_of(event))
        except Exception:  # noqa: BLE001 - no se interrumpe la macro por un error de captura
            pass

    def _do_find_image(self, event, speed):
        """Busca la imagen de referencia en pantalla.

        Si se encuentra, ejecuta la accion de mouse indicada y continua con
        el siguiente paso (devuelve None). Si no se encuentra, espera
        'not_found_wait' segundos y, si 'not_found_goto' es > 0, devuelve ese
        numero de paso (1-based) para que _play_once salte ahi."""
        path = event.get("image_path", "")
        location = None
        if path:
            try:
                location = image_search.locate_image(
                    path,
                    region=self._region_of(event),
                    confidence=event.get("confidence", 0.8),
                )
            except Exception:  # noqa: BLE001 - dependencia faltante u otro error: no encontrada
                location = None
        return self._resolve_found_location(event, location, speed)

    def _do_find_ocr(self, event, speed):
        """Busca un texto en pantalla por OCR y aplica las mismas opciones
        de "si se encuentra / si no se encuentra" que _do_find_image."""
        text = event.get("text", "")
        location = None
        if text:
            try:
                location = image_search.locate_text(
                    text,
                    region=self._region_of(event),
                    lang=event.get("lang", "eng"),
                    case_sensitive=event.get("case_sensitive", False),
                )
            except Exception:  # noqa: BLE001 - dependencia faltante u otro error: no encontrada
                location = None
        return self._resolve_found_location(event, location, speed)

    def _resolve_found_location(self, event, location, speed):
        if location is not None:
            x = location[0] + event.get("offset_x", 0)
            y = location[1] + event.get("offset_y", 0)
            self._do_found_action(event, x, y)
            return None

        wait_seconds = max(event.get("not_found_wait", 0.0), 0.0) / max(speed, 0.01)
        if not self._sleep(wait_seconds):
            return None
        goto = event.get("not_found_goto", 0)
        return goto if goto and goto > 0 else None

    def _do_found_action(self, event, x, y):
        action = event.get("found_action", "click")
        if action == "none":
            return
        self._mouse.position = (x, y)
        if action == "move":
            return
        button = mouse.Button.right if action == "right_click" else mouse.Button.left
        times = 2 if action == "double_click" else 1
        for _ in range(times):
            self._mouse.click(button)
