import os
import winreg
import ctypes

CARPETAS_IGNORADAS = {
    "windows", "program files", "program files (x86)", "programdata",
    "$recycle.bin", "system volume information", "appdata",
    "windowsapps", "msocache", "recovery", "perflogs",
    "node_modules", "__pycache__", "venv", "$sysreset"
}

EXTENSIONES_RELEVANTES = {
    ".docx", ".doc", ".pdf", ".txt", ".xlsx", ".xls", ".pptx", ".ppt", ".odt", ".csv",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".flac",
    ".exe", ".lnk",
    ".zip", ".rar", ".7z",
}

FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3

class FileManager:
    @staticmethod
    def _leer_carpeta_registro(nombre_valor, fallback):
        """Lee la ruta real de una carpeta conocida de Windows desde el registro."""
        try:
            clave = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            )
            valor, _ = winreg.QueryValueEx(clave, nombre_valor)
            winreg.CloseKey(clave)
            return os.path.expandvars(valor)
        except Exception:
            return fallback

    @staticmethod
    def obtener_carpetas_usuario():
        """Devuelve las rutas reales de las carpetas principales."""
        home = os.path.expanduser("~")
        return [
            FileManager._leer_carpeta_registro("Desktop", os.path.join(home, "Desktop")),
            FileManager._leer_carpeta_registro("Personal", os.path.join(home, "Documents")),
            FileManager._leer_carpeta_registro("{374DE290-123F-4565-9164-39C4925E467B}", os.path.join(home, "Downloads")),
            FileManager._leer_carpeta_registro("My Pictures", os.path.join(home, "Pictures")),
            FileManager._leer_carpeta_registro("My Video", os.path.join(home, "Videos")),
        ]

    @staticmethod
    def obtener_unidades_disponibles():
        """Obtiene letras de discos fijos o extraíbles."""
        unidades = []
        try:
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for i in range(26):
                if not (bitmask & (1 << i)):
                    continue
                letra = f"{chr(65 + i)}:\\"
                tipo = ctypes.windll.kernel32.GetDriveTypeW(letra)
                if tipo in (DRIVE_REMOVABLE, DRIVE_FIXED):
                    unidades.append(letra)
        except Exception:
            pass
        return unidades

    @staticmethod
    def _es_carpeta_ignorada(nombre_carpeta):
        return nombre_carpeta.lower() in CARPETAS_IGNORADAS or nombre_carpeta.startswith(".")

    @staticmethod
    def _es_archivo_oculto_o_sistema(ruta_completa):
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(ruta_completa)
            if attrs == -1:
                return False
            return bool(attrs & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM))
        except Exception:
            return False

    @staticmethod
    def buscar_archivos(carpetas_raiz, limite=2000):
        """Busca archivos relevantes en las carpetas dadas."""
        resultados = []
        vistos = set()
        for raiz in carpetas_raiz:
            if not os.path.exists(raiz):
                continue
            for carpeta_actual, subcarpetas, archivos in os.walk(raiz):
                subcarpetas[:] = [d for d in subcarpetas if not FileManager._es_carpeta_ignorada(d)]

                for nombre_archivo in archivos:
                    ext = os.path.splitext(nombre_archivo)[1].lower()
                    if ext not in EXTENSIONES_RELEVANTES:
                        continue

                    ruta_completa = os.path.join(carpeta_actual, nombre_archivo)
                    ruta_normalizada = os.path.normcase(os.path.abspath(ruta_completa))
                    
                    if ruta_normalizada in vistos:
                        continue
                    vistos.add(ruta_normalizada)

                    if FileManager._es_archivo_oculto_o_sistema(ruta_completa):
                        continue

                    resultados.append(ruta_completa)
                    if len(resultados) >= limite:
                        return resultados
        return resultados
    @staticmethod
    def abrir_archivo(ruta):
        """Abre un archivo con su programa predeterminado en Windows."""
        try:
            if os.path.exists(ruta):
                os.startfile(ruta)
                return True, f"Abriendo {os.path.basename(ruta)}"
            return False, "El archivo no existe."
        except Exception as e:
            return False, f"No pude abrir el archivo: {e}"

    @staticmethod
    def leer_archivo(ruta):
        """Lee el contenido de un archivo de texto/código."""
        try:
            with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                return True, f.read()
        except Exception as e:
            return False, f"No pude leer el archivo: {e}"

    @staticmethod
    def escribir_archivo(ruta, contenido):
        """Sobrescribe un archivo (usar con cuidado)."""
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(contenido)
            return True, "Archivo guardado exitosamente."
        except Exception as e:
            return False, f"No pude escribir en el archivo: {e}"