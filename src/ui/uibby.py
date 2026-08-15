import threading
import time
import customtkinter as ctk
from src.core.cerebr_ai import CerebrAI

# Configuramos el tema general
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue") 

class Uibby(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cerebro = CerebrAI()
        self.grabando_mic = False
        
        # Configuración de la ventana
        self.title("Aibby - Asistente Personal de IA")
        self.geometry("600x700")
        
        # Conectar callbacks del servicio IA a la UI
        self.cerebro.ai_service.on_model_change = self.evento_cambio_modelo
        self.cerebro.ai_service.on_cooldown = self.evento_cooldown
        
        # Variables de estado de UI
        self.cooldown_activo = False
        self.cooldown_hasta = 0.0

        self._crear_widgets()

    def _crear_widgets(self):
        # --- Etiquetas de Estado ---
        self.modelo_label = ctk.CTkLabel(
            self, 
            text=f"⚙️ Modelo activo: {self.cerebro.ai_service.modelo_actual}", 
            font=("Segoe UI", 12)
        )
        self.modelo_label.pack(pady=(10, 0))

        self.cooldown_label = ctk.CTkLabel(
            self, 
            text="🟢 Aibby disponible", 
            font=("Segoe UI", 12, "bold"),
            text_color="#28a745" # Verde
        )
        self.cooldown_label.pack(pady=(0, 10))

        # --- Área de Chat ---
        self.chat_area = ctk.CTkTextbox(
            self, 
            wrap="word", 
            font=("Segoe UI", 14),
            state="disabled"
        )
        self.chat_area.pack(padx=20, pady=(0, 10), fill="both", expand=True)

        # --- Frame Inferior (Entrada y Botones) ---
        self.frame_inferior = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_inferior.pack(padx=20, pady=(0, 20), fill="x")

        self.entrada = ctk.CTkEntry(
            self.frame_inferior, 
            placeholder_text="Escribile a Aibby o pedile buscar un archivo...",
            font=("Segoe UI", 14),
            height=40
        )
        self.entrada.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entrada.bind("<Return>", self.enviar_texto)

        self.boton_enviar = ctk.CTkButton(
            self.frame_inferior, 
            text="Enviar", 
            width=80, 
            height=40,
            command=self.enviar_texto
        )
        self.boton_enviar.pack(side="left", padx=(0, 10))

        self.boton_grabar = ctk.CTkButton(
            self.frame_inferior, 
            text="🎤 Grabar", 
            width=80, 
            height=40,
            fg_color="#db5e5e", # Rojo claro
            hover_color="#ba4c4c",
            command=self.toggle_grabacion
        )
        self.boton_grabar.pack(side="left")

    # --- Lógica de Interfaz ---
    
    def mostrar_mensaje(self, quien, texto):
        """Inserta un mensaje en el área de chat de forma segura (Thread-Safe)."""
        self.chat_area.configure(state="normal")
        self.chat_area.insert("end", f"{quien}: {texto}\n\n")
        self.chat_area.configure(state="disabled")
        self.chat_area.see("end")

    def enviar_texto(self, event=None):
        if self.cooldown_activo:
            return

        mensaje = self.entrada.get().strip()
        if not mensaje:
            return

        self.mostrar_mensaje("Vos", mensaje)
        self.entrada.delete(0, "end")
        
        # Bloquear botón de envío temporalmente
        self.boton_enviar.configure(state="disabled")

        # Procesar en segundo plano para no congelar la UI
        threading.Thread(target=self._hilo_procesar, args=(mensaje,), daemon=True).start()

    def _hilo_procesar(self, mensaje):
        try:
            respuesta = self.cerebro.procesar_mensaje(mensaje)
            
            # Mostramos el texto en pantalla
            self.after(0, lambda: self.mostrar_mensaje("Aibby", respuesta))
            
            # Reproducimos el audio de GenAI
            self.cerebro.audio_service.decir(respuesta)
            
        except Exception as e:
            self.after(0, lambda: self.mostrar_mensaje("Sistema", f"Error crítico: {str(e)}"))
        finally:
            self.after(0, lambda: self.boton_enviar.configure(state="normal"))

    def toggle_grabacion(self):
        # Usamos un atributo nuevo 'self.grabando_mic' (asegurate de definirlo como False en el __init__)
        if not getattr(self, 'grabando_mic', False):
            self.grabando_mic = True
            self.boton_grabar.configure(text="⏹ Detener", fg_color="red", hover_color="#ba4c4c")
            
            # Encendemos Whisper
            self.cerebro.audio_service.iniciar_grabacion()
        else:
            self.grabando_mic = False
            self.boton_grabar.configure(text="🎤 Grabar", fg_color="#db5e5e", hover_color="#ba4c4c")
            self.boton_enviar.configure(state="disabled") # Bloqueamos mientras transcribe
            
            def procesar_audio():
                self.after(0, lambda: self.mostrar_mensaje("Sistema", "Transcribiendo audio con Whisper... ⏳"))
                
                texto_usuario = self.cerebro.audio_service.detener_grabacion_y_transcribir()
                
                if texto_usuario:
                    # Lo escribimos en la barra y lo enviamos como si lo hubieras tecleado
                    self.after(0, lambda: self.entrada.delete(0, "end"))
                    self.after(0, lambda: self.entrada.insert(0, texto_usuario))
                    self.after(0, self.enviar_texto)
                else:
                    self.after(0, lambda: self.mostrar_mensaje("Sistema", "No se escuchó nada."))
                    self.after(0, lambda: self.boton_enviar.configure(state="normal"))

            # Ejecutamos la transcripción en un hilo para no tildar la app
            threading.Thread(target=procesar_audio, daemon=True).start()

    # --- Eventos / Callbacks inyectados desde ai_call.py ---

    def evento_cambio_modelo(self, nuevo_modelo, mensaje_sistema):
        self.after(0, lambda: self.modelo_label.configure(text=f"⚙️ Modelo activo: {nuevo_modelo}"))
        if mensaje_sistema:
            self.after(0, lambda: self.mostrar_mensaje("Sistema", mensaje_sistema))

    def evento_cooldown(self, timestamp_hasta):
        self.cooldown_activo = True
        self.cooldown_hasta = timestamp_hasta
        self.after(0, self._bucle_actualizar_cooldown)

    def _bucle_actualizar_cooldown(self):
        if not self.cooldown_activo:
            return

        restantes = max(0, int(round(self.cooldown_hasta - time.monotonic())))

        if restantes > 0:
            self.cooldown_label.configure(
                text=f"⏳ Aibby en cooldown · {restantes} s",
                text_color="#ffc107" # Amarillo/Naranja
            )
            self.boton_enviar.configure(state="disabled")
            self.boton_grabar.configure(state="disabled")
            self.after(1000, self._bucle_actualizar_cooldown)
        else:
            self.cooldown_activo = False
            self.cooldown_label.configure(text="🟢 Aibby disponible", text_color="#28a745")
            self.boton_enviar.configure(state="normal")
            self.boton_grabar.configure(state="normal")