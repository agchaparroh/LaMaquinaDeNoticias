import os
from groq import Groq, APIConnectionError, RateLimitError, APIStatusError
from loguru import logger

# Importar configuración usando import relativo
from ..config import settings
# Importar excepciones personalizadas y decoradores
from ..utils.error_handling import (
    ValidationError, GroqAPIError, ErrorPhase,
    retry_groq_api
)

class GroqService:
    """
    Servicio para interactuar con la API de Groq para generación de texto.
    """
    def __init__(self, api_key: str = None, model_id: str = None):
        """
        Inicializa el cliente Groq.
        Args:
            api_key (str, optional): Clave API de Groq. Si no se provee, se toma de `settings.GROQ_API_KEY`.
            model_id (str, optional): ID del modelo a usar. Si no se provee, se toma de `settings.GROQ_DEFAULT_MODEL_ID` o un valor por defecto.
        """
        try:
            self.api_key = api_key or settings.GROQ_API_KEY
        except AttributeError:
            logger.error("GROQ_API_KEY no encontrada en settings.py. Asegúrate de que esté definida.")
            raise ValidationError(
                message="GROQ_API_KEY es requerida y no se encontró en la configuración.",
                validation_errors=[{"field": "GROQ_API_KEY", "error": "Missing in settings"}],
                phase=ErrorPhase.GENERAL
            )
        
        if not self.api_key:
            logger.error("GROQ_API_KEY está vacía en la configuración.")
            raise ValidationError(
                message="GROQ_API_KEY no puede estar vacía.",
                validation_errors=[{"field": "GROQ_API_KEY", "error": "Empty value"}],
                phase=ErrorPhase.GENERAL
            )

        self.client = Groq(api_key=self.api_key)
        
        _hardcoded_default_model = "llama3-8b-8192"
        try:
            self.model_id = model_id or settings.GROQ_DEFAULT_MODEL_ID
        except AttributeError:
            logger.warning(f"GROQ_DEFAULT_MODEL_ID no encontrada en settings. Usando valor por defecto: {_hardcoded_default_model}")
            self.model_id = model_id or _hardcoded_default_model
        
        logger.info(f"GroqService inicializado. Modelo por defecto: {self.model_id}")

    @retry_groq_api(max_attempts=2, wait_seconds=5)  # Según documentación: máximo 2 reintentos
    def _create_chat_completion_with_retry(self, messages: list, model: str, max_tokens: int, temperature: float, timeout: float):
        logger.debug(f"Intentando llamada a Groq API. Modelo: {model}, Timeout: {timeout}s")
        try:
            return self.client.chat.completions.create(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
        except APIConnectionError as e:
            logger.error(f"Error de conexión con Groq API: {e}")
            # El decorador @retry_groq_api manejará la conversión a GroqAPIError
            raise
        except RateLimitError as e:
            logger.warning(f"Límite de tasa de Groq API excedido: {e}. Reintentando según configuración.")
            # El decorador @retry_groq_api manejará la conversión a GroqAPIError
            raise
        except APIStatusError as e:
            logger.error(f"Error de estado de Groq API: {e.status_code} - {e.response}. Mensaje: {e.message}")
            # El decorador @retry_groq_api manejará la conversión a GroqAPIError
            raise
        except Exception as e:
            logger.error(f"Error inesperado durante la llamada a Groq API: {e}")
            # El decorador @retry_groq_api manejará la conversión a GroqAPIError
            raise

    def send_prompt(self, prompt: str, system_prompt: str = None, model_id: str = None, 
                    max_tokens: int = None, temperature: float = None, timeout: float = None) -> str | None:
        """
        Envía un prompt a la API de Groq y retorna la respuesta del modelo.

        Args:
            prompt (str): El prompt del usuario.
            system_prompt (str, optional): Prompt del sistema para guiar al modelo.
            model_id (str, optional): ID del modelo a usar. Sobrescribe el modelo por defecto del servicio.
            max_tokens (int, optional): Máximo número de tokens a generar. Usa `settings.GROQ_DEFAULT_MAX_TOKENS` o un valor por defecto.
            temperature (float, optional): Temperatura para la generación. Usa `settings.GROQ_DEFAULT_TEMPERATURE` o un valor por defecto.
            timeout (float, optional): Timeout para la solicitud. Usa `settings.GROQ_DEFAULT_TIMEOUT` o un valor por defecto.

        Returns:
            str | None: La respuesta del modelo, o None si ocurre un error después de los reintentos.
        """
        current_model = model_id or self.model_id
        logger.info(f"Enviando prompt a Groq. Modelo: {current_model}")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Obtener valores por defecto de settings o usar valores fijos si no están en settings
        _s_max_tokens, _s_temp, _s_timeout = 1024, 0.7, 60.0 # Fallbacks hardcodeados
        try:
            current_max_tokens = max_tokens if max_tokens is not None else settings.GROQ_DEFAULT_MAX_TOKENS
        except AttributeError:
            current_max_tokens = max_tokens if max_tokens is not None else _s_max_tokens
            if max_tokens is None: logger.debug(f"GROQ_DEFAULT_MAX_TOKENS no en settings, usando {_s_max_tokens}")

        try:
            current_temperature = temperature if temperature is not None else settings.GROQ_DEFAULT_TEMPERATURE
        except AttributeError:
            current_temperature = temperature if temperature is not None else _s_temp
            if temperature is None: logger.debug(f"GROQ_DEFAULT_TEMPERATURE no en settings, usando {_s_temp}")

        try:
            current_timeout = timeout if timeout is not None else settings.GROQ_DEFAULT_TIMEOUT
        except AttributeError:
            current_timeout = timeout if timeout is not None else _s_timeout
            if timeout is None: logger.debug(f"GROQ_DEFAULT_TIMEOUT no en settings, usando {_s_timeout}")

        try:
            chat_completion = self._create_chat_completion_with_retry(
                messages=messages,
                model=current_model,
                max_tokens=current_max_tokens,
                temperature=current_temperature,
                timeout=current_timeout
            )
            response_content = chat_completion.choices[0].message.content
            logger.info("Respuesta recibida exitosamente de Groq.")
            logger.debug(f"Respuesta de Groq (primeros 100 chars): {response_content[:100]}...")
            return response_content
        except GroqAPIError as e:
            # Ya es una excepción personalizada del decorador, re-lanzar con fase correcta
            raise GroqAPIError(
                message=e.message,
                phase=ErrorPhase.GENERAL,  # Se debe establecer en el contexto de uso
                retry_count=e.details.get('retry_count', 0),
                timeout_seconds=e.details.get('timeout_seconds', 60)
            ) from e
        except Exception as e:
            logger.error(f"Fallo al enviar prompt a Groq: {e}")
            # Convertir a GroqAPIError para manejo consistente
            raise GroqAPIError(
                message=f"Error al enviar prompt a Groq: {str(e)}",
                phase=ErrorPhase.GENERAL,
                retry_count=0,
                timeout_seconds=60
            ) from e

# Método de compatibilidad para código existente
def create_groq_service(api_key: str = None, model_id: str = None) -> 'GroqService':
    """
    Factory method para crear instancias de GroqService.
    Mantiene compatibilidad con código existente.
    
    Args:
        api_key: API key de Groq (opcional)
        model_id: ID del modelo a usar (opcional)
        
    Returns:
        GroqService: Instancia configurada del servicio
    """
    return GroqService(api_key=api_key, model_id=model_id)
