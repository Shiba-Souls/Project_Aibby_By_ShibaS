"""Módulo de búsqueda de archivos en el sistema."""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import (
    EXTENSIONES_RELEVANTES, LIMITE_ARCHIVOS_BUSQUEDA, LIMITE_ARCHIVOS_MOSTRAR
)
from utils import (
    obtener_carpetas_usuario, obtener_unidades_disponibles,
    es_carpeta_ignorada, es_archivo_oculto_o_sistema
)
from utils import FileSearchError


def buscar_archivos(carpetas_raiz: list, limite: int = LIMITE_ARCHIVOS_BUSQUEDA) -> list:
    """Busca archivos relevantes en las carpetas especificadas.
    
    Args:
        carpetas_raiz: Lista de rutas base donde buscar
        limite: Máximo de archivos a retornar
        
    Returns:
        Lista de rutas de archivos encontrados
    """
    resultados = []
    vistos = set()
    
    for raiz in carpetas_raiz:
        if not os.path.exists(raiz):
            continue
            
        try:
            for carpeta_actual, subcarpetas, archivos in os.walk(raiz):
                # Filtrar carpetas ignoradas
                subcarpetas[:] = [d for d in subcarpetas if not es_carpeta_ignorada(d)]

                for nombre_archivo in archivos:
                    ext = os.path.splitext(nombre_archivo)[1].lower()
                    if ext not in EXTENSIONES_RELEVANTES:
                        continue

                    ruta_completa = os.path.join(carpeta_actual, nombre_archivo)

                    # Evitar duplicados
                    ruta_normalizada = os.path.normcase(os.path.abspath(ruta_completa))
                    if ruta_normalizada in vistos:
                        continue
                    vistos.add(ruta_normalizada)

                    # Ignorar archivos ocultos/sistema
                    if es_archivo_oculto_o_sistema(ruta_completa):
                        continue

                    resultados.append(ruta_completa)
                    if len(resultados) >= limite:
                        return resultados
        except PermissionError:
            # Saltar carpetas sin permisos
            continue
        except Exception as e:
            print(f"Error buscando en {raiz}: {e}")
            continue
            
    return resultados


def buscar_por_palabras_clave(archivos: list, palabras_clave: list) -> list:
    """Filtra archivos que coinciden con las palabras clave.
    
    Args:
        archivos: Lista de rutas de archivos
        palabras_clave: Palabras a buscar en los nombres
        
    Returns:
        Lista de archivos que coinciden
    """
    coincidencias = [
        f for f in archivos
        if any(palabra in os.path.basename(f).lower() for palabra in palabras_clave)
    ]
    return coincidencias


def obtener_archivos_del_sistema(limite: int = LIMITE_ARCHIVOS_BUSQUEDA) -> list:
    """Obtiene todos los archivos relevantes del sistema."""
    carpetas = obtener_carpetas_usuario() + obtener_unidades_disponibles()
    return buscar_archivos(carpetas, limite=limite)


def buscar_archivos_por_consulta(consulta: str) -> list:
    """Busca archivos que coincidan con una consulta de usuario.
    
    Args:
        consulta: Texto de búsqueda del usuario
        
    Returns:
        Lista de rutas de archivos relevantes
    """
    try:
        # Obtener todos los archivos
        todos_archivos = obtener_archivos_del_sistema(LIMITE_ARCHIVOS_BUSQUEDA)
        
        if not todos_archivos:
            raise FileSearchError("No se encontraron archivos en el sistema.")
        
        # Extraer palabras clave
        palabras_clave = [p for p in consulta.lower().split() if len(p) > 2]
        
        if not palabras_clave:
            raise FileSearchError("La consulta no contiene palabras válidas para buscar.")
        
        # Buscar coincidencias
        coincidencias = buscar_por_palabras_clave(todos_archivos, palabras_clave)
        
        return coincidencias[:LIMITE_ARCHIVOS_MOSTRAR]
        
    except Exception as e:
        raise FileSearchError(f"Error durante la búsqueda: {str(e)}")


def formatear_resultados_busqueda(archivos: list) -> str:
    """Formatea la lista de archivos como texto para mostrar al usuario.
    
    Args:
        archivos: Lista de rutas de archivos
        
    Returns:
        String con formato de los archivos
    """
    if not archivos:
        return "No encontré archivos que coincidan con esa búsqueda."
    
    return "\n".join(archivos)
