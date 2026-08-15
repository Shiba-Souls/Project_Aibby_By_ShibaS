import re
import time
import threading
from google import genai
from google.genai import types

# Importamos nuestras configuraciones previas
from src.core.config import Config
from src.core.person_ai import PersonAI

class AICall:
    def __init__(self):
        self.client = genai.Client(api_key=Config.obtener_api_key())
        self.modelo_actual = Config.MODELO_PRINCIPAL
        self.modelo_lock = threading.Lock()
        
        # Estado de Cooldown
        self.cooldown_activo = False
        self.cooldown_hasta = 0.0
        
        # Iniciamos el chat
        self.chat = self._crear_chat(self.modelo_actual)
        
        # Callbacks (se los inyectará la UI más adelante para no mezclar código)
        self.on_model_change = None 
        self.on_cooldown = None
    def _crear_chat(self, modelo, historial=None):
        """Crea una sesión de chat nueva conservando el historial si existe."""
        return self.client.chats.create(
            model=modelo,
            config=types.GenerateContentConfig(
                system_instruction=PersonAI.SYSTEM_INSTRUCTION
            ),
            history=historial or []
        )

    def _extraer_segundos_retry(self, mensaje_error):
        """Busca cuántos segundos pide esperar Gemini."""
        match = re.search(r"Please retry in\s+([\d.]+)s", str(mensaje_error), re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 60.0  # Valor por defecto

    def cambiar_a_modelo_ligero(self, mensaje_error):
        """Pasa al modelo liviano e inicia el temporizador para volver al principal."""
        with self.modelo_lock:
            if self.modelo_actual == Config.MODELO_LIGERO:
                return

            segundos = self._extraer_segundos_retry(mensaje_error)
            segundos_mostrar = max(1, int(round(segundos)))

            try:
                historial = self.chat.get_history()
            except Exception:
                historial = []

            self.modelo_actual = Config.MODELO_LIGERO
            self.chat = self._crear_chat(self.modelo_actual, historial)

            # Avisamos a la UI que cambiamos de modelo
            if self.on_model_change:
                self.on_model_change(
                    self.modelo_actual, 
                    f"⚙️ {Config.MODELO_PRINCIPAL} llegó al límite. "
                    f"Cambiando a {Config.MODELO_LIGERO} por ~{segundos_mostrar}s."
                )

            # Programamos el regreso automático sin bloquear ni depender de Tkinter
            threading.Timer(segundos_mostrar, self.volver_a_modelo_principal).start()

    def volver_a_modelo_principal(self):
        """Vuelve al modelo principal cuando se libera la cuota."""
        with self.modelo_lock:
            if self.modelo_actual == Config.MODELO_PRINCIPAL:
                return
            
            try:
                historial = self.chat.get_history()
            except Exception:
                historial = []
                
            self.modelo_actual = Config.MODELO_PRINCIPAL
            self.chat = self._crear_chat(self.modelo_actual, historial)

            if self.on_model_change:
                self.on_model_change(
                    self.modelo_actual, 
                    f"✅ De vuelta en el modelo principal ({Config.MODELO_PRINCIPAL})."
                )

    def manejar_error_total(self, error):
        """Se ejecuta si ambos modelos fallan o hay un error crítico."""
        mensaje_error = str(error)
        
        if "429" in mensaje_error and "RESOURCE_EXHAUSTED" in mensaje_error:
            segundos = self._extraer_segundos_retry(mensaje_error)
            
            self.cooldown_activo = True
            self.cooldown_hasta = time.monotonic() + max(1, int(round(segundos)))
            
            if self.on_cooldown:
                self.on_cooldown(self.cooldown_hasta)
                
            return f"⏳ Todos mis modelos están agotados. Volvé a intentarlo en {max(1, int(round(segundos)))} segundos."
        
        return f"❌ Error de sistema: {mensaje_error}"

    def enviar_mensaje(self, contenido):
        """
        Envía el mensaje. Si falla el principal por cuota, cambia al ligero
        y reintenta. Si falla todo, devuelve el mensaje de error.
        """
        if self.cooldown_activo and time.monotonic() < self.cooldown_hasta:
            return "⏳ Todavía estoy procesando el cooldown, esperá un ratito."
        else:
            self.cooldown_activo = False

        try:
            respuesta = self.chat.send_message(contenido)
            return respuesta.text
        
        except Exception as e:
            mensaje_error = str(e)
            es_429 = "429" in mensaje_error and "RESOURCE_EXHAUSTED" in mensaje_error

            # Si es 429 y estamos en el principal, hacemos fallback
            if es_429 and self.modelo_actual == Config.MODELO_PRINCIPAL:
                self.cambiar_a_modelo_ligero(mensaje_error)
                try:
                    # Reintento con el modelo liviano
                    respuesta = self.chat.send_message(contenido)
                    return respuesta.text
                except Exception as error_secundario:
                    return self.manejar_error_total(error_secundario)
            
            # Si ya estábamos en el ligero o es otro tipo de error
            return self.manejar_error_total(e)