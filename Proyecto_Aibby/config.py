"""Configuración centralizada de Aibby."""
import os
from dotenv import load_dotenv

# --- Cargar variables de entorno ---
load_dotenv(".env")

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError(
        "No se encontró API_KEY. Revisá que exista un archivo .env "
        "en la misma carpeta que este script, con la línea API_KEY=tu_clave"
    )

# --- Modelos de Gemini ---
MODELO_PRINCIPAL = "gemini-3.5-flash"
MODELO_LIGERO = "gemini-3.1-flash-lite"

# --- Instrucción del sistema ---
SYSTEM_INSTRUCTION = "Eres Aibby, una asistente personal de IA. Respondés de forma concisa y útil."

# --- Audio ---
SAMPLE_RATE = 16000
AUDIO_TEMP_FILE = "temp_audio.wav"

# --- Búsqueda de archivos ---
PALABRAS_BUSQUEDA = ["busca", "buscá", "encontr", "dónde está", "donde esta"]

CARPETAS_IGNORADAS = {
    "windows", "program files", "program files (x86)", "programdata",
    "$recycle.bin", "system volume information", "appdata",
    "windowsapps", "msocache", "recovery", "perflogs",
    "node_modules", "__pycache__", "venv", "$sysreset"
}

EXTENSIONES_RELEVANTES = {
    ".docx", ".doc", ".pdf", ".txt", ".xlsx", ".xls", ".pptx", ".ppt", ".odt", ".csv",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".flac",
    ".exe", ".lnk",
    ".zip", ".rar", ".7z",
}

# --- Límites de búsqueda ---
LIMITE_ARCHIVOS_BUSQUEDA = 2000
LIMITE_ARCHIVOS_MOSTRAR = 30

# --- Tipos de unidad (Windows) ---
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3
TIPOS_UNIDAD_PERMITIDOS = (DRIVE_REMOVABLE, DRIVE_FIXED)

FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4

# --- UI Tkinter ---
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 650
WINDOW_TITLE = "Aibby - Asistente Personal de IA"

# --- TTS (texto a voz) ---
TTS_RATE = 175  # velocidad de lectura
TTS_VOLUME = 1.0  # volumen
