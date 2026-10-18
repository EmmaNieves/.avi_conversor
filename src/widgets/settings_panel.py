"""
AVI Conversor - Panel de opciones de conversión (Compacto).

Contiene los controles para códec, resolución, calidad y preset.
Diseño horizontal compacto para ahorrar espacio vertical en pantalla.
La rotación se maneja individualmente por archivo en la lista.
"""

import customtkinter as ctk

from src.settings import (
    VIDEO_CODECS,
    AUDIO_CODECS,
    RESOLUTIONS,
    CRF_VALUES,
    PRESETS,
)


class SettingsPanel(ctk.CTkFrame):
    """Panel compacto con opciones de conversión configurables."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Header con título y nota
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            header_frame,
            text="Opciones de Conversión",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            header_frame,
            text="(Valores predeterminados recomendados)",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(side="left", padx=8)

        # Contenedor en grid para las opciones
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="x", padx=10, pady=(2, 6))

        for col in range(6):
            grid_frame.columnconfigure(col, weight=1)

        # --- Fila 1: Códec Video | Códec Audio | Resolución ---
        ctk.CTkLabel(grid_frame, text="Códec video:", font=ctk.CTkFont(size=11)).grid(
            row=0, column=0, padx=(0, 4), pady=2, sticky="e"
        )
        self.video_codec_var = ctk.StringVar(value=list(VIDEO_CODECS.keys())[0])
        self.video_codec_menu = ctk.CTkOptionMenu(
            grid_frame,
            variable=self.video_codec_var,
            values=list(VIDEO_CODECS.keys()),
            width=150,
            height=26,
            font=ctk.CTkFont(size=11),
        )
        self.video_codec_menu.grid(row=0, column=1, padx=(0, 10), pady=2, sticky="w")

        ctk.CTkLabel(grid_frame, text="Códec audio:", font=ctk.CTkFont(size=11)).grid(
            row=0, column=2, padx=(0, 4), pady=2, sticky="e"
        )
        self.audio_codec_var = ctk.StringVar(value=list(AUDIO_CODECS.keys())[0])
        self.audio_codec_menu = ctk.CTkOptionMenu(
            grid_frame,
            variable=self.audio_codec_var,
            values=list(AUDIO_CODECS.keys()),
            width=150,
            height=26,
            font=ctk.CTkFont(size=11),
        )
        self.audio_codec_menu.grid(row=0, column=3, padx=(0, 10), pady=2, sticky="w")

        ctk.CTkLabel(grid_frame, text="Resolución:", font=ctk.CTkFont(size=11)).grid(
            row=0, column=4, padx=(0, 4), pady=2, sticky="e"
        )
        self.resolution_var = ctk.StringVar(value=list(RESOLUTIONS.keys())[0])
        self.resolution_menu = ctk.CTkOptionMenu(
            grid_frame,
            variable=self.resolution_var,
            values=list(RESOLUTIONS.keys()),
            width=140,
            height=26,
            font=ctk.CTkFont(size=11),
        )
        self.resolution_menu.grid(row=0, column=5, padx=0, pady=2, sticky="w")

        # --- Fila 2: Preset | Calidad CRF | Tip ---
        ctk.CTkLabel(grid_frame, text="Velocidad:", font=ctk.CTkFont(size=11)).grid(
            row=1, column=0, padx=(0, 4), pady=2, sticky="e"
        )
        veryfast_key = [k for k in PRESETS.keys() if "Veryfast" in k][0]
        self.preset_var = ctk.StringVar(value=veryfast_key)
        self.preset_menu = ctk.CTkOptionMenu(
            grid_frame,
            variable=self.preset_var,
            values=list(PRESETS.keys()),
            width=150,
            height=26,
            font=ctk.CTkFont(size=11),
        )
        self.preset_menu.grid(row=1, column=1, padx=(0, 10), pady=2, sticky="w")

        ctk.CTkLabel(grid_frame, text="Calidad (CRF):", font=ctk.CTkFont(size=11)).grid(
            row=1, column=2, padx=(0, 4), pady=2, sticky="e"
        )
        self.crf_var = ctk.StringVar(value="23")
        self.crf_menu = ctk.CTkOptionMenu(
            grid_frame,
            variable=self.crf_var,
            values=CRF_VALUES,
            width=80,
            height=26,
            font=ctk.CTkFont(size=11),
        )
        self.crf_menu.grid(row=1, column=3, padx=(0, 10), pady=2, sticky="w")

        ctk.CTkLabel(
            grid_frame,
            text="⚡ 'Veryfast': rápido y balanceado",
            font=ctk.CTkFont(size=10),
            text_color="#999999",
        ).grid(row=1, column=4, columnspan=2, padx=0, pady=2, sticky="w")

    def get_options(self):
        """Retorna un dict con las opciones de conversión seleccionadas."""
        return {
            "video_codec": VIDEO_CODECS[self.video_codec_var.get()],
            "audio_codec": AUDIO_CODECS[self.audio_codec_var.get()],
            "resolution": RESOLUTIONS[self.resolution_var.get()],
            "crf": self.crf_var.get(),
            "preset": PRESETS[self.preset_var.get()],
        }
