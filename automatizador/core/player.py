"""Reproduccion de macros grabadas respetando los tiempos originales."""

import threading
import time

from pynput import keyboard, mouse

from .recorder import str_to_key


class Player:
    """Reproduce una lista de eventos generada por Recorder."""

    def __init__(self, on_progress=None, on_finished=None):
        self.on_progress = on_progress
        self.on_finished = on_finished

        self._mouse = mouse.Controller()
        self._keyboard = keyboard.Controller()
        self._stop_flag = threading.Event()
        self._thread = None

    @property
    def is_playing(self):
        return self._thread is not None and self._thread.is_alive()

    def play(self, events, speed=1.0, repeat=1):
        """Inicia la reproduccion en un hilo aparte.

        speed: multiplicador de velocidad (2.0 = el doble de rapido).
        repeat: numero de repeticiones; 0 o negativo significa infinito.
        """
        if self.is_playing or not events:
            return
        self._stop_flag.clear()
        self._thread = threading.Thread(
            target=self._run, args=(list(events), speed, repeat), daemon=True
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
        start = time.perf_counter()
        total = len(events)
        for index, event in enumerate(events):
            if self._stop_flag.is_set():
                return
            target = event["time"] / speed
            self._wait_until(start, target)
            if self._stop_flag.is_set():
                return
            self._apply(event)
            if self.on_progress:
                self.on_progress(index + 1, total)

    def _wait_until(self, start, target_offset):
        while True:
            remaining = target_offset - (time.perf_counter() - start)
            if remaining <= 0 or self._stop_flag.is_set():
                return
            time.sleep(min(remaining, 0.01))

    def _apply(self, event):
        kind = event["type"]
        if kind == "move":
            self._mouse.position = (event["x"], event["y"])
        elif kind == "click":
            self._mouse.position = (event["x"], event["y"])
            button = getattr(mouse.Button, event["button"])
            if event["pressed"]:
                self._mouse.press(button)
            else:
                self._mouse.release(button)
        elif kind == "scroll":
            self._mouse.position = (event["x"], event["y"])
            self._mouse.scroll(event["dx"], event["dy"])
        elif kind == "key_down":
            self._keyboard.press(str_to_key(event["key"]))
        elif kind == "key_up":
            self._keyboard.release(str_to_key(event["key"]))
