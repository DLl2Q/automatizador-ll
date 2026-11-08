"""Automatizador - clon de Macro Recorder (Martels Media) con panel de acciones.

Graba movimientos de mouse, clics, scroll y teclado, y los reproduce
respetando los tiempos originales. Ademas incluye un panel de acciones
donde se puede armar o editar una macro a mano, accion por accion
(mover el mouse, hacer clic, arrastrar, usar la rueda, presionar/soltar
una tecla, escribir texto, agregar una pausa, ejecutar un programa, abrir
una pagina web o mostrar un mensaje), sin necesidad de grabarla.

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

from core import actions, storage  # noqa: E402
from core.action_dialog import ask_action  # noqa: E402
from core.player import Player  # noqa: E402
from core.recorder import Recorder  # noqa: E402

APP_TITLE = "Automatizador"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("960x640")
        self.root.minsize(840, 560)

        self.current_events = []
        self.current_macro_name = None
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
            on_message=self._on_play_message,
        )

        self._build_ui()
        self._refresh_macro_list()
        self._refresh_tree()
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

        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        left = ttk.LabelFrame(paned, text="Macros guardadas")
        paned.add(left, weight=1)
        self._build_macro_panel(left)

        right = ttk.Frame(paned)
        paned.add(right, weight=3)
        self._build_actions_panel(right)
        self._build_record_panel(right)
        self._build_play_panel(right)

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", **pad)
        ttk.Label(status_frame, textvariable=self.status_var, foreground="blue").pack(
            side="left"
        )

    def _build_macro_panel(self, parent):
        self.listbox = tk.Listbox(parent, activestyle="dotbox")
        self.listbox.pack(side="top", fill="both", expand=True, padx=8, pady=8)

        scroll = ttk.Scrollbar(parent, orient="vertical", command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scroll.set)

        buttons = ttk.Frame(parent)
        buttons.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(buttons, text="Nueva macro", command=self._new_macro).pack(
            fill="x", pady=2
        )
        ttk.Button(buttons, text="Cargar", command=self._load_selected).pack(
            fill="x", pady=2
        )
        ttk.Button(buttons, text="Guardar", command=self._save).pack(fill="x", pady=2)
        ttk.Button(buttons, text="Guardar como...", command=self._save_as).pack(
            fill="x", pady=2
        )
        ttk.Button(buttons, text="Eliminar", command=self._delete_selected).pack(
            fill="x", pady=2
        )
        ttk.Button(buttons, text="Refrescar", command=self._refresh_macro_list).pack(
            fill="x", pady=2
        )

    def _build_actions_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Panel de acciones")
        frame.pack(fill="both", expand=True, padx=0, pady=(0, 6))

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

        columns = ("idx", "delay", "tipo", "detalle")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.tree.heading("idx", text="#")
        self.tree.heading("delay", text="Retraso (s)")
        self.tree.heading("tipo", text="Accion")
        self.tree.heading("detalle", text="Detalle")
        self.tree.column("idx", width=32, anchor="center", stretch=False)
        self.tree.column("delay", width=80, anchor="center", stretch=False)
        self.tree.column("tipo", width=150, stretch=False)
        self.tree.column("detalle", width=320)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _e: self._edit_action())

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=tree_scroll.set)

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(buttons, text="Agregar...", command=self._add_action).pack(
            side="left", padx=2
        )
        ttk.Button(buttons, text="Editar...", command=self._edit_action).pack(
            side="left", padx=2
        )
        ttk.Button(buttons, text="Duplicar", command=self._duplicate_action).pack(
            side="left", padx=2
        )
        ttk.Button(buttons, text="Eliminar", command=self._delete_action).pack(
            side="left", padx=2
        )
        ttk.Button(buttons, text="Subir", command=lambda: self._move_action(-1)).pack(
            side="left", padx=2
        )
        ttk.Button(buttons, text="Bajar", command=lambda: self._move_action(1)).pack(
            side="left", padx=2
        )
        ttk.Button(buttons, text="Vaciar lista", command=self._clear_actions).pack(
            side="right", padx=2
        )

    def _build_record_panel(self, parent):
        record_frame = ttk.LabelFrame(parent, text="Grabacion")
        record_frame.pack(fill="x", pady=(0, 6))
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

    def _build_play_panel(self, parent):
        play_frame = ttk.LabelFrame(parent, text="Reproduccion")
        play_frame.pack(fill="x")

        row1 = ttk.Frame(play_frame)
        row1.pack(fill="x", padx=8, pady=4)
        ttk.Label(row1, text="Velocidad:").pack(side="left")
        ttk.Spinbox(
            row1, from_=0.1, to=10.0, increment=0.1, width=6, textvariable=self.speed_var
        ).pack(side="left", padx=(4, 16))
        ttk.Label(row1, text="Repeticiones (0 = infinito):").pack(side="left")
        ttk.Spinbox(row1, from_=0, to=9999, width=6, textvariable=self.repeat_var).pack(
            side="left", padx=4
        )

        row2 = ttk.Frame(play_frame)
        row2.pack(fill="x", padx=8, pady=(0, 6))
        self.play_button = ttk.Button(
            row2, text="Reproducir (F10)", command=self.toggle_playback
        )
        self.play_button.pack(side="right")

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
            self._refresh_tree()
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
            self.status_var.set("No hay acciones cargadas o grabadas para reproducir.")
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

    def _on_play_message(self, title, text):
        self.root.after(0, lambda: messagebox.showinfo(title or APP_TITLE, text))

    def emergency_stop(self):
        if self.recorder.is_recording:
            self.current_events = self.recorder.stop()
            self.record_button.config(text="Grabar (F9)")
            self._refresh_tree()
        if self.player.is_playing:
            self.player.stop()
            self.play_button.config(text="Reproducir (F10)")
        self.status_var.set("Parada de emergencia.")

    # ---------- Panel de acciones ----------
    def _refresh_tree(self, select_index=None):
        self.tree.delete(*self.tree.get_children())
        for index, event in enumerate(self.current_events):
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    index + 1,
                    f"{event.get('delay', 0.0):.3f}",
                    actions.label_for(event.get("type")),
                    actions.describe(event),
                ),
            )
        if select_index is not None and 0 <= select_index < len(self.current_events):
            iid = str(select_index)
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.tree.see(iid)

    def _selected_index(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _add_action(self):
        if self.player.is_playing or self.recorder.is_recording:
            return
        event = ask_action(self.root)
        if event is None:
            return
        index = self._selected_index()
        insert_at = index + 1 if index is not None else len(self.current_events)
        self.current_events.insert(insert_at, event)
        self._refresh_tree(select_index=insert_at)
        self.status_var.set("Accion agregada.")

    def _edit_action(self):
        if self.player.is_playing or self.recorder.is_recording:
            return
        index = self._selected_index()
        if index is None:
            messagebox.showinfo(APP_TITLE, "Selecciona una accion de la lista.")
            return
        event = ask_action(self.root, self.current_events[index])
        if event is None:
            return
        self.current_events[index] = event
        self._refresh_tree(select_index=index)
        self.status_var.set("Accion actualizada.")

    def _duplicate_action(self):
        index = self._selected_index()
        if index is None:
            messagebox.showinfo(APP_TITLE, "Selecciona una accion de la lista.")
            return
        clone = dict(self.current_events[index])
        self.current_events.insert(index + 1, clone)
        self._refresh_tree(select_index=index + 1)
        self.status_var.set("Accion duplicada.")

    def _delete_action(self):
        index = self._selected_index()
        if index is None:
            messagebox.showinfo(APP_TITLE, "Selecciona una accion de la lista.")
            return
        del self.current_events[index]
        next_index = min(index, len(self.current_events) - 1)
        self._refresh_tree(select_index=next_index if next_index >= 0 else None)
        self.status_var.set("Accion eliminada.")

    def _move_action(self, direction):
        index = self._selected_index()
        if index is None:
            messagebox.showinfo(APP_TITLE, "Selecciona una accion de la lista.")
            return
        new_index = index + direction
        if not 0 <= new_index < len(self.current_events):
            return
        events = self.current_events
        events[index], events[new_index] = events[new_index], events[index]
        self._refresh_tree(select_index=new_index)

    def _clear_actions(self):
        if not self.current_events:
            return
        if messagebox.askyesno(APP_TITLE, "¿Vaciar toda la lista de acciones?"):
            self.current_events = []
            self._refresh_tree()
            self.status_var.set("Lista de acciones vaciada.")

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

    def _new_macro(self):
        if self.current_events and not messagebox.askyesno(
            APP_TITLE, "Se perderan las acciones actuales no guardadas. ¿Continuar?"
        ):
            return
        self.current_events = []
        self.current_macro_name = None
        self._refresh_tree()
        self.status_var.set("Nueva macro vacia.")

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
        self.current_macro_name = name
        self._refresh_tree()
        self.status_var.set(f"Macro '{name}' cargada: {len(self.current_events)} acciones.")

    def _save(self):
        if not self.current_events:
            messagebox.showinfo(APP_TITLE, "No hay acciones para guardar.")
            return
        if not self.current_macro_name:
            self._save_as()
            return
        path = storage.save_macro(self.current_macro_name, self.current_events)
        self.status_var.set(f"Macro guardada en {path}")
        self._refresh_macro_list()

    def _save_as(self):
        if not self.current_events:
            messagebox.showinfo(
                APP_TITLE, "Primero grava, carga o agrega acciones antes de guardar."
            )
            return
        name = simpledialog.askstring(APP_TITLE, "Nombre de la macro:", parent=self.root)
        if not name:
            return
        path = storage.save_macro(name, self.current_events)
        self.current_macro_name = name
        self.status_var.set(f"Macro guardada en {path}")
        self._refresh_macro_list()

    def _delete_selected(self):
        name = self._selected_name()
        if not name:
            messagebox.showinfo(APP_TITLE, "Selecciona una macro de la lista.")
            return
        if messagebox.askyesno(APP_TITLE, f"¿Eliminar la macro '{name}'?"):
            storage.delete_macro(name)
            if self.current_macro_name == name:
                self.current_macro_name = None
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
