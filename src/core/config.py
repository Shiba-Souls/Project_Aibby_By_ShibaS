import os
from dotenv import load_dotenv

class Config:
    @classmethod
    def obtener_api_key(cls):
        """Carga el .env dinámicamente y devuelve la clave (soporta ambos nombres)."""
        load_dotenv(".env", override=True)
        return os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")

    # Modelos de Gemini
    MODELO_PRINCIPAL = "gemini-3.6-flash"
    MODELO_LIGERO = "gemini-3.1-flash-lite"
    
    # Configuración de Whisper
    WHISPER_MODEL = "base"
    
    # Configuración de Audio
    SAMPLE_RATE = 16000