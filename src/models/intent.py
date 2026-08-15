class Intent:
    PALABRAS_BUSQUEDA = ["busca", "buscá", "encontr", "dónde está", "donde esta"]
    PALABRAS_ABRIR = ["abre", "abrí", "abrir", "ejecuta", "ejecutá"]
    PALABRAS_LEER = ["lee", "leé", "leer", "qué dice", "contenido"]

    @staticmethod
    def detectar_intencion(texto):
        texto_lower = texto.lower()
        
        if any(p in texto_lower for p in Intent.PALABRAS_ABRIR):
            return "ABRIR_ARCHIVO"
        if any(p in texto_lower for p in Intent.PALABRAS_LEER):
            return "LEER_ARCHIVO"
        if any(p in texto_lower for p in Intent.PALABRAS_BUSQUEDA):
            return "BUSCAR_ARCHIVO"
            
        return "CONVERSACION"