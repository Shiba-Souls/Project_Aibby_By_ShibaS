"""Excepciones personalizadas de Aibby."""


class AibbyException(Exception):
    """Excepción base de Aibby."""
    pass


class APIError(AibbyException):
    """Error relacionado con la API de Gemini."""
    pass


class AudioError(AibbyException):
    """Error relacionado con audio (grabación/reproducción)."""
    pass


class FileSearchError(AibbyException):
    """Error relacionado con búsqueda de archivos."""
    pass


class RateLimitError(APIError):
    """Error de límite de cuota (429)."""
    pass


class ConfigError(AibbyException):
    """Error en configuración."""
    pass
