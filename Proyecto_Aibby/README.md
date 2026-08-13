# Aibby - Asistente Personal de IA

Aibby es un asistente personal de IA modular y escalable basado en Gemini API, con interfaz gráfica, reconocimiento de voz y búsqueda de archivos inteligente.

## 📋 Requisitos

- Python 3.12+
- Windows (para los módulos de Windows registry y audio)
- Una API key de Gemini (obtén una en [AI Studio](https://aistudio.google.com))

## 🚀 Instalación

1. **Crea un entorno virtual:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura la API key:**
   - Crea un archivo `.env` en la carpeta raíz
   - Agrega tu API key:
   ```
   API_KEY=tu_api_key_aqui
   ```

## 📂 Estructura del proyecto

```
Proyecto Aibby/
├── main.py                  # Punto de entrada
├── config.py               # Configuración centralizada
├── requirements.txt        # Dependencias
├── .env                    # Variables de entorno (NO commitar)
├── .gitignore             # Archivos a ignorar en git
├── README.md              # Este archivo
│
├── core/                   # Módulos principales
│   ├── __init__.py
│   ├── UIbby.py           # Interfaz gráfica
│   ├── talkatative.py     # Audio (grabación + TTS)
│   └── file_findersearch.py # Búsqueda de archivos
│
├── models/                # Interacción con LLMs
│   ├── __init__.py
│   ├── models_gemini.py   # API de Gemini
│   └── fallback.py        # Cambio de modelos + cooldown
│
├── utils/                 # Utilidades
│   ├── __init__.py
│   ├── utils.py          # Funciones auxiliares
│   └── exceptions.py     # Excepciones personalizadas
│
└── data/                 # Datos y logs
    ├── logs/
    └── cache/
```

## 🎯 Características

- ✅ **Interfaz gráfica** con Tkinter
- ✅ **Chat de voz** (grabación y reproducción)
- ✅ **Búsqueda inteligente de archivos** en el sistema
- ✅ **Fallback automático** entre modelos de Gemini
- ✅ **Cooldown visual** cuando la API alcanza límites
- ✅ **Historial de contexto** preservado entre modelos
- ✅ **Arquitectura modular** y extensible

## 🎮 Uso

Ejecuta:
```bash
python main.py
```

Luego interactúa con Aibby a través de:
- **Texto**: Escribe mensajes en el campo de entrada
- **Voz**: Presiona 🎤 para grabar y enviar audio
- **Búsqueda**: Usa palabras como "busca", "encontr", "dónde está" para buscar archivos

## 🏗️ Arquitectura

### Módulos principales

**`main.py`** - Orquestador central
- Instancia todos los módulos
- Maneja callbacks y flujos de datos
- Gestiona threading para operaciones async

**`core/UIbby.py`** - Interfaz gráfica
- Tkinter UI con chat, entrada y botones
- Manejo de estado visual (cooldown, grabación)

**`core/talkatative.py`** - Audio
- `GrabadorAudio`: Captura de micrófono
- `TextoAVoz`: Reproducción de voz
- Procesamiento de archivos WAV

**`core/file_findersearch.py`** - Búsqueda de archivos
- Escaneo inteligente del sistema
- Filtrado por extensiones y carpetas ignoradas
- Integración con Gemini para resultados naturales

**`models/models_gemini.py`** - API de Gemini
- Manejo de chats y mensajes
- Generación de contenido

**`models/fallback.py`** - Gestión de modelos
- Cambio automático entre modelos
- Detección y manejo de rate limits (429)
- Cooldown visual bloqueante

**`utils/`** - Utilidades
- Funciones auxiliares (Windows registry, validación)
- Excepciones personalizadas

## ⚙️ Configuración

Edita `config.py` para personalizar:

```python
# Modelos
MODELO_PRINCIPAL = "gemini-3.5-flash"
MODELO_LIGERO = "gemini-3.1-flash-lite"

# Audio
SAMPLE_RATE = 16000
TTS_RATE = 175

# UI
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 650
```

## 🐛 Troubleshooting

**ImportError: "could not be resolved"**
- Verifica que existan todos los `__init__.py`
- Asegúrate de que `.env` esté en la carpeta raíz

**Error de API key**
- Comprueba que `.env` contiene: `API_KEY=tu_clave`
- Verifica que no haya espacios extra

**Audio no funciona**
- Requiere Windows con drivers de audio correctos
- Comprueba que `sounddevice` se instaló correctamente

**No encuentra archivos**
- Algunos archivos pueden estar ocultos/protegidos
- Las búsquedas ignoran carpetas de sistema intencionalmente

## 📝 Próximos pasos

- [ ] Integración con Gemini Live API para voz en tiempo real
- [ ] Diseño visual mejorado de la UI
- [ ] Caching de búsquedas de archivos
- [ ] Historial persistente de conversaciones
- [ ] Configuración mediante UI

## 📄 Licencia

Uso personal. Made with ❤️ for Ezequiel.

---

¿Problemas? Revisa los logs en `data/logs/` o abre un issue.
