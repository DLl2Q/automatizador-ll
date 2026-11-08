"""Automatizador - clon de Macro Recorder (Martels Media) con panel de acciones.

Graba movimientos de mouse, clics, scroll y teclado, y los reproduce
respetando los tiempos originales. Ademas incluye un panel de acciones
donde se puede armar o editar una macro a mano, accion por accion
(mover el mouse, hacer clic, arrastrar, usar la rueda, presionar/soltar
una tecla, escribir texto, agregar una pausa, ejecutar un programa, abrir
una pagina web, mostrar un mensaje, capturar o buscar una imagen en
pantalla, o buscar texto en pantalla por OCR), sin necesidad de grabarla.

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

# ---------- Paleta de colores de la interfaz ----------
COLOR_BG = "#f2f4f7"
COLOR_PANEL = "#ffffff"
COLOR_PRIMARY = "#1f6feb"
COLOR_PRIMARY_DARK = "#1554b5"
COLOR_RECORD = "#d64550"
COLOR_RECORD_DARK = "#a9333c"
COLOR_PLAY = "#1f9d55"
COLOR_PLAY_DARK = "#167a41"
COLOR_TEXT = "#1f2933"
COLOR_MUTED = "#6b7280"
COLOR_ROW_ODD = "#ffffff"
COLOR_ROW_EVEN = "#eef2f9"
COLOR_SELECTION = "#1f6feb"

# ---------- Iconos en texto (sin dependencias de imagenes) ----------
ICON_NEW = "\U0001F4C4"
ICON_OPEN = "\U0001F4C2"
ICON_SAVE = "\U0001F4BE"
ICON_SAVE_AS = "\U0001F4BE"
ICON_DELETE = "\U0001F5D1"
ICON_REFRESH = "\U0001F504"
ICON_ADD = "\u2795"
ICON_EDIT = "\u270E"
ICON_DUP = "\u29C9"
ICON_UP = "\u25B2"
ICON_DOWN = "\u25BC"
ICON_CLEAR = "\U0001F9F9"
ICON_RECORD = "\u23FA"
ICON_STOP = "\u23F9"
ICON_PLAY = "\u25B6"
ICON_SEARCH = "\U0001F50D"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1040x680")
        self.root.minsize(900, 600)
        self.root.configure(bg=COLOR_BG)

        self.current_events = []
        self.current_macro_name = None
        self.record_mouse_move = tk.BooleanVar(value=True)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.repeat_var = tk.IntVar(value=1)
        self.status_var = tk.StringVar(value="Listo.")
        self.macro_filter_var = tk.StringVar(value="")
        self._all_macro_names = []

        self.recorder = Recorder(
            on_event=self._on_record_event,
            record_mouse_move=self.record_mouse_move.get(),
        )
        self.player = Player(
            on_progress=self._on_play_progress,
            on_finished=self._on_play_finished,
            on_message=self._on_play_message,
        )

        self._setup_style()
        self._build_menu()
        self._build_ui()
        self._refresh_macro_list()
        self._refresh_tree()
        self._start_hotkeys()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- Estilo visual ----------
    def _setup_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        default_font = ("Segoe UI", 10)
        bold_font = ("Segoe UI", 10, "bold")
        self.root.option_add("*Font", default_font)

        style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT, font=default_font)
        style.configure("TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_PANEL)
        style.configure(
            "TLabelframe", background=COLOR_PANEL, foreground=COLOR_TEXT, borderwidth=1
        )
        style.configure(
            "TLabelframe.Label",
            background=COLOR_PANEL,
            foreground=COLOR_PRIMARY_DARK,
            font=bold_font,
        )
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT)
        style.configure("Panel.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT)
        style.configure("Muted.TLabel", background=COLOR_BG, foreground=COLOR_MUTED)
        style.configure("Title.TLabel", background=COLOR_BG, foreground=COLOR_PRIMARY_DARK)
        style.configure("Status.TLabel", background=COLOR_BG, foreground=COLOR_PRIMARY_DARK)

        style.configure("TButton", padding=6, relief="flat")
        style.map("TButton", background=[("active", "#dfe7f3")])

        style.configure(
            "Record.TButton",
            background=COLOR_RECORD,
            foreground="white",
            padding=8,
        )
        style.map(
            "Record.TButton",
            background=[("active", COLOR_RECORD_DARK), ("pressed", COLOR_RECORD_DARK)],
        )

        style.configure(
            "Play.TButton",
            background=COLOR_PLAY,
            foreground="white",
            padding=8,
        )
        style.map(
            "Play.TButton",
            background=[("active", COLOR_PLAY_DARK), ("pressed", COLOR_PLAY_DARK)],
        )

        style.configure("Treeview", rowheight=24, font=default_font, background=COLOR_PANEL)
        style.configure("Treeview.Heading", font=bold_font, background="#dfe7f3")
        style.map(
            "Treeview",
            background=[("selected", COLOR_SELECTION)],
            foreground=[("selected", "white")],
        )

    # ---------- Menu ----------
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Nueva macro", command=self._new_macro)
        file_menu.add_command(label="Cargar seleccionada", command=self._load_selected)
        file_menu.add_separator()
        file_menu.add_command(label="Guardar", command=self._save)
        file_menu.add_command(label="Guardar como...", command=self._save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Eliminar macro seleccionada", command=self._delete_selected)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._on_close)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        actions_menu = tk.Menu(menubar, tearoff=False)
        actions_menu.add_command(label="Agregar...", command=self._add_action)
        actions_menu.add_command(label="Editar...", command=self._edit_action)
        actions_menu.add_command(label="Duplicar", command=self._duplicate_action)
        actions_menu.add_command(label="Eliminar", command=self._delete_action)
        actions_menu.add_separator()
        actions_menu.add_command(label="Subir", command=lambda: self._move_action(-1))
        actions_menu.add_command(label="Bajar", command=lambda: self._move_action(1))
        actions_menu.add_separator()
        actions_menu.add_command(label="Vaciar lista", command=self._clear_actions)
        menubar.add_cascade(label="Acciones", menu=actions_menu)

        run_menu = tk.Menu(menubar, tearoff=False)
        run_menu.add_command(label="Grabar / Detener (F9)", command=self.toggle_recording)
        run_menu.add_command(label="Reproducir / Detener (F10)", command=self.toggle_playback)
        run_menu.add_separator()
        run_menu.add_command(label="Parada de emergencia (Esc)", command=self.emergency_stop)
        menubar.add_cascade(label="Ejecucion", menu=run_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Acerca de", command=self._show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        self.root.config(menu=menubar)

    def _show_about(self):
        messagebox.showinfo(
            APP_TITLE,
            f"{APP_TITLE}\n\n"
            "Clon de Macro Recorder con panel de acciones, busqueda de "
            "imagenes/texto en pantalla (OCR) y grabacion/reproduccion "
            "de mouse y teclado.",
        )

    # ---------- UI ----------
    def _build_ui(self):
        top = tk.Frame(self.root, bg=COLOR_PRIMARY, height=56)
        top.pack(fill="x")
        inner_top = tk.Frame(top, bg=COLOR_PRIMARY)
        inner_top.pack(fill="both", expand=True, padx=16, pady=10)
        tk.Label(
            inner_top,
            text=APP_TITLE,
            font=("Segoe UI", 16, "bold"),
            bg=COLOR_PRIMARY,
            fg="white",
        ).pack(side="left")
        tk.Label(
            inner_top,
            text="F9 Grabar   |   F10 Reproducir   |   Esc Detener",
            bg=COLOR_PRIMARY,
            fg="#dbe7fb",
            font=("Segoe UI", 9),
        ).pack(side="right")

        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.LabelFrame(paned, text="Macros guardadas")
        paned.add(left, weight=1)
        self._build_macro_panel(left)

        right = ttk.Frame(paned)
        paned.add(right, weight=3)
        self._build_actions_panel(right)
        self._build_record_panel(right)
        self._build_play_panel(right)

        status_frame = tk.Frame(self.root, bg=COLOR_BG)
        status_frame.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel").pack(
            side="left"
        )
        self.progress = ttk.Progressbar(
            status_frame, orient="horizontal", mode="determinate", length=220
        )
        self.progress.pack(side="right")

    def _build_macro_panel(self, parent):
        search_frame = ttk.Frame(parent, style="Panel.TFrame")
        search_frame.pack(side="top", fill="x", padx=8, pady=(8, 4))
        ttk.Label(search_frame, text=ICON_SEARCH, style="Panel.TLabel").pack(side="left")
        filter_entry = ttk.Entry(search_frame, textvariable=self.macro_filter_var)
        filter_entry.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.macro_filter_var.trace_add("write", lambda *_a: self._apply_macro_filter())

        list_frame = ttk.Frame(parent, style="Panel.TFrame")
        list_frame.pack(side="top", fill="both", expand=True, padx=8, pady=(0, 8))
        self.listbox = tk.Listbox(
            list_frame,
            activestyle="dotbox",
            highlightthickness=0,
            relief="flat",
            selectbackground=COLOR_SELECTION,
            selectforeground="white",
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<Double-1>", lambda _e: self._load_selected())

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scroll.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scroll.set)

        buttons = ttk.Frame(parent, style="Panel.TFrame")
        buttons.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(
            buttons, text=f"{ICON_NEW} Nueva macro", command=self._new_macro
        ).pack(fill="x", pady=2)
        ttk.Button(
            buttons, text=f"{ICON_OPEN} Cargar", command=self._load_selected
        ).pack(fill="x", pady=2)
        ttk.Button(
            buttons, text=f"{ICON_SAVE} Guardar", command=self._save
        ).pack(fill="x", pady=2)
        ttk.Button(
            buttons, text=f"{ICON_SAVE_AS} Guardar como...", command=self._save_as
        ).pack(fill="x", pady=2)
        ttk.Button(
            buttons, text=f"{ICON_DELETE} Eliminar", command=self._delete_selected
        ).pack(fill="x", pady=2)
        ttk.Button(
            buttons, text=f"{ICON_REFRESH} Refrescar", command=self._refresh_macro_list
        ).pack(fill="x", pady=2)

    def _build_actions_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Panel de acciones")
        frame.pack(fill="both", expand=True, padx=0, pady=(0, 6))

        tree_frame = ttk.Frame(frame, style="Panel.TFrame")
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
        self.tree.column("tipo", width=170, stretch=False)
        self.tree.column("detalle", width=320)
        self.tree.tag_configure("oddrow", background=COLOR_ROW_ODD)
        self.tree.tag_configure("evenrow", background=COLOR_ROW_EVEN)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _e: self._edit_action())
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=tree_scroll.set)

        buttons = ttk.Frame(frame, style="Panel.TFrame")
        buttons.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(buttons, text=f"{ICON_ADD} Agregar...", command=self._add_action).pack(
            side="left", padx=2
        )
        ttk.Button(buttons, text=f"{ICON_EDIT} Editar...", command=self._edit_action).pack(
            side="left", padx=2
        )
        ttk.Button(buttons, text=f"{ICON_DUP} Duplicar", command=self._duplicate_action).pack(
            side="left", padx=2
        )
        ttk.Button(buttons, text=f"{ICON_DELETE} Eliminar", command=self._delete_action).pack(
            side="left", padx=2
        )
        ttk.Button(
            buttons, text=f"{ICON_UP} Subir", command=lambda: self._move_action(-1)
        ).pack(side="left", padx=2)
        ttk.Button(
            buttons, text=f"{ICON_DOWN} Bajar", command=lambda: self._move_action(1)
        ).pack(side="left", padx=2)
        ttk.Button(
            buttons, text=f"{ICON_CLEAR} Vaciar lista", command=self._clear_actions
        ).pack(side="right", padx=2)

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
            record_frame,
            text=f"{ICON_RECORD} Grabar (F9)",
            style="Record.TButton",
            command=self.toggle_recording,
        )
        self.record_button.pack(side="right", padx=8, pady=6)

    def _build_play_panel(self, parent):
        play_frame = ttk.LabelFrame(parent, text="Reproduccion")
        play_frame.pack(fill="x")

        row1 = ttk.Frame(play_frame, style="Panel.TFrame")
        row1.pack(fill="x", padx=8, pady=4)
        ttk.Label(row1, text="Velocidad:", style="Panel.TLabel").pack(side="left")
        ttk.Spinbox(
            row1, from_=0.1, to=10.0, increment=0.1, width=6, textvariable=self.speed_var
        ).pack(side="left", padx=(4, 16))
        ttk.Label(row1, text="Repeticiones (0 = infinito):", style="Panel.TLabel").pack(
            side="left"
        )
        ttk.Spinbox(row1, from_=0, to=9999, width=6, textvariable=self.repeat_var).pack(
            side="left", padx=4
        )

        row2 = ttk.Frame(play_frame, style="Panel.TFrame")
        row2.pack(fill="x", padx=8, pady=(0, 6))
        self.play_button = ttk.Button(
            row2,
            text=f"{ICON_PLAY} Reproducir (F10)",
            style="Play.TButton",
            command=self.toggle_playback,
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
            self.record_button.config(text=f"{ICON_RECORD} Grabar (F9)")
            self._refresh_tree()
            self.status_var.set(f"Grabacion detenida: {len(self.current_events)} eventos.")
        else:
            self.recorder.record_mouse_move = self.record_mouse_move.get()
            self.recorder.start()
            self.record_button.config(text=f"{ICON_STOP} Detener (F9)")
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
        self.progress.config(value=0, maximum=max(len(self.current_events), 1))
        self.play_button.config(text=f"{ICON_STOP} Detener (F10)")
        self.status_var.set("Reproduciendo...")
        self.player.play(self.current_events, speed=speed, repeat=repeat)

    def _on_play_progress(self, done, total):
        def update():
            self.status_var.set(f"Reproduciendo... {done}/{total}")
            self.progress.config(maximum=max(total, 1), value=done)

        self.root.after(0, update)

    def _on_play_finished(self):
        def update():
            self.play_button.config(text=f"{ICON_PLAY} Reproducir (F10)")
            self.status_var.set("Reproduccion finalizada.")
            self.progress.config(value=0)

        self.root.after(0, update)

    def _on_play_message(self, title, text):
        self.root.after(0, lambda: messagebox.showinfo(title or APP_TITLE, text))

    def emergency_stop(self):
        if self.recorder.is_recording:
            self.current_events = self.recorder.stop()
            self.record_button.config(text=f"{ICON_RECORD} Grabar (F9)")
            self._refresh_tree()
        if self.player.is_playing:
            self.player.stop()
            self.play_button.config(text=f"{ICON_PLAY} Reproducir (F10)")
        self.progress.config(value=0)
        self.status_var.set("Parada de emergencia.")

    # ---------- Panel de acciones ----------
    def _refresh_tree(self, select_index=None):
        self.tree.delete(*self.tree.get_children())
        for index, event in enumerate(self.current_events):
            tag = "evenrow" if index % 2 else "oddrow"
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
                tags=(tag,),
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

    def _on_tree_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        try:
            index = int(row_id)
        except ValueError:
            return
        if not 0 <= index < len(self.current_events):
            return
        action_event = self.current_events[index]
        if action_event.get("type") != "click":
            return
        self._show_click_position_marker(
            action_event.get("x", 0), action_event.get("y", 0)
        )

    def _show_click_position_marker(self, x, y, duration_ms=2000):
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        transparent_key = "magenta"
        overlay.configure(bg=transparent_key)
        try:
            overlay.attributes("-transparentcolor", transparent_key)
        except tk.TclError:
            overlay.attributes("-alpha", 0.6)
        screen_w = overlay.winfo_screenwidth()
        screen_h = overlay.winfo_screenheight()
        overlay.geometry(f"{screen_w}x{screen_h}+0+0")

        canvas = tk.Canvas(overlay, bg=transparent_key, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        half = 14
        canvas.create_line(x - half, y, x + half, y, fill="red", width=3)
        canvas.create_line(x, y - half, x, y + half, fill="red", width=3)

        overlay.after(duration_ms, overlay.destroy)

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
        self._all_macro_names = storage.list_macros()
        self._apply_macro_filter()

    def _apply_macro_filter(self):
        query = self.macro_filter_var.get().strip().lower()
        self.listbox.delete(0, tk.END)
        for name in self._all_macro_names:
            if not query or query in name.lower():
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
