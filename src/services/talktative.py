import os
import threading
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import pygame
from google import genai
from google.genai import types

from src.core.config import Config

class Talktative:
    def __init__(self):
        # 1. Configurar FFmpeg y Whisper Local
        os.environ["PATH"] += os.pathsep + os.getcwd()
        
        # Cargamos el modelo apuntando al archivo base.pt local
        print("Cargando modelo Whisper (base.pt)...")
        self.whisper_model = whisper.load_model("base.pt")
        
        # 2. Configuración de grabación
        self.sample_rate = 16000
        self.grabando = False
        self.frames = []
        self.stream = None
        
        # 3. Configuración de GenAI TTS
        self.client = genai.Client(api_key=Config.API_KEY)
        self.tts_lock = threading.Lock()
        
        # Inicializamos pygame para reproducir el audio de forma invisible
        pygame.mixer.init()

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