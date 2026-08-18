import os
import threading
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import pygame
import torch
from google import genai
from google.genai import types

from src.core.config import Config
torch.backends.mkldnn.enabled = False

class Talktative:
    def __init__(self):
        # --- RUTA ABSOLUTA PARA PYINSTALLER ---
        import sys
        if getattr(sys, 'frozen', False):
            self.ruta_base = os.path.dirname(sys.executable)
        else:
            self.ruta_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        # 1. Configurar FFmpeg y Whisper Local usando la ruta absoluta
        os.environ["PATH"] += os.pathsep + self.ruta_base
        
        # Cargamos el modelo apuntando al archivo base.pt exacto
        ruta_modelo_whisper = os.path.join(self.ruta_base, "base.pt")
        print(f"Cargando modelo Whisper desde: {ruta_modelo_whisper}")
        
        # Si no existe el modelo, evitamos que la app se rompa (útil para el primer inicio)
        if not os.path.exists(ruta_modelo_whisper):
            print("⚠️ ADVERTENCIA: No se encontró base.pt. El micrófono no funcionará hasta descargarlo.")
            self.whisper_model = None
        else:
            self.whisper_model = whisper.load_model(ruta_modelo_whisper)
        
        # 2. Configuración de grabación
        self.sample_rate = Config.SAMPLE_RATE  # 16000 Hz, antes hardcodeado mal en 1600
        self.grabando = False
        self.frames = []
        self.stream = None
        
        # 3. Configuración de GenAI TTS
        self.client = genai.Client(api_key=Config.obtener_api_key())
        self.tts_lock = threading.Lock()
        
        # Inicializamos pygame para reproducir el audio de forma invisible.
        # Si la PC no tiene un dispositivo de audio activo (sin parlantes/auriculares,
        # o audio deshabilitado en Windows), pygame.mixer.init() tira pygame.error
        # (ej: "WASAPI can't find requested audio endpoint"). No dejamos que esto
        # tire abajo toda la app: Aibby sigue funcionando por texto, solo sin voz.
        self.audio_disponible = True
        try:
            pygame.mixer.init()
        except pygame.error as e:
            self.audio_disponible = False
            print(f"⚠️ No se pudo inicializar el audio (sin dispositivo de salida?): {e}")
            print("⚠️ Aibby va a funcionar sin voz (TTS deshabilitado).")

    # --- PARTE 1: OÍDOS (Speech to Text con Whisper) ---

    def _callback_audio(self, indata, frames_count, time, status):
        """Guarda los fragmentos de audio mientras se habla."""
        if self.grabando:
            self.frames.append(indata.copy())

    def iniciar_grabacion(self):
        """Abre el micrófono y empieza a guardar audio."""
        self.frames = []
        self.grabando = True
        self.stream = sd.InputStream(
            samplerate=self.sample_rate, 
            channels=1, 
            callback=self._callback_audio
        )
        self.stream.start()

    def detener_grabacion_y_transcribir(self):
        """Corta el micrófono, guarda el archivo temporal y usa Whisper."""
        self.grabando = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        if not self.frames:
            return ""

        if self.whisper_model is None:
            print("⚠️ No se puede transcribir: falta el modelo Whisper (base.pt).")
            return ""

        # Unimos los fragmentos y guardamos un wav temporal
        audio_data = np.concatenate(self.frames, axis=0)
        archivo_temp = "temp_mic.wav"
        write(archivo_temp, self.sample_rate, audio_data)
        
        # Whisper hace la magia localmente
        resultado = self.whisper_model.transcribe(archivo_temp, language="es", fp16=False)
        texto_transcrito = resultado["text"].strip()
        
        # Limpiamos el archivo temporal
        if os.path.exists(archivo_temp):
            os.remove(archivo_temp)
            
        return texto_transcrito

    # --- PARTE 2: VOZ (Text to Speech con GenAI) ---

    def decir(self, texto):
        """Usa GenAI para generar la voz de Aibby y la reproduce."""
        if not texto:
            return

        if not self.audio_disponible:
            return  # Sin dispositivo de audio: no tiene sentido ni llamar a la API de TTS
            
        with self.tts_lock:
            try:
                # Le pedimos a GenAI que "lea" el texto usando la modalidad de audio
                respuesta = self.client.models.generate_content(
                    model=Config.MODELO_PRINCIPAL,
                    contents=f"Lee el siguiente texto con naturalidad y sin agregar nada más: {texto}",
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name="Aoede"  # Voces geniales: Aoede, Puck, Charon, Kore
                                )
                            )
                        )
                    )
                )
                
                # Extraemos los bytes del audio de la respuesta
                audio_bytes = None
                for candidate in respuesta.candidates:
                    for part in candidate.content.parts:
                        if part.inline_data:
                            audio_bytes = part.inline_data.data
                            break
                            
                if audio_bytes:
                    # Lo guardamos temporalmente para que pygame lo reproduzca
                    archivo_voz = "temp_aibby_voice.wav"
                    with open(archivo_voz, "wb") as f:
                        f.write(audio_bytes)
                        
                    # Reproducir usando pygame
                    pygame.mixer.music.load(archivo_voz)
                    pygame.mixer.music.play()
                    
                    # Esperamos a que termine de hablar antes de continuar
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                        
                    # Liberamos el archivo para poder borrarlo
                    pygame.mixer.music.unload()
                    os.remove(archivo_voz)
                    
            except Exception as e:
                print(f"Error en TTS de GenAI: {e}")