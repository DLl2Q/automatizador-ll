"""Automatizador - clon basico de Macro Recorder (Martels Media).

Graba movimientos de mouse, clics, scroll y teclado, y los reproduce
respetando los tiempos originales. Permite guardar y cargar macros,
controlar la velocidad y el numero de repeticiones.

Atajos globales (funcionan aunque la ventana no tenga el foco):
    F9  -> iniciar / detener grabacion
    F10 -> iniciar / detener reproduccion
    Esc -> detener grabacion y reproduccion (parada de emergencia)
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pynput import keyboard  # noqa: E402

from core import storage  # noqa: E402
from core.player import Player  # noqa: E402
from core.recorder import Recorder  # noqa: E402

APP_TITLE = "Automatizador"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("460x520")
        self.root.minsize(420, 480)

        self.current_events = []
        self.record_mouse_move = tk.BooleanVar(value=True)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.repeat_var = tk.IntVar(value=1)
        self.status_var = tk.StringVar(value="Listo.")

        self.recorder = Recorder(
            on_event=self._on_record_event,
            record_mouse_move=self.record_mouse_move.get(),
        )
        self.player = Player(
            on_progress=self._on_play_progress,
            on_finished=self._on_play_finished,
        )

        self._build_ui()
        self._refresh_macro_list()
        self._start_hotkeys()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- UI ----------
    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)
        ttk.Label(top, text=APP_TITLE, font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Label(
            top, text="F9 Grabar  |  F10 Reproducir  |  Esc Detener", foreground="gray"
        ).pack(side="right")

        list_frame = ttk.LabelFrame(self.root, text="Macros guardadas")
        list_frame.pack(fill="both", expand=True, **pad)

        self.listbox = tk.Listbox(list_frame, activestyle="dotbox")
        self.listbox.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        self.listbox.bind("<<ListboxSelect>>", self._on_select_macro)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))
        self.listbox.config(yscrollcommand=scroll.set)

        list_buttons = ttk.Frame(self.root)
        list_buttons.pack(fill="x", **pad)
        ttk.Button(list_buttons, text="Cargar", command=self._load_selected).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(list_buttons, text="Guardar como...", command=self._save_as).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(list_buttons, text="Eliminar", command=self._delete_selected).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(list_buttons, text="Refrescar", command=self._refresh_macro_list).pack(
            side="left", expand=True, fill="x", padx=2
        )

        record_frame = ttk.LabelFrame(self.root, text="Grabacion")
        record_frame.pack(fill="x", **pad)
        ttk.Checkbutton(
            record_frame,
            text="Grabar movimientos del mouse",
            variable=self.record_mouse_move,
            command=self._toggle_record_mouse_move,
        ).pack(side="left", padx=8, pady=6)
        self.record_button = ttk.Button(
            record_frame, text="Grabar (F9)", command=self.toggle_recording
        )
        self.record_button.pack(side="right", padx=8, pady=6)

        play_frame = ttk.LabelFrame(self.root, text="Reproduccion")
        play_frame.pack(fill="x", **pad)

        row1 = ttk.Frame(play_frame)
        row1.pack(fill="x", padx=8, pady=4)
        ttk.Label(row1, text="Velocidad:").pack(side="left")
        ttk.Spinbox(
            row1, from_=0.1, to=10.0, increment=0.1, width=6, textvariable=self.speed_var
        ).pack(side="left", padx=(4, 16))
        ttk.Label(row1, text="Repeticiones (0 = infinito):").pack(side="left")
        ttk.Spinbox(
            row1, from_=0, to=9999, width=6, textvariable=self.repeat_var
        ).pack(side="left", padx=4)

        row2 = ttk.Frame(play_frame)
        row2.pack(fill="x", padx=8, pady=(0, 6))
        self.play_button = ttk.Button(
            row2, text="Reproducir (F10)", command=self.toggle_playback
        )
        self.play_button.pack(side="right")

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", **pad)
        ttk.Label(status_frame, textvariable=self.status_var, foreground="blue").pack(
            side="left"
        )

    # ---------- Hotkeys globales ----------
    def _start_hotkeys(self):
        def on_press(key):
            if key == keyboard.Key.f9:
                self.root.after(0, self.toggle_recording)
            elif key == keyboard.Key.f10:
                self.root.after(0, self.toggle_playback)
            elif key == keyboard.Key.esc:
                self.root.after(0, self.emergency_stop)

        self._hotkey_listener = keyboard.Listener(on_press=on_press)
        self._hotkey_listener.start()

    # ---------- Grabacion ----------
    def toggle_recording(self):
        if self.player.is_playing:
            return
        if self.recorder.is_recording:
            self.current_events = self.recorder.stop()
            self.record_button.config(text="Grabar (F9)")
            self.status_var.set(f"Grabacion detenida: {len(self.current_events)} eventos.")
        else:
            self.recorder.record_mouse_move = self.record_mouse_move.get()
            self.recorder.start()
            self.record_button.config(text="Detener (F9)")
            self.status_var.set("Grabando... 0 eventos")

    def _toggle_record_mouse_move(self):
        self.recorder.record_mouse_move = self.record_mouse_move.get()

    def _on_record_event(self, total):
        self.root.after(0, lambda: self.status_var.set(f"Grabando... {total} eventos"))

    # ---------- Reproduccion ----------
    def toggle_playback(self):
        if self.recorder.is_recording:
            return
        if self.player.is_playing:
            self.player.stop()
            self.status_var.set("Deteniendo reproduccion...")
            return
        if not self.current_events:
            self.status_var.set("No hay una macro cargada o grabada para reproducir.")
            return
        speed = max(self.speed_var.get(), 0.1)
        repeat = self.repeat_var.get()
        self.play_button.config(text="Detener (F10)")
        self.status_var.set("Reproduciendo...")
        self.player.play(self.current_events, speed=speed, repeat=repeat)

    def _on_play_progress(self, done, total):
        self.root.after(0, lambda: self.status_var.set(f"Reproduciendo... {done}/{total}"))

    def _on_play_finished(self):
        def update():
            self.play_button.config(text="Reproducir (F10)")
            self.status_var.set("Reproduccion finalizada.")

        self.root.after(0, update)

    def emergency_stop(self):
        if self.recorder.is_recording:
            self.current_events = self.recorder.stop()
            self.record_button.config(text="Grabar (F9)")
        if self.player.is_playing:
            self.player.stop()
            self.play_button.config(text="Reproducir (F10)")
        self.status_var.set("Parada de emergencia.")

    # ---------- Macros guardadas ----------
    def _refresh_macro_list(self):
        self.listbox.delete(0, tk.END)
        for name in storage.list_macros():
            self.listbox.insert(tk.END, name)

    def _selected_name(self):
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self.listbox.get(selection[0])

    def _on_select_macro(self, _event):
        pass

    def _load_selected(self):
        name = self._selected_name()
        if not name:
            messagebox.showinfo(APP_TITLE, "Selecciona una macro de la lista.")
            return
        try:
            self.current_events = storage.load_macro(name)
        except (OSError, ValueError) as exc:
            messagebox.showerror(APP_TITLE, f"No se pudo cargar '{name}':\n{exc}")
            return
        self.status_var.set(f"Macro '{name}' cargada: {len(self.current_events)} eventos.")

    def _save_as(self):
        if not self.current_events:
            messagebox.showinfo(
                APP_TITLE, "Primero grava o carga una macro antes de guardar."
            )
            return
        name = simpledialog.askstring(APP_TITLE, "Nombre de la macro:", parent=self.root)
        if not name:
            return
        path = storage.save_macro(name, self.current_events)
        self.status_var.set(f"Macro guardada en {path}")
        self._refresh_macro_list()

    def _delete_selected(self):
        name = self._selected_name()
        if not name:
            messagebox.showinfo(APP_TITLE, "Selecciona una macro de la lista.")
            return
        if messagebox.askyesno(APP_TITLE, f"¿Eliminar la macro '{name}'?"):
            storage.delete_macro(name)
            self._refresh_macro_list()
            self.status_var.set(f"Macro '{name}' eliminada.")

    # ---------- Cierre ----------
    def _on_close(self):
        if self.recorder.is_recording:
            self.recorder.stop()
        if self.player.is_playing:
            self.player.stop()
        if self._hotkey_listener is not None:
            self._hotkey_listener.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
