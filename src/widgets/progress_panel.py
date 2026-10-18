"""
AVI Conversor - Panel de progreso (Compacto).

Muestra barra de progreso general, porcentaje, contador y estado actual.
Diseñado para ocupar poco espacio vertical fijo.
"""

import customtkinter as ctk


class ProgressPanel(ctk.CTkFrame):
    """Panel compacto que muestra el progreso general de la conversión."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Fila 1: Título a la izquierda, conteo a la derecha
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            top_row,
            text="Progreso General",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        self.count_label = ctk.CTkLabel(
            top_row,
            text="0/0 completados",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.count_label.pack(side="right")

        # Fila 2: Barra de progreso + Porcentaje
        bar_frame = ctk.CTkFrame(self, fg_color="transparent")
        bar_frame.pack(fill="x", padx=10, pady=(0, 2))

        self.progress_bar = ctk.CTkProgressBar(bar_frame, height=16)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.progress_bar.set(0)

        self.percentage_label = ctk.CTkLabel(
            bar_frame,
            text="0%",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=45,
        )
        self.percentage_label.pack(side="right")

        # Fila 3: Texto de estado actual (una sola línea limpia)
        self.status_label = ctk.CTkLabel(
            self,
            text="Listo para convertir",
            font=ctk.CTkFont(size=11),
            text_color="#aaaaaa",
            anchor="w",
            height=16,
        )
        self.status_label.pack(fill="x", padx=10, pady=(0, 6))

    def update_progress(self, value, completed=0, total=0, status_text=None):
        """Actualiza el progreso general."""
        self.progress_bar.set(value)
        self.percentage_label.configure(text=f"{value * 100:.0f}%")

        if total > 0:
            self.count_label.configure(text=f"{completed}/{total} completados")

        if status_text:
            # Limitar longitud para que no desborde
            display_text = status_text if len(status_text) <= 80 else status_text[:77] + "..."
            self.status_label.configure(text=display_text)

    def reset(self):
        """Resetea el panel de progreso."""
        self.progress_bar.set(0)
        self.percentage_label.configure(text="0%")
        self.count_label.configure(text="0/0 completados")
        self.status_label.configure(text="Listo para convertir")

    def set_complete(self, total):
        """Marca la conversión como completada."""
        self.progress_bar.set(1.0)
        self.percentage_label.configure(text="100%")
        self.count_label.configure(text=f"{total}/{total} completados")
        self.status_label.configure(text="✅ ¡Conversión completada con éxito!")
