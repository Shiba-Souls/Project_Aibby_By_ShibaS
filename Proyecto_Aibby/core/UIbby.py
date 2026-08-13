"""Módulo de interfaz gráfica de Aibby."""
import tkinter as tk
from tkinter import scrolledtext
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, MODELO_PRINCIPAL


class UIbby:
    """Interfaz gráfica de Aibby."""
    
    def __init__(self, callback_enviar_texto=None, callback_grabar=None):
        """Inicializa la interfaz.
        
        Args:
            callback_enviar_texto: Función a llamar al enviar mensaje
            callback_grabar: Función a llamar al grabar audio
        """
        self.ventana = tk.Tk()
        self.ventana.title(WINDOW_TITLE)
        self.ventana.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        self.callback_enviar_texto = callback_enviar_texto
        self.callback_grabar = callback_grabar
        
        self._crear_widgets()
    
    def _crear_widgets(self):
        """Crea todos los widgets de la interfaz."""
        # Área de chat
        self.chat_area = scrolledtext.ScrolledText(
            self.ventana,
            wrap=tk.WORD,
            state="disabled",
            font=("Segoe UI", 10)
        )
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Label de modelo actual
        self.modelo_label = tk.Label(
            self.ventana,
            text=f"⚙️ Modelo activo: {MODELO_PRINCIPAL}",
            font=("Segoe UI", 9)
        )
        self.modelo_label.pack(pady=(0, 2))
        
        # Label de cooldown
        self.cooldown_label = tk.Label(
            self.ventana,
            text="🟢 Aibby disponible",
            font=("Segoe UI", 9)
        )
        self.cooldown_label.pack(pady=(0, 5))
        
        # Frame inferior con entrada y botones
        frame_inferior = tk.Frame(self.ventana)
        frame_inferior.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        # Entrada de texto
        self.entrada = tk.Entry(frame_inferior, font=("Segoe UI", 11))
        self.entrada.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entrada.bind("<Return>", lambda e: self._enviar_texto())
        
        # Botón enviar
        self.boton_enviar = tk.Button(
            frame_inferior,
            text="Enviar",
            command=self._enviar_texto
        )
        self.boton_enviar.pack(side=tk.LEFT, padx=(5, 0))
        
        # Botón grabar
        self.boton_grabar = tk.Button(
            frame_inferior,
            text="🎤 Grabar",
            command=self._grabar
        )
        self.boton_grabar.pack(side=tk.LEFT, padx=(5, 0))
    
    def _enviar_texto(self):
        """Procesa el envío de texto."""
        if self.callback_enviar_texto:
            self.callback_enviar_texto()
    
    def _grabar(self):
        """Procesa el toggle de grabación."""
        if self.callback_grabar:
            self.callback_grabar()
    
    def obtener_texto_entrada(self) -> str:
        """Obtiene el texto de la entrada."""
        return self.entrada.get().strip()
    
    def limpiar_entrada(self):
        """Limpia la entrada de texto."""
        self.entrada.delete(0, tk.END)
    
    def mostrar_mensaje(self, quien: str, texto: str):
        """Muestra un mensaje en el chat.
        
        Args:
            quien: Quién envía el mensaje (Vos, Aibby, Sistema, Error)
            texto: Contenido del mensaje
        """
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"{quien}: {texto}\n\n")
        self.chat_area.config(state="disabled")
        self.chat_area.see(tk.END)
    
    def cambiar_modelo_label(self, modelo: str):
        """Actualiza el label del modelo activo."""
        self.modelo_label.config(text=f"⚙️ Modelo activo: {modelo}")
    
    def iniciar_cooldown(self, segundos: int):
        """Inicia el cooldown visual."""
        self.boton_enviar.config(state="disabled")
        self.boton_grabar.config(state="disabled")
        self.cooldown_label.config(text=f"⏳ Aibby está en cooldown · {segundos} s restantes")
    
    def actualizar_cooldown(self, segundos: int):
        """Actualiza el contador de cooldown."""
        if segundos > 0:
            self.cooldown_label.config(text=f"⏳ Aibby está en cooldown · {segundos} s restantes")
        else:
            self.finalizar_cooldown()
    
    def finalizar_cooldown(self):
        """Finaliza el cooldown."""
        self.cooldown_label.config(text="🟢 Aibby disponible")
        self.boton_enviar.config(state="normal")
        self.boton_grabar.config(state="normal")
    
    def cambiar_estado_grabacion(self, grabando: bool):
        """Cambia el estado visual del botón de grabación."""
        if grabando:
            self.boton_grabar.config(text="⏹ Detener", bg="red")
        else:
            self.boton_grabar.config(text="🎤 Grabar", bg="SystemButtonFace")
    
    def es_cooldown_activo(self) -> bool:
        """Verifica si hay cooldown activo (por el estado del botón)."""
        return self.boton_enviar.cget("state") == "disabled"
    
    def ejecutar(self):
        """Inicia el loop de la interfaz."""
        self.ventana.mainloop()
    
    def agendar_en_ventana(self, funcion, delay_ms=0):
        """Agenda una función para ejecutarse en el hilo de Tkinter.
        
        Args:
            funcion: Función a ejecutar
            delay_ms: Delay en milisegundos
        """
        self.ventana.after(delay_ms, funcion)
