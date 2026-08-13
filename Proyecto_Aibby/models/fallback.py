"""Módulo de fallback y cambio de modelos."""
import threading
import time
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import MODELO_PRINCIPAL, MODELO_LIGERO
from .models_gemini import crear_chat, enviar_mensaje, obtener_historial
from utils import extraer_segundos_retry, es_429_rate_limit, RateLimitError, APIError


class ModeloFallback:
    """Gestiona el cambio entre modelos y el estado de cooldown."""
    
    def __init__(self, chat_inicial, callback_cambio_modelo=None, callback_cooldown=None):
        """Inicializa el gestor de fallback.
        
        Args:
            chat_inicial: Chat inicial con modelo principal
            callback_cambio_modelo: Función a llamar cuando cambia modelo
            callback_cooldown: Función a llamar para actualizar UI de cooldown
        """
        self.chat = chat_inicial
        self.modelo_actual = MODELO_PRINCIPAL
        self.lock = threading.Lock()
        self.callback_cambio_modelo = callback_cambio_modelo
        self.callback_cooldown = callback_cooldown
        
        # Estado de cooldown
        self.cooldown_activo = False
        self.cooldown_hasta = 0.0
        self.thread_cooldown = None
    
    def enviar_con_fallback(self, contenido):
        """Envía un mensaje con fallback automático.
        
        Si el modelo principal está en rate limit (429), cambia al ligero
        y reintenta una sola vez.
        
        Args:
            contenido: Mensaje a enviar
            
        Returns:
            Respuesta del modelo
            
        Raises:
            RateLimitError: Si ambos modelos están agotados
            APIError: Para otros errores
        """
        try:
            return enviar_mensaje(self.chat, contenido)
        except Exception as e:
            mensaje_error = str(e)
            
            if es_429_rate_limit(mensaje_error) and self.modelo_actual == MODELO_PRINCIPAL:
                self._cambiar_a_modelo_ligero(mensaje_error)
                try:
                    return enviar_mensaje(self.chat, contenido)
                except Exception as e2:
                    self._manejar_cooldown_total(e2)
                    raise
            else:
                raise
    
    def _cambiar_a_modelo_ligero(self, mensaje_error: str):
        """Cambia del modelo principal al ligero."""
        with self.lock:
            if self.modelo_actual == MODELO_LIGERO:
                return
            
            segundos = extraer_segundos_retry(mensaje_error)
            
            # Obtener historial para preservar contexto
            historial = obtener_historial(self.chat)
            
            # Cambiar modelo
            self.modelo_actual = MODELO_LIGERO
            self.chat = crear_chat(MODELO_LIGERO, historial)
            
            # Notificar cambio
            if self.callback_cambio_modelo:
                self.callback_cambio_modelo(
                    f"⚙️ {MODELO_PRINCIPAL} llegó a su límite temporal.\n"
                    f"Cambio automático a {MODELO_LIGERO} por ~{int(round(segundos))}s"
                )
            
            # Programar vuelta al modelo principal
            if self.thread_cooldown:
                self.thread_cooldown.join(timeout=0.1)
            self.thread_cooldown = threading.Timer(
                segundos,
                self._volver_a_modelo_principal
            )
            self.thread_cooldown.daemon = True
            self.thread_cooldown.start()
    
    def _volver_a_modelo_principal(self):
        """Vuelve al modelo principal después del cooldown."""
        with self.lock:
            if self.modelo_actual == MODELO_PRINCIPAL:
                return
            
            historial = obtener_historial(self.chat)
            self.modelo_actual = MODELO_PRINCIPAL
            self.chat = crear_chat(MODELO_PRINCIPAL, historial)
            
            if self.callback_cambio_modelo:
                self.callback_cambio_modelo(
                    f"✅ De vuelta en el modelo principal ({MODELO_PRINCIPAL})."
                )
    
    def _manejar_cooldown_total(self, error):
        """Activa cooldown total cuando ambos modelos están agotados."""
        mensaje_error = str(error)
        
        if es_429_rate_limit(mensaje_error):
            segundos = extraer_segundos_retry(mensaje_error)
            self.iniciar_cooldown(segundos)
    
    def iniciar_cooldown(self, segundos: float):
        """Inicia el cooldown visual que bloquea la interfaz.
        
        Args:
            segundos: Duración del cooldown en segundos
        """
        with self.lock:
            segundos = max(1, int(round(segundos)))
            self.cooldown_activo = True
            self.cooldown_hasta = time.monotonic() + segundos
            
            if self.callback_cooldown:
                self.callback_cooldown("iniciar", segundos)
            
            # Actualizar cooldown en tiempo real
            self._actualizar_cooldown_visual()
    
    def _actualizar_cooldown_visual(self):
        """Actualiza la visualización del cooldown."""
        if not self.cooldown_activo:
            return
        
        restantes = max(0, int(round(self.cooldown_hasta - time.monotonic())))
        
        if restantes > 0:
            if self.callback_cooldown:
                self.callback_cooldown("actualizar", restantes)
            # Programar siguiente actualización
            threading.Timer(0.25, self._actualizar_cooldown_visual).start()
        else:
            self.cooldown_activo = False
            if self.callback_cooldown:
                self.callback_cooldown("finalizar", 0)
    
    def obtener_modelo_actual(self) -> str:
        """Retorna el modelo activo actualmente."""
        with self.lock:
            return self.modelo_actual
