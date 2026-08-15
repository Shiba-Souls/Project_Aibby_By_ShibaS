import os
from dotenv import load_dotenv

# Carga el archivo .env (asegurate de que se llame .env o api_key.env)
load_dotenv(".env")

class Config:
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        raise RuntimeError(
            "No se encontró API_KEY. Revisá que exista un archivo .env "
            "con la línea API_KEY=tu_clave"
        )
    
    # Modelos de Gemini
    MODELO_PRINCIPAL = "gemini-3.6-flash"
    MODELO_LIGERO = "gemini-3.1-flash-lite"
    
    # Configuración de Whisper
    WHISPER_MODEL = "base" # o la ruta exacta a "base.pt" si lo cargas manual
    
    # Configuración de Audio
    SAMPLE_RATE = 16000