# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller para Aibby (beta 1.6.2) — modo ONEDIR
# Compilar con: pyinstaller Aibby.spec
# Salida: dist/Aibby/Aibby.exe + carpeta con dependencias al lado
# (base.pt y ffmpeg.exe NO se empaquetan: el usuario los coloca en dist/Aibby/ a mano,
#  siguiendo los links de descarga que ya muestra setup_ui.py)

from PyInstaller.utils.hooks import collect_data_files

# --- Archivos de datos a empaquetar (solo ícono + assets imprescindibles) ---
datas = [
    ('aibby.ico', '.'),                 # Ícono, usado en runtime por Config.obtener_ruta_recurso
]
datas += collect_data_files('customtkinter')  # Temas JSON y assets de CTk
datas += collect_data_files('whisper')         # mel_filters.npz y tokenizers de Whisper

# --- Imports que PyInstaller no detecta solo (imports dinámicos) ---
hiddenimports = [
    'customtkinter',
    'google.genai',
    'google.genai.types',
    'whisper',
    'tiktoken_ext.openai_public',   # sin esto, Whisper falla al transcribir (no al compilar)
    'tiktoken_ext',
]

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# En ONEDIR, el EXE no lleva binarios ni datas adentro: eso lo arma COLLECT
# como archivos sueltos en la carpeta de salida (dist/Aibby/).
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Aibby',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # False = sin consola negra detrás (--windowed)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='aibby.ico',        # Ícono del .exe (Explorador / taskbar)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Aibby',
)
