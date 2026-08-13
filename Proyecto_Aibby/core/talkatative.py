"""Módulo de audio: grabación, procesamiento y texto a voz."""
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import threading
import pyttsx3
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import SAMPLE_RATE, AUDIO_TEMP_FILE, TTS_RATE, TTS_VOLUME
from utils import AudioError


class GrabadorAudio:
    """Gestiona la grabación de audio del micrófono."""
    
    def __init__(self):
        self.grabando = False
        self.frames = []
    
    def iniciar_grabacion(self):
        """Inicia la grabación de audio."""
        self.frames = []
        self.grabando = True
        threading.Thread(target=self._grabar, daemon=True).start()
    
    def detener_grabacion(self) -> bool:
        """Detiene la grabación y retorna si hubo frames."""
        self.grabando = False
        return len(self.frames) > 0
    
    def _callback_audio(self, indata, frames_count, time, status):
        """Callback para sounddevice."""
        if status:
            print(f"Estado de audio: {status}")
        self.frames.append(indata.copy())
    
    def _grabar(self):
        """Hilo de grabación."""
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                callback=self._callback_audio
            ):
                while self.grabando:
                    sd.sleep(100)
        except Exception as e:
            raise AudioError(f"Error durante grabación: {str(e)}")
    
    def obtener_bytes_audio(self) -> bytes:
        """Procesa los frames grabados y retorna bytes de audio WAV.
        
        Returns:
            Bytes del archivo WAV
            
        Raises:
            AudioError: Si no hay frames o error al procesar
        """
        if not self.frames:
            raise AudioError("No se grabó audio.")
        
        try:
            # Concatenar frames
            audio_data = np.concatenate(self.frames, axis=0)
            
            # Guardar a archivo temporal
            write(AUDIO_TEMP_FILE, SAMPLE_RATE, audio_data)
            
            # Leer archivo
            with open(AUDIO_TEMP_FILE, "rb") as f:
                audio_bytes = f.read()
            
            # Limpiar archivo temporal
            try:
                os.remove(AUDIO_TEMP_FILE)
            except:
                pass
            
            return audio_bytes
            
        except Exception as e:
            raise AudioError(f"Error procesando audio: {str(e)}")


class TextoAVoz:
    """Gestiona la reproducción de texto como audio."""
    
    def __init__(self):
        self.lock = threading.Lock()
    
    def hablar(self, texto: str):
        """Convierte texto a voz y lo reproduce.
        
        Args:
            texto: Texto a reproducir
        """
        if not texto:
            return
        
        threading.Thread(
            target=self._reproducir,
            args=(texto,),
            daemon=True
        ).start()
    
    def _reproducir(self, texto: str):
        """Reproduce el texto en voz (se ejecuta en un hilo)."""
        with self.lock:
            try:
                motor = pyttsx3.init()
                motor.setProperty("rate", TTS_RATE)
                motor.setProperty("volume", TTS_VOLUME)
                motor.say(texto)
                motor.runAndWait()
                motor.stop()
            except Exception as e:
                print(f"Error en texto a voz: {e}")


# Instancias globales
grabador = GrabadorAudio()
tts = TextoAVoz()


def obtener_grabador():
    """Retorna la instancia del grabador."""
    return grabador


def obtener_tts():
    """Retorna la instancia de TTS."""
    return tts
