"""Dialogo para agregar o editar manualmente una accion del panel de acciones."""

import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from pynput import keyboard

from . import actions, image_search
from .keys import SPECIAL_KEY_NAMES, display_to_key_str, key_to_display

IMAGE_FILETYPES = [
    ("Imagenes", "*.png *.bmp *.jpg *.jpeg *.gif"),
    ("Todos los archivos", "*.*"),
]


class ActionDialog(tk.Toplevel):
    """Ventana modal para crear/editar una accion. Deja el resultado en self.result."""

    def __init__(self, parent, event=None):
        super().__init__(parent)
        self.title("Editar accion" if event else "Agregar accion")
        self.resizable(False, False)
        self.transient(parent)

        self.result = None
        self._field_vars = {}
        self._key_listener = None
        self._capture_var = None

        initial_type = (event or {}).get("type", actions.ACTION_ORDER[0])

        top = ttk.Frame(self, padding=10)
        top.pack(fill="both", expand=True)

        ttk.Label(top, text="Tipo de accion:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.type_var = tk.StringVar(value=initial_type)
        self.type_combo = ttk.Combobox(
            top,
            textvariable=self.type_var,
            state="readonly",
            width=28,
            values=[actions.label_for(t) for t in actions.ACTION_ORDER],
        )
        self.type_combo.set(actions.label_for(initial_type))
        self.type_combo.grid(row=0, column=1, columnspan=2, sticky="w", pady=(0, 6))
        self.type_combo.bind("<<ComboboxSelected>>", lambda _e: self._rebuild_fields())

        self.fields_frame = ttk.Frame(top)
        self.fields_frame.grid(row=1, column=0, columnspan=3, sticky="we")

        self._label_to_type = {actions.label_for(t): t for t in actions.ACTION_ORDER}

        buttons = ttk.Frame(top)
        buttons.grid(row=2, column=0, columnspan=3, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Cancelar", command=self._on_cancel).pack(side="right")
        ttk.Button(buttons, text="Aceptar", command=self._on_accept).pack(
            side="right", padx=(0, 8)
        )

        self._rebuild_fields(event)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda _e: self._on_cancel())
        self.grab_set()
        self.wait_visibility()
        self.focus_set()

    # ---------- construccion dinamica de campos ----------
    def _current_type(self):
        label = self.type_combo.get()
        return self._label_to_type.get(label, actions.ACTION_ORDER[0])

    def _rebuild_fields(self, event=None):
        for child in self.fields_frame.winfo_children():
            child.destroy()
        self._field_vars = {}

        action_type = self._current_type()
        event = event if (event and event.get("type") == action_type) else None

        row = 0
        delay_label = (
            "Duracion de la pausa (s):"
            if action_type == "wait"
            else "Retraso antes de ejecutar (s):"
        )
        ttk.Label(self.fields_frame, text=delay_label).grid(
            row=row, column=0, sticky="w", pady=3
        )
        delay_default = (event or {}).get("delay", 1.0 if action_type == "wait" else 0.0)
        self.delay_var = tk.StringVar(value=str(delay_default))
        ttk.Entry(self.fields_frame, textvariable=self.delay_var, width=10).grid(
            row=row, column=1, sticky="w", pady=3
        )
        row += 1

        for name, label, kind, default, choices in actions.fields_for(action_type):
            value = (event or {}).get(name, default)
            ttk.Label(self.fields_frame, text=f"{label}:").grid(
                row=row, column=0, sticky="w", pady=3
            )
            self._build_field(row, name, kind, value, choices)
            row += 1

        self._build_extra_tools(row, action_type)

    def _build_field(self, row, name, kind, value, choices):
        frame = self.fields_frame
        if kind in ("int", "float", "text"):
            var = tk.StringVar(value=str(value))
            ttk.Entry(frame, textvariable=var, width=30).grid(
                row=row, column=1, columnspan=2, sticky="w", pady=3
            )
            self._field_vars[name] = (kind, var)
        elif kind == "textarea":
            text_widget = tk.Text(frame, width=34, height=4, wrap="word")
            text_widget.insert("1.0", str(value))
            text_widget.grid(row=row, column=1, columnspan=2, sticky="w", pady=3)
            self._field_vars[name] = (kind, text_widget)
        elif kind == "choice":
            var = tk.StringVar(value=value)
            combo = ttk.Combobox(
                frame, textvariable=var, state="readonly", width=15, values=choices
            )
            combo.grid(row=row, column=1, sticky="w", pady=3)
            self._field_vars[name] = (kind, var)
        elif kind == "bool":
            var = tk.BooleanVar(value=bool(value))
            ttk.Checkbutton(frame, variable=var).grid(row=row, column=1, sticky="w", pady=3)
            self._field_vars[name] = (kind, var)
        elif kind == "key":
            display = key_to_display_safe(value)
            var = tk.StringVar(value=display)
            combo = ttk.Combobox(
                frame, textvariable=var, width=18, values=SPECIAL_KEY_NAMES
            )
            combo.grid(row=row, column=1, sticky="w", pady=3)
            capture_btn = ttk.Button(
                frame,
                text="Capturar...",
                command=lambda v=var, b_row=row: self._capture_key(v),
            )
            capture_btn.grid(row=row, column=2, sticky="w", padx=(6, 0), pady=3)
            self._field_vars[name] = (kind, var)
        elif kind == "path":
            var = tk.StringVar(value=str(value))
            ttk.Entry(frame, textvariable=var, width=26).grid(
                row=row, column=1, sticky="w", pady=3
            )
            ttk.Button(
                frame, text="Elegir...", command=lambda v=var: self._choose_path(v)
            ).grid(row=row, column=2, sticky="w", padx=(6, 0), pady=3)
            self._field_vars[name] = (kind, var)
        elif kind == "image_path":
            var = tk.StringVar(value=str(value))
            ttk.Entry(frame, textvariable=var, width=26).grid(
                row=row, column=1, sticky="w", pady=3
            )
            ttk.Button(
                frame,
                text="Elegir...",
                command=lambda v=var: self._choose_path(
                    v, filetypes=IMAGE_FILETYPES, title="Elegir imagen de referencia"
                ),
            ).grid(row=row, column=2, sticky="w", padx=(6, 0), pady=3)
            self._field_vars[name] = (kind, var)
        elif kind == "save_path":
            var = tk.StringVar(value=str(value))
            ttk.Entry(frame, textvariable=var, width=26).grid(
                row=row, column=1, sticky="w", pady=3
            )
            ttk.Button(
                frame, text="Guardar como...", command=lambda v=var: self._choose_save_path(v)
            ).grid(row=row, column=2, sticky="w", padx=(6, 0), pady=3)
            self._field_vars[name] = (kind, var)

    def _build_extra_tools(self, row, action_type):
        frame = self.fields_frame
        if action_type in ("capture_image", "find_image", "find_ocr"):
            ttk.Button(
                frame,
                text="Seleccionar region en pantalla...",
                command=self._pick_region,
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(10, 3))
            row += 1
        if action_type == "capture_image":
            ttk.Button(
                frame, text="Capturar ahora", command=self._do_capture_now
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 3))
            row += 1
        elif action_type == "find_image":
            ttk.Button(
                frame,
                text="Capturar imagen de referencia...",
                command=self._do_capture_reference_image,
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 3))
            row += 1
            ttk.Button(
                frame, text="Probar busqueda", command=self._do_test_find
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 3))
            row += 1
        elif action_type == "find_ocr":
            ttk.Button(
                frame, text="Probar busqueda", command=self._do_test_find_ocr
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 3))
            row += 1
        if action_type == "click":
            ttk.Button(
                frame,
                text="Capturar posicion del mouse...",
                command=self._do_capture_click_position,
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(10, 3))
            row += 1
        return row

    def _collect_region(self):
        def _get(name):
            try:
                return int(float(self._field_vars[name][1].get()))
            except (KeyError, ValueError, TypeError):
                return 0

        return (_get("x"), _get("y"), _get("width"), _get("height"))

    def _pick_region(self):
        self.grab_release()
        self.withdraw()
        try:
            box = select_region_interactively(self)
        finally:
            self.deiconify()
            self.grab_set()
        if not box:
            return
        x, y, w, h = box
        for name, value in (("x", x), ("y", y), ("width", w), ("height", h)):
            if name in self._field_vars:
                self._field_vars[name][1].set(str(int(value)))

    def _do_capture_now(self):
        path = self._field_vars.get("save_path", (None, tk.StringVar()))[1].get().strip()
        if not path:
            messagebox.showerror(
                "Captura", "Primero indica donde guardar la captura.", parent=self
            )
            return
        region = self._collect_region()
        self.grab_release()
        self.withdraw()
        try:
            image_search.save_capture(path, region=region)
        except Exception as exc:  # noqa: BLE001 - se muestra el error al usuario
            self.deiconify()
            self.grab_set()
            messagebox.showerror("Captura", str(exc), parent=self)
            return
        self.deiconify()
        self.grab_set()
        messagebox.showinfo("Captura", f"Imagen guardada en:\n{path}", parent=self)

    def _do_capture_reference_image(self):
        self.grab_release()
        self.withdraw()
        try:
            box = select_region_interactively(self)
        finally:
            self.deiconify()
            self.grab_set()
        if not box:
            return
        x, y, w, h = box
        if not w or not h:
            messagebox.showerror(
                "Capturar imagen", "Selecciona un area valida.", parent=self
            )
            return

        images_dir = image_search.ensure_images_dir()
        default_name = f"referencia_{int(time.time())}.png"
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar imagen de referencia como",
            defaultextension=".png",
            initialdir=images_dir,
            initialfile=default_name,
            filetypes=IMAGE_FILETYPES,
        )
        if not path:
            return
        try:
            image_search.save_capture(path, region=(x, y, w, h))
        except Exception as exc:  # noqa: BLE001 - se muestra el error al usuario
            messagebox.showerror("Capturar imagen", str(exc), parent=self)
            return
        if "image_path" in self._field_vars:
            self._field_vars["image_path"][1].set(path)
        messagebox.showinfo(
            "Capturar imagen", f"Imagen de referencia guardada en:\n{path}", parent=self
        )

    def _do_capture_click_position(self):
        self.grab_release()
        self.withdraw()
        try:
            point = select_point_interactively(self)
        finally:
            self.deiconify()
            self.grab_set()
        if not point:
            return
        x, y = point
        for name, value in (("x", x), ("y", y)):
            if name in self._field_vars:
                self._field_vars[name][1].set(str(int(value)))

    def _do_test_find(self):
        path = self._field_vars.get("image_path", (None, tk.StringVar()))[1].get().strip()
        if not path:
            messagebox.showerror(
                "Buscar imagen", "Primero elige la imagen de referencia.", parent=self
            )
            return
        try:
            confidence = float(self._field_vars["confidence"][1].get())
        except (KeyError, ValueError):
            confidence = 0.8
        region = self._collect_region()
        self.grab_release()
        self.withdraw()
        try:
            location = image_search.locate_image(path, region=region, confidence=confidence)
        except Exception as exc:  # noqa: BLE001 - se muestra el error al usuario
            self.deiconify()
            self.grab_set()
            messagebox.showerror("Buscar imagen", str(exc), parent=self)
            return
        self.deiconify()
        self.grab_set()
        if location:
            messagebox.showinfo(
                "Buscar imagen", f"Imagen encontrada en {location}.", parent=self
            )
        else:
            messagebox.showinfo("Buscar imagen", "Imagen no encontrada en pantalla.", parent=self)

    def _do_test_find_ocr(self):
        text = self._field_vars.get("text", (None, tk.StringVar()))[1].get().strip()
        if not text:
            messagebox.showerror(
                "Buscar texto (OCR)", "Primero indica el texto a buscar.", parent=self
            )
            return
        lang = self._field_vars.get("lang", (None, tk.StringVar(value="eng")))[1].get().strip()
        case_sensitive = bool(
            self._field_vars.get("case_sensitive", (None, tk.BooleanVar(value=False)))[1].get()
        )
        region = self._collect_region()
        self.grab_release()
        self.withdraw()
        try:
            location = image_search.locate_text(
                text, region=region, lang=lang or "eng", case_sensitive=case_sensitive
            )
        except Exception as exc:  # noqa: BLE001 - se muestra el error al usuario
            self.deiconify()
            self.grab_set()
            messagebox.showerror("Buscar texto (OCR)", str(exc), parent=self)
            return
        self.deiconify()
        self.grab_set()
        if location:
            messagebox.showinfo(
                "Buscar texto (OCR)", f"Texto encontrado en {location}.", parent=self
            )
        else:
            messagebox.showinfo(
                "Buscar texto (OCR)", "Texto no encontrado en pantalla.", parent=self
            )

    def _choose_path(self, var, filetypes=None, title="Elegir programa o archivo"):
        kwargs = {"parent": self, "title": title}
        if filetypes:
            kwargs["filetypes"] = filetypes
        path = filedialog.askopenfilename(**kwargs)
        if path:
            var.set(path)

    def _choose_save_path(self, var):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar captura como",
            defaultextension=".png",
            filetypes=IMAGE_FILETYPES,
        )
        if path:
            var.set(path)

    def _capture_key(self, var):
        var.set("Presiona una tecla...")

        def on_press(key):
            try:
                display = key_to_display(key)
            except Exception:  # noqa: BLE001 - cualquier tecla rara se ignora
                return
            self.after(0, lambda: var.set(display))
            return False  # detiene el listener tras la primera tecla

        if self._key_listener is not None:
            self._key_listener.stop()
        self._key_listener = keyboard.Listener(on_press=on_press)
        self._key_listener.start()

    # ---------- aceptar / cancelar ----------
    def _collect_values(self):
        action_type = self._current_type()
        try:
            delay = float(self.delay_var.get())
            if delay < 0:
                raise ValueError
        except ValueError as exc:
            raise ValueError("El retraso/duracion debe ser un numero >= 0.") from exc

        event = {"type": action_type, "delay": delay}
        for name, label, kind, _default, _choices in actions.fields_for(action_type):
            kind_stored, widget_or_var = self._field_vars[name]
            if kind_stored == "textarea":
                raw = widget_or_var.get("1.0", "end-1c")
            elif kind_stored == "bool":
                raw = widget_or_var.get()
            else:
                raw = widget_or_var.get()

            if kind == "int":
                try:
                    event[name] = int(float(raw))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"'{label}' debe ser un numero entero.") from exc
            elif kind == "float":
                try:
                    event[name] = float(raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"'{label}' debe ser un numero.") from exc
            elif kind == "key":
                event[name] = display_to_key_str(raw)
            elif kind == "bool":
                event[name] = bool(raw)
            else:
                event[name] = raw
        return event

    def _on_accept(self):
        try:
            self.result = self._collect_values()
        except ValueError as exc:
            messagebox.showerror("Accion invalida", str(exc), parent=self)
            return
        self._cleanup()
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self._cleanup()
        self.destroy()

    def _cleanup(self):
        if self._key_listener is not None:
            self._key_listener.stop()
            self._key_listener = None


def key_to_display_safe(value):
    """Convierte un valor guardado de tecla al texto corto de la UI, sin romper
    si el valor viene vacio (caso de una accion nueva todavia sin tecla)."""
    if not value:
        return ""
    from .keys import key_str_to_display

    return key_str_to_display(value)


def select_region_interactively(parent):
    """Abre una ventana semitransparente de pantalla completa para que el
    usuario seleccione un area arrastrando el mouse.

    Devuelve (x, y, width, height) en coordenadas absolutas de pantalla, o
    None si se cancela (Esc o sin arrastrar)."""
    result = {}
    overlay = tk.Toplevel(parent)
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-alpha", 0.3)
    overlay.attributes("-topmost", True)
    overlay.configure(bg="gray20")
    overlay.config(cursor="cross")

    canvas = tk.Canvas(overlay, bg="gray20", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_text(
        10,
        10,
        anchor="nw",
        fill="white",
        font=("Segoe UI", 11),
        text="Arrastra para seleccionar el area. Esc para cancelar.",
    )

    start = {}
    rect_id = {"id": None}

    def on_press(event):
        start["x"], start["y"] = event.x, event.y
        if rect_id["id"] is not None:
            canvas.delete(rect_id["id"])
        rect_id["id"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red", width=2
        )

    def on_drag(event):
        if rect_id["id"] is None or "x" not in start:
            return
        canvas.coords(rect_id["id"], start["x"], start["y"], event.x, event.y)

    def on_release(event):
        if "x" not in start:
            overlay.destroy()
            return
        x0, y0 = start["x"], start["y"]
        x1, y1 = event.x, event.y
        result["box"] = (min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        overlay.destroy()

    def on_escape(_event):
        result["box"] = None
        overlay.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    overlay.bind("<Escape>", on_escape)
    overlay.grab_set()
    overlay.focus_force()
    overlay.wait_window()
    return result.get("box")


def select_point_interactively(parent):
    """Abre una ventana semitransparente de pantalla completa donde el
    usuario mueve el mouse hasta la posicion deseada; una cruz roja sigue
    al cursor para identificar donde se hara el clic. Al pulsar la barra
    espaciadora se captura esa posicion.

    Devuelve (x, y) en coordenadas absolutas de pantalla, o None si se
    cancela (Esc)."""
    result = {}
    overlay = tk.Toplevel(parent)
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-alpha", 0.3)
    overlay.attributes("-topmost", True)
    overlay.configure(bg="gray20")
    overlay.config(cursor="cross")

    canvas = tk.Canvas(overlay, bg="gray20", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_text(
        10,
        10,
        anchor="nw",
        fill="white",
        font=("Segoe UI", 11),
        text="Mueve el mouse a la posicion deseada y pulsa Espacio para capturar."
        " Esc para cancelar.",
    )

    cross = {"h": None, "v": None}
    half = 14

    def draw_cross(x, y):
        if cross["h"] is not None:
            canvas.delete(cross["h"])
        if cross["v"] is not None:
            canvas.delete(cross["v"])
        cross["h"] = canvas.create_line(x - half, y, x + half, y, fill="red", width=2)
        cross["v"] = canvas.create_line(x, y - half, x, y + half, fill="red", width=2)

    def on_motion(event):
        draw_cross(event.x, event.y)

    def on_space(_event):
        result["point"] = (overlay.winfo_pointerx(), overlay.winfo_pointery())
        overlay.destroy()

    def on_escape(_event):
        result["point"] = None
        overlay.destroy()

    canvas.bind("<Motion>", on_motion)
    overlay.bind("<space>", on_space)
    overlay.bind("<Escape>", on_escape)
    overlay.grab_set()
    overlay.focus_force()
    overlay.wait_window()
    return result.get("point")


def ask_action(parent, event=None):
    """Abre el dialogo y devuelve el evento resultante, o None si se cancela."""
    dialog = ActionDialog(parent, event)
    parent.wait_window(dialog)
    return dialog.result
