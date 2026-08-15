import customtkinter as ctk
import os
import threading
import webbrowser  # <-- NUEVO IMPORT PARA ABRIR LINKS
from google import genai

class SetupWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Aibby - Configuración Inicial")
        self.geometry("500x480")  # <-- Ventana más alta para que entre la advertencia
        self.resizable(False, False)
        self.eval('tk::PlaceWindow . center')

        # Título
        self.label_titulo = ctk.CTkLabel(
            self, text="¡Bienvenido a Aibby!", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.label_titulo.pack(pady=(20, 5))

        # Instrucciones API
        self.label_instrucciones = ctk.CTkLabel(
            self, text="Ingresa tu API Key de Google Gemini:", 
            font=ctk.CTkFont(size=13)
        )
        self.label_instrucciones.pack(pady=(0, 5))

        # Campo de texto API
        self.entry_apikey = ctk.CTkEntry(
            self, width=380, placeholder_text="AIzaSy...", show="*"
        )
        self.entry_apikey.pack(pady=(0, 10))

        # --- NUEVO: RECUADRO DE ADVERTENCIA PARA ARCHIVOS LOCALES ---
        # Creamos un marco (Frame) para agrupar visualmente las advertencias
        self.frame_adv = ctk.CTkFrame(self, corner_radius=8)
        self.frame_adv.pack(pady=5, padx=30, fill="x")

        self.lbl_adv_titulo = ctk.CTkLabel(
            self.frame_adv, 
            text="⚠️ Archivos requeridos para el reconocimiento de voz", 
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffcc00" # Amarillo advertencia
        )
        self.lbl_adv_titulo.pack(pady=(10, 0))
        
        self.lbl_adv_texto = ctk.CTkLabel(
            self.frame_adv, 
            text="Para que Aibby te escuche, debes tener estos dos archivos\nen la misma carpeta donde se encuentra el ejecutable de Aibby:", 
            font=ctk.CTkFont(size=12)
        )
        self.lbl_adv_texto.pack(pady=(5, 10))

        # Link 1: base.pt (Descarga directa oficial de OpenAI)
        self.lbl_link_base = ctk.CTkLabel(
            self.frame_adv, 
            text="📥 1. Descargar modelo (base.pt)", 
            font=ctk.CTkFont(size=12, underline=True),
            text_color="#3a86ff", # Azul estilo enlace
            cursor="hand2"        # Cursor de manito al pasar por encima
        )
        self.lbl_link_base.pack(pady=0)
        self.lbl_link_base.bind("<Button-1>", lambda e: webbrowser.open(
            "https://openaipublic.azureedge.net/main/whisper/models/ed3a0b28610eb4110ae252839d666181f920f4f9b8c381f1cfc0f1e84a287bf1/base.pt"
        ))

        # Link 2: FFmpeg (Descarga un ZIP, le avisamos al usuario que extraiga el exe)
        self.lbl_link_ffmpeg = ctk.CTkLabel(
            self.frame_adv, 
            text="📥 2. Descargar FFmpeg (extraer ffmpeg.exe del archivo zip)", 
            font=ctk.CTkFont(size=12, underline=True),
            text_color="#3a86ff",
            cursor="hand2"
        )
        self.lbl_link_ffmpeg.pack(pady=(5, 15))
        self.lbl_link_ffmpeg.bind("<Button-1>", lambda e: webbrowser.open(
            "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-gpl.zip"
        ))
        # -------------------------------------------------------------

        # Label de estado (mensajes de carga o error)
        self.label_estado = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12)
        )
        self.label_estado.pack(pady=(5, 5))

        # Botón de acción
        self.btn_guardar = ctk.CTkButton(
            self, text="Validar y Guardar", command=self.iniciar_validacion
        )
        self.btn_guardar.pack(pady=(0, 15))

    def iniciar_validacion(self):
        clave = self.entry_apikey.get().strip()
        if not clave:
            self.label_estado.configure(
                text="Por favor, pega una API Key válida.", text_color="orange"
            )
            return

        # Deshabilitamos el botón y mostramos estado de carga
        self.btn_guardar.configure(state="disabled", text="Verificando...")
        self.label_estado.configure(
            text="Probando conexión con Gemini...", text_color="gray"
        )
        
        # Ejecutamos la prueba en un hilo para no congelar la GUI
        threading.Thread(target=self._probar_conexion, args=(clave,), daemon=True).start()

    def _probar_conexion(self, clave):
        try:
            # Prueba liviana para verificar autenticación
            client = genai.Client(api_key=clave)
            client.models.generate_content(
                model='gemini-2.5-flash',
                contents='ping'
            )
            
            # Si responde con éxito, guardamos en el .env y cerramos
            with open(".env", "w") as f:
                f.write(f"GEMINI_API_KEY={clave}\n")
            
            self.destroy()

        except Exception:
            # Si la clave es errónea o no hay internet, rehabilitamos los controles
            self.btn_guardar.configure(state="normal", text="Validar y Guardar")
            self.label_estado.configure(
                text="API Key no válida o error de red. Verifícala.", 
                text_color="red"
            )