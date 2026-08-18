import os
import sys
from dotenv import load_dotenv

class Config:
    @classmethod
    def obtener_api_key(cls):
        """Carga el .env dinámicamente y devuelve la clave (ruta absoluta para PyInstaller)."""
        if getattr(sys, 'frozen', False):
            ruta_base = os.path.dirname(sys.executable)
        else:
            # En VS Code, la raíz del proyecto está dos niveles arriba de src/core
            ruta_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            
        archivo_env = os.path.join(ruta_base, ".env")
        load_dotenv(archivo_env, override=True)
        
        return os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")

    @staticmethod
    def obtener_ruta_recurso(nombre_archivo):
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, nombre_archivo)
        else:
            ruta_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            return os.path.join(ruta_base, nombre_archivo)

    # Modelos de Gemini
    MODELO_PRINCIPAL = "gemini-3.6-flash"
    MODELO_LIGERO = "gemini-3.1-flash-lite"
    
    # Configuración de Whisper
    WHISPER_MODEL = "base"
    
    # Configuración de Audio
    SAMPLE_RATE = 16000