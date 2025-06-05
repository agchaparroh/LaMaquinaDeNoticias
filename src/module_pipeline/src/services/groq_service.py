import os
from groq import Groq, APIConnectionError, RateLimitError, APIStatusError
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from loguru import logger

# Importar configuración usando import relativo
from ..config import settings

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
            raise ValueError("GROQ_API_KEY es requerida y no se encontró en la configuración.")
        
        if not self.api_key:
            logger.error("GROQ_API_KEY está vacía en la configuración.")
            raise ValueError("GROQ_API_KEY no puede estar vacía.")

        self.client = Groq(api_key=self.api_key)
        
        _hardcoded_default_model = "llama3-8b-8192"
        try:
            self.model_id = model_id or settings.GROQ_DEFAULT_MODEL_ID
        except AttributeError:
            logger.warning(f"GROQ_DEFAULT_MODEL_ID no encontrada en settings. Usando valor por defecto: {_hardcoded_default_model}")
            self.model_id = model_id or _hardcoded_default_model
        
        logger.info(f"GroqService inicializado. Modelo por defecto: {self.model_id}")

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=60), # Espera exponencial: 2s, 4s, ..., hasta 60s
        stop=stop_after_attempt(5), # Reintentar hasta 5 veces
        reraise=True # Volver a lanzar la última excepción si todos los reintentos fallan
    )
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
            raise
        except RateLimitError as e:
            logger.warning(f"Límite de tasa de Groq API excedido: {e}. Reintentando según configuración de tenacity.")
            raise
        except APIStatusError as e:
            logger.error(f"Error de estado de Groq API: {e.status_code} - {e.response}. Mensaje: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado durante la llamada a Groq API: {e}")
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
        except RetryError as e: 
            logger.error(f"Fallo al obtener respuesta de Groq después de múltiples reintentos: {e.last_attempt.exception()}")
            return None
        except Exception as e:
            logger.error(f"Fallo al enviar prompt a Groq: {e}")
            return None

# Ejemplo de cómo se podría configurar loguru en el punto de entrada de la aplicación (ej: main.py)
# if __name__ == "__main__":
#     logger.remove() # Remover el handler por defecto
#     logger.add(sys.stderr, level="INFO") # Agregar un handler para stderr con nivel INFO
#     logger.add("file_{time}.log", rotation="500 MB", level="DEBUG") # Log a archivo con rotación y nivel DEBUG

#     # Para probar (asegúrate de que settings.py y GROQ_API_KEY estén configurados):
#     # from src.config.settings import settings # Necesitarías configurar esto
#     # settings.GROQ_API_KEY = os.environ.get("GROQ_API_KEY") # Ejemplo de carga
#     # settings.GROQ_DEFAULT_MODEL_ID = "mixtral-8x7b-32768"
     
#     if not os.environ.get("GROQ_API_KEY"):
#         print("Por favor, establece la variable de entorno GROQ_API_KEY para ejecutar este ejemplo.")
#     else:
#         # Simular que settings tiene la clave API para prueba local sin settings.py completo
#         class MockSettings:
#             GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
#             GROQ_DEFAULT_MODEL_ID = "mixtral-8x7b-32768"
#             # GROQ_DEFAULT_MAX_TOKENS = 200 # Descomentar para probar

#         # Temporalmente sobreescribir settings para la prueba
#         original_settings = settings
#         settings = MockSettings()

#         groq_service = GroqService()
#         test_prompt = "¿Cuál es la capital de Francia?"
#         logger.info(f"Enviando prompt de prueba: {test_prompt}")
#         response = groq_service.send_prompt(test_prompt)
#         if response:
#             logger.info(f"Respuesta del prompt de prueba: {response}")
#         else:
#             logger.error("No se recibió respuesta para el prompt de prueba.")
        
#         # Restaurar settings originales
#         settings = original_settings
