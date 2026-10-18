"""
AVI Conversor - Motor de conversión AVI → MP4.

Usa FFmpeg (embebido via imageio-ffmpeg) para la conversión,
con soporte para opciones de calidad, rotación y preservación de metadatos.
Optimizado para máxima compatibilidad con Windows Media Player (yuv420p, audio estéreo 44.1kHz),
alto rendimiento y prevención absoluta de bloqueos/deadlocks.
"""

import collections
import os
import re
import subprocess
import tempfile
import threading
import time

import imageio_ffmpeg

from src.file_date_handler import get_file_dates, set_file_dates
from src.settings import ROTATION_FILTERS, DEFAULT_OUTPUT_DIR, PREVIEW_FRAME_TIME


# --- Registro de subprocesos activos para cancelación limpia ---
_active_processes = set()
_processes_lock = threading.Lock()


def register_process(proc):
    """Registra un proceso de FFmpeg en ejecución."""
    with _processes_lock:
        _active_processes.add(proc)


def unregister_process(proc):
    """Elimina un proceso del registro."""
    with _processes_lock:
        _active_processes.discard(proc)


def terminate_active_processes():
    """Termina de inmediato todos los procesos de FFmpeg activos."""
    with _processes_lock:
        for proc in list(_active_processes):
            try:
                proc.kill()
            except Exception:
                pass
        _active_processes.clear()


def get_ffmpeg_path():
    """Obtiene la ruta al binario de FFmpeg embebido."""
    return imageio_ffmpeg.get_ffmpeg_exe()


def get_video_duration(input_path):
    """
    Obtiene la duración del video en segundos usando ffmpeg.

    Args:
        input_path: Ruta al archivo de video.

    Returns:
        Duración en segundos (float), o None si no se puede obtener.
    """
    ffmpeg = get_ffmpeg_path()
    try:
        creationflags = subprocess.CREATE_NO_WINDOW
        if hasattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS"):
            creationflags |= subprocess.BELOW_NORMAL_PRIORITY_CLASS

        result = subprocess.run(
            [ffmpeg, "-i", input_path],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=creationflags,
        )
        output = result.stderr
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", output)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            centiseconds = int(match.group(4))
            return hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
    except Exception as e:
        print(f"Error obteniendo duración de '{input_path}': {e}")
    return None


def extract_preview_frame(input_path):
    """
    Extrae un frame del video como imagen para vista previa.
    Usa baja resolución para que sea instantáneo.

    Args:
        input_path: Ruta al archivo de video.

    Returns:
        Ruta al archivo de imagen temporal (PNG), o None si falla.
    """
    ffmpeg = get_ffmpeg_path()
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"avi_preview_{os.getpid()}_{int(time.time()*1000)}.png")

    try:
        creationflags = subprocess.CREATE_NO_WINDOW
        if hasattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS"):
            creationflags |= subprocess.BELOW_NORMAL_PRIORITY_CLASS

        cmd = [
            ffmpeg,
            "-ss", PREVIEW_FRAME_TIME,
            "-i", input_path,
            "-vframes", "1",
            "-vf", "scale=400:-1,format=yuv420p",
            "-q:v", "10",
            "-y",
            temp_path,
        ]

        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=creationflags,
        )

        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            return temp_path

    except Exception as e:
        print(f"Error extrayendo preview de '{input_path}': {e}")

    return None


def build_ffmpeg_command(input_path, output_path, options):
    """
    Construye el comando FFmpeg para la conversión.
    Garantiza 100% de compatibilidad con Windows Media Player y reproductores nativos.

    Args:
        input_path: Ruta al archivo .avi de entrada.
        output_path: Ruta al archivo .mp4 de salida.
        options: dict con las opciones de conversión.

    Returns:
        Lista con el comando FFmpeg y sus argumentos.
    """
    ffmpeg = get_ffmpeg_path()

    cmd = [
        ffmpeg,
        "-i", input_path,
        "-y",
    ]

    # Asignar un número equilibrado de hilos
    cpu_count = os.cpu_count() or 4
    threads_per_worker = max(2, cpu_count // 2)
    cmd.extend(["-threads", str(threads_per_worker)])

    # --- Filtros de video (rotación + resolución + formato de píxeles estándar) ---
    video_filters = []

    # Rotación individual si aplica
    rotation = options.get("rotation", "none")
    rotation_filter = ROTATION_FILTERS.get(rotation)
    if rotation_filter:
        video_filters.append(rotation_filter)

    # Resolución personalizada si se seleccionó
    resolution = options.get("resolution", "original")
    if resolution != "original":
        video_filters.append(f"scale={resolution}")

    # FUNDAMENTAL PARA WINDOWS MEDIA PLAYER:
    # Muchos videos .AVI de cámaras usan MJPEG con 4:2:2 (yuvj422p).
    # Windows Media Player NO admite H.264 en 4:2:2 (da error 0x80004005).
    # Forzar 'format=yuv420p' garantiza que el archivo sea estándar YUV 4:2:0.
    video_filters.append("format=yuv420p")
    cmd.extend(["-vf", ",".join(video_filters)])

    # --- Códec de video ---
    video_codec = options.get("video_codec", "libx264")
    cmd.extend(["-c:v", video_codec])
    cmd.extend(["-pix_fmt", "yuv420p"])

    # CRF y preset para x264/x265
    if video_codec in ("libx264", "libx265"):
        crf = options.get("crf", "23")
        cmd.extend(["-crf", str(crf)])

        preset = options.get("preset", "veryfast")
        cmd.extend(["-preset", preset])

    # --- Códec de audio compatible con Windows ---
    # Muchos .AVI usan audio PCM mono a 16000Hz.
    # Windows Media Player requiere estéreo a 44100Hz para decodificar AAC sin error.
    audio_codec = options.get("audio_codec", "aac")
    cmd.extend(["-c:a", audio_codec])

    if audio_codec == "aac":
        cmd.extend(["-b:a", "192k", "-ac", "2", "-ar", "44100"])
    elif audio_codec == "libmp3lame":
        cmd.extend(["-b:a", "192k", "-ac", "2", "-ar", "44100"])

    # --- Preservar metadatos ---
    cmd.extend(["-map_metadata", "0"])

    # --- Mover moov atom al inicio para reproducción inmediata en Windows ---
    cmd.extend(["-movflags", "+faststart"])

    # --- Progreso en pipe ---
    cmd.extend(["-progress", "pipe:1", "-nostats"])

    # --- Salida ---
    cmd.append(output_path)

    return cmd


def convert_single_file(input_path, output_dir, options, progress_callback=None,
                         cancel_event=None):
    """
    Convierte un solo archivo .avi a .mp4 de forma robusta sin deadlocks y con
    formato 100% compatible con reproductores de Windows.

    Args:
        input_path: Ruta al archivo .avi de entrada.
        output_dir: Carpeta donde guardar el .mp4.
        options: dict con opciones de conversión.
        progress_callback: función(porcentaje, mensaje) para reportar progreso.
        cancel_event: threading.Event para cancelar.

    Returns:
        dict con 'success', 'input', 'output', 'error'.
    """
    filename = os.path.basename(input_path)
    name_without_ext = os.path.splitext(filename)[0]
    output_path = os.path.join(output_dir, f"{name_without_ext}.mp4")

    os.makedirs(output_dir, exist_ok=True)

    result = {
        "success": False,
        "input": input_path,
        "output": output_path,
        "error": None,
    }

    process = None
    log_tail = collections.deque(maxlen=30)

    try:
        # 1. Leer fechas originales ANTES de convertir
        if progress_callback:
            progress_callback(0.0, f"Iniciando {filename}...")
        original_dates = get_file_dates(input_path)

        # 2. Obtener duración del video para calcular %
        duration = get_video_duration(input_path)

        # 3. Construir comando FFmpeg con máxima compatibilidad
        cmd = build_ffmpeg_command(input_path, output_path, options)

        if cancel_event and cancel_event.is_set():
            result["error"] = "Conversión cancelada"
            return result

        creationflags = subprocess.CREATE_NO_WINDOW
        if hasattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS"):
            creationflags |= subprocess.BELOW_NORMAL_PRIORITY_CLASS

        # Redirigir stderr a STDOUT para evitar deadlocks de buffer
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            creationflags=creationflags,
        )

        register_process(process)

        # 4. Leer progreso de FFmpeg de forma continua y con limitador de refresco
        last_update_time = 0.0
        last_pct = -1

        for raw_line in process.stdout:
            line = raw_line.strip()
            log_tail.append(line)

            if cancel_event and cancel_event.is_set():
                try:
                    process.kill()
                    process.wait(timeout=2)
                except Exception:
                    pass
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except Exception:
                        pass
                result["error"] = "Conversión cancelada por el usuario"
                return result

            # Parsear línea de tiempo
            if line.startswith("out_time_us="):
                try:
                    current_time_us = int(line.split("=")[1])
                    if duration and duration > 0:
                        calculated = (current_time_us / 1_000_000) / duration * 100
                        progress = min(max(calculated, 0.0), 99.0)
                        pct = int(progress)
                        now = time.time()
                        if (now - last_update_time >= 0.25) or (pct != last_pct):
                            last_update_time = now
                            last_pct = pct
                            if progress_callback:
                                progress_callback(
                                    progress, f"Convirtiendo {filename}... {pct}%"
                                )
                except (ValueError, ZeroDivisionError):
                    pass

            # Señal explícita de FFmpeg de que terminó de procesar fotogramas
            elif line == "progress=end":
                if progress_callback:
                    progress_callback(99.0, f"Finalizando {filename}...")

        # Esperar finalización del proceso
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        if cancel_event and cancel_event.is_set():
            result["error"] = "Conversión cancelada por el usuario"
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            return result

        if process.returncode != 0:
            error_details = "\n".join(list(log_tail)[-10:])
            result["error"] = f"FFmpeg error ({process.returncode}): {error_details[:300]}"
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            return result

        if not os.path.exists(output_path):
            result["error"] = "El archivo de salida no se creó"
            return result

        # 5. Restaurar fechas originales en el archivo de salida
        if original_dates:
            set_file_dates(output_path, original_dates)

        # 6. Éxito confirmado
        result["success"] = True
        if progress_callback:
            progress_callback(100.0, f"✅ {filename} completado")

    except Exception as e:
        result["error"] = str(e)
        if progress_callback:
            progress_callback(0.0, f"❌ Error en {filename}")
    finally:
        if process:
            unregister_process(process)

    return result
