"""
AVI Conversor - Widget de lista de archivos.

Cada archivo tiene su propio selector de rotación y botón de vista previa.
Los widgets se crean una vez y solo se actualiza el texto al cambiar estado.
"""

import os
import threading
import customtkinter as ctk
from tkinter import Toplevel
from PIL import Image, ImageTk

from src.file_date_handler import format_file_date, format_file_size
from src.converter import extract_preview_frame
from src.settings import ROTATIONS


class FileListWidget(ctk.CTkFrame):
    """Widget que muestra una lista de archivos con rotación individual y vista previa."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.files = []  # Lista de dicts: {'path', 'status', 'progress', 'rotation'}
        self._row_frames = []  # Frames de cada fila
        self._status_labels = {}  # {filepath: CTkLabel} para actualizar sin reconstruir
        self._icon_labels = {}   # {filepath: CTkLabel}

        # --- Header ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            header_frame,
            text="Archivos seleccionados",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self.count_label = ctk.CTkLabel(
            header_frame,
            text="(0 archivos)",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.count_label.pack(side="right")

        # --- Scrollable frame para la lista ---
        self.scrollable_frame = ctk.CTkScrollableFrame(self, height=200)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Placeholder cuando no hay archivos
        self.placeholder_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="Usa el botón 'Agregar archivos' para seleccionar videos .avi",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        )
        self.placeholder_label.pack(pady=40)

    def add_files(self, file_paths):
        """Añade archivos a la lista."""
        for path in file_paths:
            if any(f["path"] == path for f in self.files):
                continue
            if not path.lower().endswith(".avi"):
                continue

            self.files.append({
                "path": path,
                "status": "En cola",
                "progress": 0.0,
                "rotation": "none",
                "rotation_label": list(ROTATIONS.keys())[0],
            })

        self._rebuild_list()

    def remove_selected(self):
        """Elimina el último archivo de la lista."""
        if self.files:
            removed = self.files.pop()
            self._status_labels.pop(removed["path"], None)
            self._icon_labels.pop(removed["path"], None)
            self._rebuild_list()

    def clear_all(self):
        """Elimina todos los archivos de la lista."""
        self.files.clear()
        self._status_labels.clear()
        self._icon_labels.clear()
        self._rebuild_list()

    def get_pending_files(self):
        """Retorna las rutas de archivos que aún no se han convertido."""
        return [f["path"] for f in self.files if f["status"] == "En cola"]

    def get_all_files(self):
        """Retorna todas las rutas de archivos en la lista."""
        return [f["path"] for f in self.files]

    def get_file_rotation(self, filepath):
        """Retorna la rotación configurada para un archivo específico."""
        for f in self.files:
            if f["path"] == filepath:
                return f["rotation"]
        return "none"

    def update_file_status(self, filepath, status, progress=None):
        """
        Actualiza SOLO el texto del estado y el icono de un archivo.
        NO reconstruye la lista entera — solo modifica los labels existentes.
        """
        for f in self.files:
            if f["path"] == filepath:
                f["status"] = status
                if progress is not None:
                    f["progress"] = progress
                break

        # Actualizar solo el label de estado (sin reconstruir)
        status_label = self._status_labels.get(filepath)
        if status_label and status_label.winfo_exists():
            status_color = "gray"
            if "✅" in status or "Completado" in status:
                status_color = "#2ecc71"
            elif "Error" in status or "❌" in status:
                status_color = "#e74c3c"
            elif "⏳" in status:
                status_color = "#f39c12"

            status_label.configure(text=status, text_color=status_color)

        # Actualizar icono
        icon_label = self._icon_labels.get(filepath)
        if icon_label and icon_label.winfo_exists():
            icon = "📄"
            if "✅" in status or "Completado" in status:
                icon = "✅"
            elif "Error" in status or "❌" in status:
                icon = "❌"
            elif "⏳" in status or "Convirtiendo" in status:
                icon = "⏳"
            icon_label.configure(text=icon)

    def reset_all_statuses(self):
        """Resetea el estado de todos los archivos a 'En cola'."""
        for f in self.files:
            f["status"] = "En cola"
            f["progress"] = 0.0
        # Actualizar labels existentes
        for filepath in self._status_labels:
            self.update_file_status(filepath, "En cola", 0.0)

    def _on_rotation_changed(self, file_index, choice):
        """Callback cuando cambia la rotación de un archivo."""
        if file_index < len(self.files):
            self.files[file_index]["rotation"] = ROTATIONS[choice]
            self.files[file_index]["rotation_label"] = choice

    def _on_preview_click(self, filepath):
        """Abre una ventana de vista previa para el archivo."""
        def _extract_and_show():
            preview_path = extract_preview_frame(filepath)
            if preview_path:
                self.after(0, self._show_preview_window, filepath, preview_path)
            else:
                self.after(0, self._show_preview_error, filepath)

        thread = threading.Thread(target=_extract_and_show, daemon=True)
        thread.start()

    def _show_preview_window(self, filepath, image_path):
        """Muestra la ventana de vista previa con la imagen extraída."""
        filename = os.path.basename(filepath)

        preview_win = Toplevel(self.winfo_toplevel())
        preview_win.title(f"Vista previa — {filename}")
        preview_win.resizable(False, False)

        try:
            img = Image.open(image_path)
            w, h = img.size

            # Redimensionar si es muy grande
            max_w, max_h = 450, 400
            if w > max_w or h > max_h:
                ratio = min(max_w / w, max_h / h)
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                img = img.resize((new_w, new_h), Image.LANCZOS)
                w, h = new_w, new_h

            # Determinar orientación
            if h > w:
                orientation = "📱 VERTICAL"
                orient_color = "#e74c3c"
            elif w > h:
                orientation = "🖥️ HORIZONTAL"
                orient_color = "#27ae60"
            else:
                orientation = "⬜ CUADRADO"
                orient_color = "#f39c12"

            preview_win.geometry(f"{w + 40}x{h + 100}")

            # Info del archivo
            info_frame = ctk.CTkFrame(preview_win)
            info_frame.pack(fill="x", padx=10, pady=(10, 5))

            ctk.CTkLabel(
                info_frame,
                text=filename,
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left", padx=10, pady=5)

            ctk.CTkLabel(
                info_frame,
                text=orientation,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=orient_color,
            ).pack(side="right", padx=10, pady=5)

            # Imagen
            photo = ImageTk.PhotoImage(img)
            img_label = ctk.CTkLabel(preview_win, text="", image=photo)
            img_label.image = photo  # Mantener referencia
            img_label.pack(padx=10, pady=5)

            # Info extra
            ctk.CTkLabel(
                preview_win,
                text=f"{format_file_size(filepath)}  |  {format_file_date(filepath)}",
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(pady=(0, 10))

            # Centrar ventana
            preview_win.update_idletasks()
            screen_w = preview_win.winfo_screenwidth()
            screen_h = preview_win.winfo_screenheight()
            x = (screen_w - preview_win.winfo_width()) // 2
            y = (screen_h - preview_win.winfo_height()) // 2
            preview_win.geometry(f"+{x}+{y}")

        except Exception as e:
            ctk.CTkLabel(
                preview_win,
                text=f"Error cargando imagen: {e}",
                text_color="red",
            ).pack(padx=20, pady=20)

        try:
            os.remove(image_path)
        except Exception:
            pass

    def _show_preview_error(self, filepath):
        """Muestra un mensaje de error si no se pudo generar la vista previa."""
        filename = os.path.basename(filepath)
        error_win = Toplevel(self.winfo_toplevel())
        error_win.title("Error de vista previa")
        error_win.geometry("350x120")
        error_win.resizable(False, False)

        ctk.CTkLabel(
            error_win,
            text=f"❌ No se pudo generar la vista previa\nde {filename}",
            font=ctk.CTkFont(size=13),
        ).pack(padx=20, pady=20)

        ctk.CTkButton(
            error_win,
            text="Cerrar",
            command=error_win.destroy,
            width=100,
        ).pack(pady=(0, 10))

    def _rebuild_list(self):
        """
        Reconstruye la lista SOLO cuando se agregan/quitan archivos.
        NO se llama durante actualizaciones de progreso.
        """
        # Limpiar frames existentes
        for frame in self._row_frames:
            frame.destroy()
        self._row_frames.clear()
        self._status_labels.clear()
        self._icon_labels.clear()

        if not self.files:
            self.placeholder_label.pack(pady=40)
            self.count_label.configure(text="(0 archivos)")
            return
        else:
            self.placeholder_label.pack_forget()

        self.count_label.configure(text=f"({len(self.files)} archivos)")

        for idx, file_info in enumerate(self.files):
            row = self._create_file_row(idx, file_info)
            row.pack(fill="x", padx=2, pady=2)
            self._row_frames.append(row)

    def _create_file_row(self, index, file_info):
        """Crea un frame de fila para un archivo con toda su info."""
        path = file_info["path"]
        status = file_info["status"]

        row_frame = ctk.CTkFrame(self.scrollable_frame, height=40)

        # --- Icono ---
        icon = "📄"
        if "✅" in status or "Completado" in status:
            icon = "✅"
        elif "Error" in status or "❌" in status:
            icon = "❌"
        elif "⏳" in status:
            icon = "⏳"

        icon_label = ctk.CTkLabel(
            row_frame, text=icon, font=ctk.CTkFont(size=14), width=25
        )
        icon_label.pack(side="left", padx=(8, 2))
        self._icon_labels[path] = icon_label

        # --- Nombre del archivo ---
        ctk.CTkLabel(
            row_frame,
            text=os.path.basename(path),
            font=ctk.CTkFont(size=12),
            anchor="w",
            width=180,
        ).pack(side="left", padx=4)

        # --- Tamaño ---
        ctk.CTkLabel(
            row_frame,
            text=format_file_size(path),
            font=ctk.CTkFont(size=10),
            text_color="gray",
            width=60,
        ).pack(side="left", padx=4)

        # --- Fecha ---
        ctk.CTkLabel(
            row_frame,
            text=format_file_date(path),
            font=ctk.CTkFont(size=10),
            text_color="gray",
            width=100,
        ).pack(side="left", padx=4)

        # --- Estado (a la derecha) ---
        status_color = "gray"
        if "✅" in status or "Completado" in status:
            status_color = "#2ecc71"
        elif "Error" in status or "❌" in status:
            status_color = "#e74c3c"
        elif "⏳" in status:
            status_color = "#f39c12"

        status_label = ctk.CTkLabel(
            row_frame,
            text=status,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=status_color,
            width=80,
        )
        status_label.pack(side="right", padx=(4, 8))
        self._status_labels[path] = status_label

        # --- Rotación (dropdown individual) ---
        rotation_var = ctk.StringVar(value=file_info["rotation_label"])
        rotation_menu = ctk.CTkOptionMenu(
            row_frame,
            variable=rotation_var,
            values=list(ROTATIONS.keys()),
            width=155,
            height=26,
            font=ctk.CTkFont(size=10),
            command=lambda choice, idx=index: self._on_rotation_changed(idx, choice),
        )
        rotation_menu.pack(side="right", padx=4)

        # --- Botón Vista Previa ---
        preview_btn = ctk.CTkButton(
            row_frame,
            text="👁",
            width=32,
            height=26,
            font=ctk.CTkFont(size=14),
            command=lambda p=path: self._on_preview_click(p),
            fg_color="#3498db",
            hover_color="#2980b9",
        )
        preview_btn.pack(side="right", padx=2)

        return row_frame
