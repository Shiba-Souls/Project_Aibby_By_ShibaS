"""Módulo de interacción con la API de Gemini."""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from google import genai
from google.genai import types
from config import API_KEY, SYSTEM_INSTRUCTION
from utils import APIError


# Inicializar cliente de Gemini
client = genai.Client(api_key=API_KEY)


def crear_chat(modelo: str, historial=None):
    """Crea una sesión de chat nueva con el modelo indicado.
    
    Args:
        modelo: Nombre del modelo a usar
        historial: Historial existente para preservar contexto
        
    Returns:
        Objeto chat de Gemini
    """
    try:
        return client.chats.create(
            model=modelo,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
            history=historial or []
        )
    except Exception as e:
        raise APIError(f"Error creando chat: {str(e)}")


def enviar_mensaje(chat, contenido):
    """Envía un mensaje al chat y obtiene la respuesta.
    
    Args:
        chat: Objeto chat de Gemini
        contenido: Contenido a enviar (puede ser texto o incluir audio)
        
    Returns:
        Texto de la respuesta
    """
    try:
        respuesta = chat.send_message(contenido)
        return respuesta.text
    except Exception as e:
        raise APIError(f"Error enviando mensaje: {str(e)}")


def generar_contenido(modelo: str, contenido):
    """Genera contenido sin chat (uso único).
    
    Args:
        modelo: Nombre del modelo
        contenido: Contenido a procesar
        
    Returns:
        Texto de la respuesta
    """
    try:
        respuesta = client.models.generate_content(model=modelo, contents=contenido)
        return respuesta.text
    except Exception as e:
        raise APIError(f"Error generando contenido: {str(e)}")


def obtener_historial(chat):
    """Obtiene el historial del chat.
    
    Args:
        chat: Objeto chat de Gemini
        
    Returns:
        Historial del chat o lista vacía si hay error
    """
    try:
        return chat.get_history()
    except Exception:
        return []
