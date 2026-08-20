import os
import sys
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import torch

from src.core.config import Config
torch.backends.mkldnn.enabled = False


class Talktative:
    """Los OÍDOS de Aibby: graba el micrófono y lo transcribe a texto con
    Whisper local. El habla (texto -> audio) la maneja PaiperTTS por separado,
    así que acá ya no queda nada relacionado con GenAI ni con pygame."""

    def __init__(self):
        # --- RUTA ABSOLUTA PARA PYINSTALLER ---
        if getattr(sys, 'frozen', False):
            self.ruta_base = os.path.dirname(sys.executable)
        else:
            self.ruta_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        # Configurar FFmpeg (lo necesita Whisper) usando la ruta absoluta
        os.environ["PATH"] += os.pathsep + self.ruta_base

        # Cargamos el modelo apuntando al archivo base.pt exacto
        ruta_modelo_whisper = os.path.join(self.ruta_base, "base.pt")
        print(f"Cargando modelo Whisper desde: {ruta_modelo_whisper}")

        if not os.path.exists(ruta_modelo_whisper):
            print("⚠️ ADVERTENCIA: No se encontró base.pt. El micrófono no funcionará hasta descargarlo.")
            self.whisper_model = None
        else:
            self.whisper_model = whisper.load_model(ruta_modelo_whisper)

        # Configuración de grabación
        self.sample_rate = Config.SAMPLE_RATE
        self.grabando = False
        self.frames = []
        self.stream = None

    # --- OÍDOS (Speech to Text con Whisper) ---

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

        audio_data = np.concatenate(self.frames, axis=0)
        archivo_temp = "temp_mic.wav"
        write(archivo_temp, self.sample_rate, audio_data)

        resultado = self.whisper_model.transcribe(archivo_temp, language="es", fp16=False)
        texto_transcrito = resultado["text"].strip()

        if os.path.exists(archivo_temp):
            os.remove(archivo_temp)

        return texto_transcrito