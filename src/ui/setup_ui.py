import customtkinter as ctk
import os
import threading
from google import genai

class SetupWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Aibby - Configuración Inicial")
        self.geometry("450x290")
        self.resizable(False, False)
        self.eval('tk::PlaceWindow . center')

        # Título
        self.label_titulo = ctk.CTkLabel(
            self, text="¡Bienvenido a Aibby!", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.label_titulo.pack(pady=(20, 5))

        # Instrucciones
        self.label_instrucciones = ctk.CTkLabel(
            self, text="Ingresa tu API Key de Google Gemini:", 
            font=ctk.CTkFont(size=13)
        )
        self.label_instrucciones.pack(pady=(0, 15))

        # Campo de texto para la API Key
        self.entry_apikey = ctk.CTkEntry(
            self, width=360, placeholder_text="AIzaSy...", show="*"
        )
        self.entry_apikey.pack(pady=(0, 10))

        # Label de estado (mensajes de carga o error)
        self.label_estado = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12)
        )
        self.label_estado.pack(pady=(0, 10))

        # Botón de acción
        self.btn_guardar = ctk.CTkButton(
            self, text="Validar y Guardar", command=self.iniciar_validacion
        )
        self.btn_guardar.pack()

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
            # Hacemos una prueba ultra liviana para verificar autenticación
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