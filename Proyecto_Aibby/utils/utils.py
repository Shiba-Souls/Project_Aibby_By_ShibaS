"""Funciones auxiliares de Aibby."""
import re
import ctypes
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import winreg
from config import FILE_ATTRIBUTE_HIDDEN, FILE_ATTRIBUTE_SYSTEM, CARPETAS_IGNORADAS


def extraer_segundos_retry(mensaje_error: str) -> float:
    """Extrae los segundos de retry del mensaje de error de la API."""
    match = re.search(r"Please retry in\s+([\d.]+)s", mensaje_error, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 60.0  # Por defecto, 60 segundos


def leer_carpeta_registro(nombre_valor: str, fallback: str) -> str:
    """Lee la ruta real de una carpeta conocida de Windows desde el registro.
    
    Detecta automáticamente si OneDrive la redirigió (ej: Escritorio,
    Documentos, Descargas movidos dentro de OneDrive), sin importar el
    idioma del sistema.
    """
    try:
        clave = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        )
        valor, _ = winreg.QueryValueEx(clave, nombre_valor)
        winreg.CloseKey(clave)
        return os.path.expandvars(valor)
    except Exception:
        return fallback


def obtener_carpetas_usuario() -> list:
    """Devuelve las rutas reales de Escritorio, Documentos, Descargas,
    Imágenes y Videos, ya resueltas (contemplando redirección de OneDrive)."""
    home = os.path.expanduser("~")
    return [
        leer_carpeta_registro("Desktop", os.path.join(home, "Desktop")),
        leer_carpeta_registro("Personal", os.path.join(home, "Documents")),
        leer_carpeta_registro("{374DE290-123F-4565-9164-39C4925E467B}", os.path.join(home, "Downloads")),
        leer_carpeta_registro("My Pictures", os.path.join(home, "Pictures")),
        leer_carpeta_registro("My Video", os.path.join(home, "Videos")),
    ]


def obtener_unidades_disponibles() -> list:
    """Obtiene las unidades (drives) disponibles en el sistema."""
    from config import DRIVE_REMOVABLE, DRIVE_FIXED, TIPOS_UNIDAD_PERMITIDOS
    
    unidades = []
    try:
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i in range(26):
            if not (bitmask & (1 << i)):
                continue
            letra = f"{chr(65 + i)}:\\"
            tipo = ctypes.windll.kernel32.GetDriveTypeW(letra)
            if tipo in TIPOS_UNIDAD_PERMITIDOS:
                unidades.append(letra)
    except Exception:
        pass
    return unidades


def es_carpeta_ignorada(nombre_carpeta: str) -> bool:
    """Verifica si una carpeta debe ser ignorada en búsquedas."""
    return nombre_carpeta.lower() in CARPETAS_IGNORADAS or nombre_carpeta.startswith(".")


def es_archivo_oculto_o_sistema(ruta_completa: str) -> bool:
    """Verifica si un archivo está oculto o es de sistema."""
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(ruta_completa)
        if attrs == -1:
            return False
        return bool(attrs & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM))
    except Exception:
        return False


def es_429_rate_limit(mensaje_error: str) -> bool:
    """Verifica si el error es un rate limit (429)."""
    return "429" in mensaje_error and "RESOURCE_EXHAUSTED" in mensaje_error
