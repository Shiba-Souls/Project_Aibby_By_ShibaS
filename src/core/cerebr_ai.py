import os
from src.services.ai_call import AICall
from src.utils.file_manager import FileManager
from src.models.intent import Intent
from src.services.talktative import Talktative
from src.services.paiper_tts import PaiperTTS

class CerebrAI:
    def __init__(self):
        self.ai_service = AICall()          # texto -> texto (Gemini, solo texto)
        self.audio_service = Talktative()   # audio -> texto (Whisper, oídos)
        self.tts_service = PaiperTTS()      # texto -> audio (Piper, voz)
        self.ultimos_archivos_encontrados = []

    def procesar_mensaje(self, mensaje):
        intencion = Intent.detectar_intencion(mensaje)

        if intencion == "BUSCAR_ARCHIVO":
            return self._manejar_busqueda_archivos(mensaje)
        elif intencion == "ABRIR_ARCHIVO":
            return self._manejar_abrir_archivo(mensaje)
        elif intencion == "LEER_ARCHIVO":
            return self._manejar_leer_archivo(mensaje)
        else:
            return self._manejar_conversacion(mensaje)

    def _buscar_archivo_por_nombre(self, consulta):
        palabras_ignoradas = Intent.PALABRAS_ABRIR + Intent.PALABRAS_LEER + [
            "archivo", "documento", "texto", "carpeta", "el", "la", "los", "las", 
            "un", "una", "por", "favor", "aibby", "eso", "lo"
        ]
        
        palabras_clave = [
            p.lower() for p in consulta.split() 
            if len(p) > 2 and p.lower() not in palabras_ignoradas
        ]

        # --- MAGIA 1: Si dice "ábrelo" y hay algo en memoria, lo abre directo ---
        if not palabras_clave and self.ultimos_archivos_encontrados:
            return self.ultimos_archivos_encontrados[0]
            
        # --- MAGIA 2: Buscar primero en la memoria a corto plazo ---
        if self.ultimos_archivos_encontrados and palabras_clave:
            coincidencias_memoria = [
                f for f in self.ultimos_archivos_encontrados 
                if all(p in os.path.basename(f).lower() for p in palabras_clave)
            ]
            if coincidencias_memoria:
                return coincidencias_memoria[0] # ¡Lo encontró en caché al instante!

        # --- MAGIA 3: Si no estaba en memoria, recién ahí buscamos en toda la PC ---
        if not palabras_clave:
            return None # Faltan datos para buscar
            
        carpetas = FileManager.obtener_carpetas_usuario() + FileManager.obtener_unidades_disponibles()
        archivos = FileManager.buscar_archivos(carpetas, limite=2000)
        
        coincidencias = [
            f for f in archivos 
            if all(p in os.path.basename(f).lower() for p in palabras_clave)
        ]
        
        return coincidencias[0] if coincidencias else None

    def _manejar_abrir_archivo(self, mensaje):
        archivo = self._buscar_archivo_por_nombre(mensaje)
        if not archivo:
            return "No pude encontrar el archivo que me pediste abrir."
        
        exito, resultado = FileManager.abrir_archivo(archivo)
        return resultado if exito else f"Error al abrir: {resultado}"

    def _manejar_leer_archivo(self, mensaje):
        archivo = self._buscar_archivo_por_nombre(mensaje)
        if not archivo:
            return "No pude encontrar el archivo para leer."
        
        exito, contenido = FileManager.leer_archivo(archivo)
        if not exito:
            return f"Error al leer: {contenido}"
        
        # Le enviamos el contenido a Gemini para que lo resuma o lo explique
        prompt = f"El usuario quiere leer este archivo. Resumilo o explicalo:\n\n{contenido[:2000]}" # Límite para no saturar
        return self.ai_service.enviar_mensaje(prompt)

    
    def _manejar_conversacion(self, mensaje):
        """Delega una charla normal a Gemini."""
        return self.ai_service.enviar_mensaje(mensaje)

    def _manejar_busqueda_archivos(self, consulta):
        """Busca archivos en la PC y le pide a Gemini que lo cuente de forma natural."""
        
        # 1. Definir dónde buscar (carpetas de usuario + discos rígidos/pendrives)
        carpetas_usuario = FileManager.obtener_carpetas_usuario()
        unidades = FileManager.obtener_unidades_disponibles()
        carpetas_raiz = carpetas_usuario + unidades

        # 2. Ejecutar la búsqueda en el disco (el límite evita que se cuelgue la PC)
        todos_archivos = FileManager.buscar_archivos(carpetas_raiz, limite=2000)

        # 3. Filtrar los archivos encontrados usando las palabras del usuario
        # (ignoramos palabras de 1 o 2 letras como "el", "la", "de")
        palabras_clave = [p.lower() for p in consulta.split() if len(p) > 2]
        
        coincidencias = [
            f for f in todos_archivos
            if any(palabra in os.path.basename(f).lower() for palabra in palabras_clave)
        ]
        # --- GUARDAMOS EN MEMORIA --
        self.ultimos_archivos_encontrados = coincidencias

        # 4. Si no hay suerte...
        if not coincidencias:
            return "No encontré archivos que coincidan con esa búsqueda en tu equipo."

        # 5. Si encontramos algo, armamos un prompt "oculto" para Gemini
        # Tomamos solo los primeros 30 para no pasarnos del límite de tokens
        lista_texto = "\n".join(coincidencias[:30])
        
        prompt_sistema = (
            f"El usuario pidió buscar: '{consulta}'\n\n"
            f"Estos son los archivos encontrados en su PC que podrían coincidir:\n"
            f"{lista_texto}\n\n"
            "Respondé de forma breve y natural, como Aibby, mencionando qué encontraste "
            "(nombre del archivo y en qué carpeta está)."
        )

        # 6. Le pasamos el contexto a Gemini para que arme la respuesta final
        return self.ai_service.enviar_mensaje(prompt_sistema)