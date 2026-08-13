"""Main.py - Script principal que orquesta Aibby.

Orquestación de todos los módulos para crear la aplicación completa.
"""
import threading
import sys
from pathlib import Path

# Asegurar que el directorio raíz esté en el path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from google.genai import types

from config import MODELO_PRINCIPAL, PALABRAS_BUSQUEDA
from core import UIbby, obtener_grabador, obtener_tts, buscar_archivos_por_consulta, formatear_resultados_busqueda
from models import crear_chat, generar_contenido, ModeloFallback
from utils import FileSearchError, RateLimitError, APIError, AudioError


class Aibby:
    """Controlador principal de Aibby."""
    
    def __init__(self):
        """Inicializa Aibby."""
        # Inicializar chat con modelo principal
        self.chat_inicial = crear_chat(MODELO_PRINCIPAL)
        
        # Inicializar gestor de fallback
        self.fallback = ModeloFallback(
            self.chat_inicial,
            callback_cambio_modelo=self._en_cambio_modelo,
            callback_cooldown=self._en_cambio_cooldown
        )
        
        # Inicializar interfaz
        self.ui = UIbby(
            callback_enviar_texto=self._procesar_envio_texto,
            callback_grabar=self._toggle_grabacion
        )
        
        # Audio
        self.grabador = obtener_grabador()
        self.tts = obtener_tts()
        self.grabando = False
    
    # ========== Callbacks de la UI ==========
    
    def _procesar_envio_texto(self):
        """Procesa el envío de texto desde la interfaz."""
        if self.ui.es_cooldown_activo():
            return
        
        mensaje = self.ui.obtener_texto_entrada()
        if not mensaje:
            return
        
        self.ui.mostrar_mensaje("Vos", mensaje)
        self.ui.limpiar_entrada()
        
        # Procesar en hilo separado
        threading.Thread(
            target=self._procesar_mensaje,
            args=(mensaje,),
            daemon=True
        ).start()
    
    def _toggle_grabacion(self):
        """Toggle del botón de grabación."""
        if not self.grabando:
            self.grabando = True
            self.ui.cambiar_estado_grabacion(True)
            self.grabador.iniciar_grabacion()
        else:
            self.grabando = False
            self.ui.cambiar_estado_grabacion(False)
            
            # Procesar audio en hilo separado
            threading.Thread(
                target=self._procesar_audio,
                daemon=True
            ).start()
    
    # ========== Procesamiento de mensajes ==========
    
    def _procesar_mensaje(self, mensaje: str):
        """Procesa un mensaje de texto.
        
        Args:
            mensaje: Texto del mensaje del usuario
        """
        try:
            # Detectar si es búsqueda de archivos
            if self._es_busqueda_de_archivos(mensaje):
                respuesta = self._procesar_busqueda(mensaje)
            else:
                respuesta = self.fallback.enviar_con_fallback(mensaje)
            
            # Mostrar respuesta
            self.ui.agendar_en_ventana(
                lambda: self.ui.mostrar_mensaje("Aibby", respuesta)
            )
            
            # Reproducir en voz
            self.tts.hablar(respuesta)
            
        except RateLimitError:
            # El cooldown se maneja en fallback.py
            pass
        except FileSearchError as e:
            self._mostrar_error(f"Error en búsqueda: {str(e)}")
        except APIError as e:
            self._mostrar_error(f"Error de API: {str(e)}")
        except Exception as e:
            self._mostrar_error(f"Error: {str(e)}")
    
    def _procesar_audio(self):
        """Procesa el audio grabado."""
        try:
            # Obtener bytes del audio
            audio_bytes = self.grabador.obtener_bytes_audio()
            
            # Mostrar que se envió audio
            self.ui.agendar_en_ventana(
                lambda: self.ui.mostrar_mensaje("Vos", "[audio enviado]")
            )
            
            # Crear prompt para detectar búsqueda vs pregunta normal
            contenido = [
                "Instrucciones: si lo que se dice en el audio es un pedido de "
                "buscar, encontrar, o preguntar dónde está un archivo en la "
                "computadora, respondé ÚNICAMENTE con este formato exacto: "
                "BUSCAR: <lo que se pide buscar, en pocas palabras>. "
                "Si NO es una petición de búsqueda de archivos, respondé "
                "normalmente a lo que se dice en el audio, como Aibby.",
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
            ]
            
            # Procesar con modelo
            texto_modelo = self.fallback.enviar_con_fallback(contenido).strip()
            
            # Determinar si es búsqueda o respuesta normal
            if texto_modelo.upper().startswith("BUSCAR:"):
                consulta = texto_modelo.split(":", 1)[1].strip()
                respuesta = self._procesar_busqueda(consulta)
            else:
                respuesta = texto_modelo
            
            # Mostrar y reproducir
            self.ui.agendar_en_ventana(
                lambda: self.ui.mostrar_mensaje("Aibby", respuesta)
            )
            self.tts.hablar(respuesta)
            
        except AudioError as e:
            self._mostrar_error(f"Error de audio: {str(e)}")
        except RateLimitError:
            # Cooldown manejado en fallback
            pass
        except APIError as e:
            self._mostrar_error(f"Error de API: {str(e)}")
        except Exception as e:
            self._mostrar_error(f"Error procesando audio: {str(e)}")
    
    def _procesar_busqueda(self, consulta: str) -> str:
        """Procesa una búsqueda de archivos.
        
        Args:
            consulta: Texto de la búsqueda
            
        Returns:
            Respuesta formateada con resultados
        """
        # Buscar archivos
        archivos = buscar_archivos_por_consulta(consulta)
        
        if not archivos:
            return "No encontré archivos que coincidan con esa búsqueda."
        
        # Formatear resultados
        lista_texto = "\n".join(archivos)
        
        # Pedir a IA que haga respuesta natural
        prompt = f"""El usuario pidió buscar: "{consulta}"

Estos son los archivos encontrados en su PC que podrían coincidir:
{lista_texto}

Respondé de forma breve y natural, como Aibby, mencionando qué encontraste (nombre de archivo y en qué carpeta está)."""
        
        respuesta = generar_contenido(self.fallback.obtener_modelo_actual(), prompt)
        return respuesta
    
    def _es_busqueda_de_archivos(self, mensaje: str) -> bool:
        """Detecta si el mensaje es una búsqueda de archivos."""
        return any(palabra in mensaje.lower() for palabra in PALABRAS_BUSQUEDA)
    
    def _mostrar_error(self, mensaje: str):
        """Muestra un error en la UI."""
        self.ui.agendar_en_ventana(
            lambda: self.ui.mostrar_mensaje("Error", mensaje)
        )
    
    # ========== Callbacks del fallback ==========
    
    def _en_cambio_modelo(self, mensaje: str):
        """Se llama cuando cambia el modelo."""
        self.ui.agendar_en_ventana(
            lambda: [
                self.ui.mostrar_mensaje("Sistema", mensaje),
                self.ui.cambiar_modelo_label(self.fallback.obtener_modelo_actual())
            ]
        )
    
    def _en_cambio_cooldown(self, tipo: str, segundos: int):
        """Se llama cuando cambia el estado del cooldown.
        
        Args:
            tipo: "iniciar", "actualizar" o "finalizar"
            segundos: Segundos restantes
        """
        if tipo == "iniciar":
            self.ui.agendar_en_ventana(
                lambda s=segundos: self.ui.iniciar_cooldown(s)
            )
        elif tipo == "actualizar":
            self.ui.agendar_en_ventana(
                lambda s=segundos: self.ui.actualizar_cooldown(s)
            )
        elif tipo == "finalizar":
            self.ui.agendar_en_ventana(
                lambda: self.ui.finalizar_cooldown()
            )
    
    # ========== Ejecución ==========
    
    def ejecutar(self):
        """Inicia la aplicación."""
        self.ui.ejecutar()


if __name__ == "__main__":
    aibby = Aibby()
    aibby.ejecutar()
