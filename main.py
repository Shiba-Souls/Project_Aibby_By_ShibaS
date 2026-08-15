import os
from dotenv import load_dotenv
from src.core.config import Config
from src.ui.setup_ui import SetupWindow

def main():
    # 1. Comprobar si ya existe la clave
    api_key = Config.obtener_api_key()

    # 2. Si no existe, abrir Setup primero
    if not api_key:
        setup = SetupWindow()
        setup.mainloop()
        
        # Recomprobar si la guardó correctamente
        api_key = Config.obtener_api_key()
        if not api_key:
            print("Cierre de aplicación: Se requiere una API Key para iniciar Aibby.")
            return

    # 3. RECIÉN ACÁ importamos/instanciamos Uibby
    from src.ui.uibby import Uibby
    app = Uibby()
    app.mainloop()

if __name__ == "__main__":
    main()