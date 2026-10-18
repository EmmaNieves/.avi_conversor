"""
AVI Conversor - Configuraciones y valores por defecto.
"""

import os

# --- Valores predeterminados de conversión ---

DEFAULT_VIDEO_CODEC = "libx264"       # H.264
DEFAULT_AUDIO_CODEC = "aac"
DEFAULT_RESOLUTION = "original"       # Mantener resolución original
DEFAULT_CRF = "23"                    # Balance calidad/tamaño
DEFAULT_PRESET = "veryfast"           # Rápido con buena calidad
DEFAULT_ROTATION = "none"             # Sin rotación

# --- Carpeta de destino ---
DEFAULT_OUTPUT_DIR = r"C:\Videos\Convertidos"

# --- Opciones disponibles para la UI ---

VIDEO_CODECS = {
    "H.264 (Recomendado)": "libx264",
    "H.265 (HEVC)": "libx265",
}

AUDIO_CODECS = {
    "AAC (Recomendado)": "aac",
    "MP3": "libmp3lame",
    "Copiar original": "copy",
}

RESOLUTIONS = {
    "Original": "original",
    "1920x1080 (1080p)": "1920:1080",
    "1280x720 (720p)": "1280:720",
    "854x480 (480p)": "854:480",
}

CRF_VALUES = [str(i) for i in range(18, 29)]  # 18 a 28

PRESETS = {
    "Ultrafast (más rápido)": "ultrafast",
    "Veryfast (Recomendado)": "veryfast",
    "Fast": "fast",
    "Medium (más calidad)": "medium",
    "Slow (máxima calidad, lento)": "slow",
}

ROTATIONS = {
    "Sin rotación (0°)": "none",
    "Rotar 90° (derecha)": "90",
    "Rotar 180°": "180",
    "Rotar 270° (izquierda)": "270",
}

# --- Mapeo de rotación a filtros FFmpeg ---

ROTATION_FILTERS = {
    "none": None,
    "90": "transpose=1",
    "180": "transpose=1,transpose=1",
    "270": "transpose=2",
}

# --- Configuración del ThreadPool ---
MAX_PARALLEL_CONVERSIONS = 2  # Número de conversiones simultáneas

# --- Vista previa ---
PREVIEW_FRAME_TIME = "00:00:01"  # Segundo 1 del video
PREVIEW_MAX_WIDTH = 400
PREVIEW_MAX_HEIGHT = 350


def ensure_output_dir(path=None):
    """Crea la carpeta de destino si no existe."""
    target = path or DEFAULT_OUTPUT_DIR
    os.makedirs(target, exist_ok=True)
    return target
