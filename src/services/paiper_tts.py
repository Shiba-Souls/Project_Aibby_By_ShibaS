import os
import sys
import subprocess
import threading
import pygame


class PaiperTTS:
    def __init__(self):
        # --- RUTA ABSOLUTA (mismo patrón que el resto de Aibby, para que
        # funcione tanto en VS Code como compilado con PyInstaller) ---
        if getattr(sys, 'frozen', False):
            self.ruta_base = os.path.dirname(sys.executable)
        else:
            self.ruta_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        self.carpeta_piper = os.path.join(self.ruta_base, "piper")
        self.ruta_exe = os.path.join(self.carpeta_piper, "piper.exe")
        self.ruta_modelo = os.path.join(self.carpeta_piper, "es_AR-daniela-high.onnx")
        self.ruta_config = os.path.join(self.carpeta_piper, "es_AR-daniela-high.onnx.json")

        self.disponible = (
            os.path.exists(self.ruta_exe)
            and os.path.exists(self.ruta_modelo)
            and os.path.exists(self.ruta_config)
        )

        if not self.disponible:
            print(
                "⚠️ Piper TTS no está disponible: revisá que existan "
                "piper.exe, daniela.onnx y daniela.onnx.json dentro de la carpeta 'piper/'."
            )

        self.tts_lock = threading.Lock()

        # Reusamos pygame.mixer si ya lo inicializó Talktative; si no, lo iniciamos acá.
        self.audio_disponible = True
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as e:
                self.audio_disponible = False
                print(f"⚠️ No se pudo inicializar el audio para Piper: {e}")

    def decir(self, texto):
        """Genera el audio con Piper y lo reproduce. Bloquea hasta que termina de hablar
        (mismo comportamiento que Talktative.decir, para poder intercambiarlos)."""
        if not texto or not self.disponible or not self.audio_disponible:
            return

        with self.tts_lock:
            archivo_voz = os.path.join(self.ruta_base, "temp_aibby_piper.wav")

            comando = [
                self.ruta_exe,
                "--model", self.ruta_modelo,
                "--config", self.ruta_config,
                "--output_file", archivo_voz,
            ]

            try:
                # Piper lee el texto por stdin y escribe el wav en archivo_voz
                subprocess.run(
                    comando,
                    input=texto.encode("utf-8"),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    cwd=self.carpeta_piper,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    check=True,
                )

                if not os.path.exists(archivo_voz):
                    print("⚠️ Piper no generó el archivo de audio.")
                    return

                pygame.mixer.music.load(archivo_voz)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

                pygame.mixer.music.unload()
                os.remove(archivo_voz)

            except subprocess.CalledProcessError as e:
                detalle = e.stderr.decode(errors="ignore") if e.stderr else str(e)
                print(f"Error ejecutando Piper: {detalle}")
            except Exception as e:
                print(f"Error en TTS de Piper: {e}")