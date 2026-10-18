"""
AVI Conversor - Aplicación principal.

Ventana principal que integra todos los widgets y conecta
la interfaz con el motor de conversión.
Diseño con barra inferior fijada (docked) para que los botones de acción
y la barra de progreso estén siempre visibles y accesibles en cualquier pantalla.
"""

import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.converter import convert_single_file, terminate_active_processes
from src.settings import DEFAULT_OUTPUT_DIR, MAX_PARALLEL_CONVERSIONS, ensure_output_dir
from src.widgets.file_list import FileListWidget
from src.widgets.progress_panel import ProgressPanel
from src.widgets.settings_panel import SettingsPanel


class AVIConversorApp(ctk.CTk):
    """Ventana principal de AVI Conversor."""

    def __init__(self):
        super().__init__()

        # --- Configuración de la ventana ---
        self.title("🎬 AVI Conversor")
        self.geometry("860x650")
        self.minsize(780, 520)

        # Tema oscuro por defecto
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Estado de conversión
        self._is_converting = False
        self._cancel_event = threading.Event()
        self._output_dir = DEFAULT_OUTPUT_DIR
        self._executor = None

        # Protocolo de cierre limpio de la ventana
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # --- Construir UI ---
        self._build_ui()

    def _build_ui(self):
        """
        Construye la interfaz de usuario.
        La barra de progreso y los botones de acción se fijan en la parte inferior
        para que SIEMPRE sean visibles y nunca queden fuera de pantalla.
        """

        # =========================================================
        # 1. BARRA INFERIOR FIJA (Docked at bottom)
        # Se empaca primero con side="bottom" para garantizar su visibilidad permanente
        # =========================================================
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.pack(side="bottom", fill="x", padx=14, pady=(4, 10))

        # Panel de progreso compacto
        self.progress_panel = ProgressPanel(bottom_bar)
        self.progress_panel.pack(fill="x", pady=(0, 6))

        # Botones de acción principales
        action_frame = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        action_frame.pack(fill="x")

        self.convert_btn = ctk.CTkButton(
            action_frame,
            text="▶  Convertir Todo",
            command=self._on_convert,
            width=180,
            height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#219a52",
        )
        self.convert_btn.pack(side="left", padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            action_frame,
            text="⏹  Cancelar",
            command=self._on_cancel,
            width=120,
            height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#e74c3c",
            hover_color="#c0392b",
            state="disabled",
        )
        self.cancel_btn.pack(side="left")

        # =========================================================
        # 2. ENCABEZADO SUPERIOR FIJO (Docked at top)
        # =========================================================
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(side="top", fill="x", padx=14, pady=(8, 2))

        ctk.CTkLabel(
            top_frame,
            text="🎬 AVI Conversor",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            top_frame,
            text="Conversión rápida de AVI a MP4 con preservación de fechas",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(side="left", padx=12, pady=(3, 0))

        # =========================================================
        # 3. ZONA CENTRAL DINÁMICA (Toma todo el espacio restante)
        # =========================================================
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(side="top", fill="both", expand=True, padx=14, pady=2)

        # Botones de gestión de archivos
        buttons_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 4))

        self.add_btn = ctk.CTkButton(
            buttons_frame,
            text="+ Agregar archivos",
            command=self._on_add_files,
            width=140,
            height=28,
            font=ctk.CTkFont(size=12),
        )
        self.add_btn.pack(side="left", padx=(0, 8))

        self.remove_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑 Quitar último",
            command=self._on_remove_file,
            width=110,
            height=28,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=ctk.CTkFont(size=12),
        )
        self.remove_btn.pack(side="left", padx=(0, 8))

        self.clear_btn = ctk.CTkButton(
            buttons_frame,
            text="Limpiar todo",
            command=self._on_clear_all,
            width=100,
            height=28,
            fg_color="#555555",
            hover_color="#444444",
            font=ctk.CTkFont(size=12),
        )
        self.clear_btn.pack(side="left")

        ctk.CTkLabel(
            buttons_frame,
            text="💡 👁 = Vista previa de orientación  |  🔄 = Rotación por video",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
        ).pack(side="right", padx=5)

        # Lista de archivos (se expande para llenar todo el alto dinámico)
        self.file_list = FileListWidget(center_frame)
        self.file_list.pack(fill="both", expand=True, pady=(0, 6))

        # Opciones de conversión compactas
        self.settings_panel = SettingsPanel(center_frame)
        self.settings_panel.pack(fill="x", pady=(0, 6))

        # Carpeta de destino en una sola fila compacta
        dest_frame = ctk.CTkFrame(center_frame)
        dest_frame.pack(fill="x", pady=(0, 2))

        dest_inner = ctk.CTkFrame(dest_frame, fg_color="transparent")
        dest_inner.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            dest_inner,
            text="📁 Destino:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self.dest_label = ctk.CTkLabel(
            dest_inner,
            text=self._output_dir,
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.dest_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            dest_inner,
            text="Cambiar...",
            command=self._on_change_output_dir,
            width=85,
            height=26,
            font=ctk.CTkFont(size=11),
        ).pack(side="right")

    # ===================== HANDLERS =====================

    def _on_add_files(self):
        """Abre el diálogo de selección de archivos."""
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos AVI",
            filetypes=[("Archivos AVI", "*.avi"), ("Todos los archivos", "*.*")],
        )
        if files:
            self.file_list.add_files(files)

    def _on_remove_file(self):
        """Elimina el último archivo de la lista."""
        self.file_list.remove_selected()

    def _on_clear_all(self):
        """Limpia toda la lista de archivos."""
        if self.file_list.files:
            if messagebox.askyesno("Confirmar", "¿Quieres quitar todos los archivos de la lista?"):
                self.file_list.clear_all()
                self.progress_panel.reset()

    def _on_change_output_dir(self):
        """Abre el diálogo para seleccionar la carpeta de destino."""
        directory = filedialog.askdirectory(
            title="Seleccionar carpeta de destino",
            initialdir=self._output_dir,
        )
        if directory:
            self._output_dir = directory
            self.dest_label.configure(text=self._output_dir)

    def _on_convert(self):
        """Inicia la conversión de todos los archivos."""
        files = self.file_list.get_all_files()

        if not files:
            messagebox.showwarning("Sin archivos", "Agrega al menos un archivo .avi para convertir.")
            return

        # Preparar UI
        self._is_converting = True
        self._cancel_event.clear()
        self.convert_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.add_btn.configure(state="disabled")
        self.remove_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")

        # Resetear estados de la lista sin parpadeos
        self.file_list.reset_all_statuses()
        self.progress_panel.reset()

        ensure_output_dir(self._output_dir)

        # Opciones globales seleccionadas
        options = self.settings_panel.get_options()

        # Iniciar conversión en un hilo en segundo plano
        thread = threading.Thread(
            target=self._convert_batch,
            args=(files, options),
            daemon=True,
        )
        thread.start()

    def _on_cancel(self):
        """Cancela inmediatamente la conversión en curso."""
        if self._is_converting:
            self._cancel_event.set()
            terminate_active_processes()
            self.progress_panel.update_progress(
                self.progress_panel.progress_bar.get(),
                status_text="⏹ Cancelando conversiones...",
            )

    def _on_window_close(self):
        """Maneja el evento de cerrar la ventana (X) limpiamente."""
        if self._is_converting:
            confirm = messagebox.askyesno(
                "Conversión en curso",
                "Hay videos convirtiéndose actualmente.\n¿Estás seguro de que deseas cancelar y salir?",
            )
            if not confirm:
                return

            self._cancel_event.set()
            terminate_active_processes()

        try:
            self.destroy()
        except Exception:
            pass

        # Forzar terminación limpia de cualquier subproceso residual
        os._exit(0)

    def _convert_batch(self, files, options):
        """
        Ejecuta la conversión de múltiples archivos en paralelo.
        Se ejecuta en un hilo separado.
        """
        total = len(files)
        completed = 0
        errors = 0
        error_messages = []

        # Almacenar progreso porcentual de cada archivo para calcular el progreso general
        file_progress_map = {fp: 0.0 for fp in files}

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_CONVERSIONS) as executor:
            self._executor = executor
            futures = {}

            for filepath in files:
                if self._cancel_event.is_set():
                    break

                self._safe_ui_call(
                    self.file_list.update_file_status, filepath, "⏳ Convirtiendo...", 0.0
                )

                file_rotation = self.file_list.get_file_rotation(filepath)
                file_options = {**options, "rotation": file_rotation}

                def make_progress_callback(fp):
                    def callback(prog, message):
                        file_progress_map[fp] = prog
                        self._safe_ui_call(
                            self._update_single_progress,
                            fp, prog, message, completed, total, file_progress_map
                        )
                    return callback

                future = executor.submit(
                    convert_single_file,
                    filepath,
                    self._output_dir,
                    file_options,
                    progress_callback=make_progress_callback(filepath),
                    cancel_event=self._cancel_event,
                )
                futures[future] = filepath

            for future in as_completed(futures):
                filepath = futures[future]
                filename = os.path.basename(filepath)
                try:
                    result = future.result()
                    if result.get("success"):
                        completed += 1
                        file_progress_map[filepath] = 100.0
                        self._safe_ui_call(
                            self.file_list.update_file_status, filepath, "✅ Completado", 100.0
                        )
                    else:
                        errors += 1
                        err_msg = result.get("error", "Error desconocido")
                        error_messages.append(f"• {filename}: {err_msg}")
                        file_progress_map[filepath] = 0.0
                        err_text = "❌ Cancelado" if self._cancel_event.is_set() else "❌ Error"
                        self._safe_ui_call(
                            self.file_list.update_file_status, filepath, err_text, 0.0
                        )
                except Exception as e:
                    errors += 1
                    error_messages.append(f"• {filename}: {e}")
                    file_progress_map[filepath] = 0.0
                    self._safe_ui_call(
                        self.file_list.update_file_status, filepath, "❌ Error", 0.0
                    )

                if self._cancel_event.is_set():
                    break

                # Actualizar barra general al terminar cada archivo
                overall = (completed + errors) / total if total > 0 else 0.0
                self._safe_ui_call(
                    self.progress_panel.update_progress,
                    overall, completed, total,
                    f"Completados: {completed}/{total} (Errores: {errors})"
                )

        # Conversión terminada
        self._safe_ui_call(self._conversion_finished, completed, errors, total, error_messages)

    def _safe_ui_call(self, func, *args):
        """Ejecuta una función en el hilo principal de Tkinter solo si la ventana aún existe."""
        try:
            if self.winfo_exists():
                self.after(0, func, *args)
        except Exception:
            pass

    def _update_single_progress(self, filepath, progress, message, completed, total, progress_map):
        """Actualiza el estado del archivo individual y el progreso general ponderado."""
        if not self.winfo_exists() or not self._is_converting:
            return

        # Actualiza el label del archivo en la lista (solo texto, sin reconstruir nada)
        self.file_list.update_file_status(filepath, f"⏳ {progress:.0f}%", progress)

        # Progreso general = promedio de los progresos de todos los archivos
        if total > 0:
            sum_prog = sum(progress_map.values())
            overall = sum_prog / (total * 100.0)
            self.progress_panel.update_progress(
                min(overall, 0.99),
                completed, total,
                message,
            )

    def _conversion_finished(self, completed, errors, total, error_messages=None):
        """Se ejecuta cuando termina todo el lote de conversiones."""
        self._is_converting = False

        # Restaurar controles
        self.convert_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.add_btn.configure(state="normal")
        self.remove_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")

        if self._cancel_event.is_set():
            self.progress_panel.update_progress(
                self.progress_panel.progress_bar.get(),
                completed, total,
                "⏹ Conversión cancelada",
            )
            messagebox.showinfo(
                "Cancelado",
                f"Conversión cancelada.\n{completed} archivos completados antes de cancelar.",
            )
        elif errors > 0:
            self.progress_panel.update_progress(
                1.0, completed, total, f"⚠️ Finalizado con {errors} errores"
            )
            err_detail = ""
            if error_messages:
                err_detail = "\n\nDetalles:\n" + "\n".join(error_messages[:4])
            messagebox.showwarning(
                "Completado con advertencias",
                f"Se convirtieron {completed} de {total} archivos.\n{errors} archivos tuvieron errores.{err_detail}",
            )
        else:
            self.progress_panel.set_complete(total)
            messagebox.showinfo(
                "¡Completado con éxito!",
                f"✅ Se convirtieron {completed} videos exitosamente.\n\n"
                f"Guardados en:\n{self._output_dir}",
            )
