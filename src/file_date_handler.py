"""
AVI Conversor - Gestión de fechas de archivos.

Maneja la preservación de fechas del sistema de archivos (CreationTime,
LastWriteTime, LastAccessTime) de Windows al convertir videos.
"""

import os
import time
import datetime

import pywintypes
import win32file


def get_file_dates(filepath):
    """
    Lee las fechas del sistema de archivos de un archivo.

    Args:
        filepath: Ruta al archivo.

    Returns:
        dict con 'creation_time', 'last_access_time', 'last_write_time'
        como objetos pywintypes.Time, o None si falla.
    """
    try:
        handle = win32file.CreateFile(
            filepath,
            win32file.GENERIC_READ,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_ATTRIBUTE_NORMAL,
            None,
        )
        try:
            creation_time, last_access_time, last_write_time = (
                win32file.GetFileTime(handle)
            )
            return {
                "creation_time": creation_time,
                "last_access_time": last_access_time,
                "last_write_time": last_write_time,
            }
        finally:
            handle.Close()
    except Exception as e:
        print(f"Error leyendo fechas de '{filepath}': {e}")
        return None


def set_file_dates(filepath, dates, retries=5, delay=0.15):
    """
    Aplica las fechas del sistema de archivos a un archivo.
    Incluye reintentos por si el archivo recién cerrado está bloqueado
    temporalmente por el antivirus o el indexador de Windows.

    Args:
        filepath: Ruta al archivo destino.
        dates: dict con 'creation_time', 'last_access_time', 'last_write_time'
               (objetos pywintypes.Time).
        retries: número de intentos.
        delay: espera en segundos entre intentos.

    Returns:
        True si se aplicaron correctamente, False en caso contrario.
    """
    if dates is None:
        return False

    for attempt in range(retries):
        try:
            handle = win32file.CreateFile(
                filepath,
                win32file.GENERIC_WRITE,
                win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
                None,
                win32file.OPEN_EXISTING,
                win32file.FILE_ATTRIBUTE_NORMAL,
                None,
            )
            try:
                win32file.SetFileTime(
                    handle,
                    dates["creation_time"],
                    dates["last_access_time"],
                    dates["last_write_time"],
                )
                return True
            finally:
                handle.Close()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"Error aplicando fechas a '{filepath}': {e}")
                return False
    return False


def format_file_date(filepath):
    """
    Devuelve la fecha de modificación de un archivo formateada para mostrar en la UI.

    Args:
        filepath: Ruta al archivo.

    Returns:
        String con la fecha formateada (ej: '15/03/2024 14:30').
    """
    try:
        timestamp = os.path.getmtime(filepath)
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "Fecha desconocida"


def format_file_size(filepath):
    """
    Devuelve el tamaño de un archivo formateado para mostrar en la UI.

    Args:
        filepath: Ruta al archivo.

    Returns:
        String con el tamaño formateado (ej: '1.2 GB', '800 MB').
    """
    try:
        size_bytes = os.path.getsize(filepath)
        if size_bytes >= 1_073_741_824:  # 1 GB
            return f"{size_bytes / 1_073_741_824:.1f} GB"
        elif size_bytes >= 1_048_576:  # 1 MB
            return f"{size_bytes / 1_048_576:.1f} MB"
        elif size_bytes >= 1024:  # 1 KB
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes} B"
    except Exception:
        return "? MB"
