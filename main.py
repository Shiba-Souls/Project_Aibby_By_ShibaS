import os
import sys
from dotenv import load_dotenv
from src.core.config import Config
from src.ui.setup_ui import SetupWindow

def main():
    # --- RUTA ABSOLUTA AL EJECUTABLE ---
    # Si estamos en un exe compilado, usamos la carpeta del ejecutable
    if getattr(sys, 'frozen', False):
        ruta_base = os.path.dirname(sys.executable)
    else:
        ruta_base = os.path.dirname(os.path.abspath(__file__))
    
    archivo_env = os.path.join(ruta_base, ".env")
    
    # Cargamos el .env usando la ruta completa
    load_dotenv(archivo_env, override=True)
    
    # 1. Comprobar si ya existe la clave
    api_key = Config.obtener_api_key()

    if not api_key:
        setup = SetupWindow()
        setup.mainloop()
        
        # Volvemos a intentar cargar después del setup
        load_dotenv(archivo_env, override=True)
        api_key = Config.obtener_api_key()
        
        if not api_key:
            return

    from src.ui.uibby import Uibby
    app = Uibby()
    app.mainloop()

if __name__ == "__main__":
    main()