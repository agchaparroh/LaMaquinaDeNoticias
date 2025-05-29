# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import logging
import uuid
from datetime import datetime

# Importaciones para Tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log, RetryError
# Asumimos que supabase-py podría lanzar excepciones de red a través de 'requests' o similares.
# Si supabase-py tiene sus propias excepciones específicas para errores de API/red, impórtalas.
# Por ahora, usaremos una genérica y una personalizada.
from requests.exceptions import RequestException # Ejemplo, si aplica
import httpx # supabase-py usa httpx, por lo que sus excepciones de red serían relevantes

from .items import ArticuloInItem
from .utils.compression import compress_html
from .utils.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

# --- Configuración de Tenacity ---
DEFAULT_STOP_AFTER_ATTEMPT = 3
DEFAULT_WAIT_MULTIPLIER = 1
DEFAULT_WAIT_MIN = 2  # Segundos
DEFAULT_WAIT_MAX = 10 # Segundos

# --- Excepciones personalizadas para reintentos ---
class SupabaseNetworkError(Exception):
    """Para errores de red/conexión con Supabase que son reintentables."""
    pass

class SupabaseAPIError(Exception):
    """Para errores de la API de Supabase que podrían ser reintentables (ej. rate limits)."""
    pass

# Crear una tupla de excepciones reintentables
RETRYABLE_EXCEPTIONS = (
    SupabaseNetworkError,
    SupabaseAPIError,
    RequestException, # Si requests es usado indirectamente y relevante
    httpx.RequestError, # Errores de red de httpx
    httpx.TimeoutException # Timeouts de httpx
)
# --- Fin Configuración de Tenacity ---

class SupabaseStoragePipeline:
    def __init__(self, supabase_client: SupabaseClient, html_bucket_name: str):
        self.supabase_client = supabase_client
        self.html_bucket_name = html_bucket_name
        # Inicializar aquí para que esté disponible en los decoradores si se usan como self.stop_after_attempt
        self.stop_after_attempt = DEFAULT_STOP_AFTER_ATTEMPT
        self.wait_multiplier = DEFAULT_WAIT_MULTIPLIER
        self.wait_min = DEFAULT_WAIT_MIN
        self.wait_max = DEFAULT_WAIT_MAX

    @classmethod
    def from_crawler(cls, crawler):
        supabase_client = SupabaseClient()
        html_bucket_name = crawler.settings.get(
            'SUPABASE_STORAGE_BUCKET',
            'articulos_html_beta'
        )
        
        # Leer configuración de Tenacity desde settings.py si se desea, o usar defaults
        # Estos atributos se asignarán a la instancia en __init__ si se pasan aquí
        # o se pueden usar directamente desde cls si los decoradores se ajustan.
        # Por simplicidad, los atributos de instancia se usarán en los decoradores.
        stop_after_attempt_cfg = crawler.settings.getint('TENACITY_STOP_AFTER_ATTEMPT', DEFAULT_STOP_AFTER_ATTEMPT)
        wait_multiplier_cfg = crawler.settings.getint('TENACITY_WAIT_MULTIPLIER', DEFAULT_WAIT_MULTIPLIER)
        wait_min_cfg = crawler.settings.getint('TENACITY_WAIT_MIN', DEFAULT_WAIT_MIN)
        wait_max_cfg = crawler.settings.getint('TENACITY_WAIT_MAX', DEFAULT_WAIT_MAX)

        instance = cls(supabase_client, html_bucket_name)
        instance.stop_after_attempt = stop_after_attempt_cfg
        instance.wait_multiplier = wait_multiplier_cfg
        instance.wait_min = wait_min_cfg
        instance.wait_max = wait_max_cfg
        
        logger.info(
            f"SupabaseStoragePipeline initialized. HTML Bucket: {html_bucket_name}. "
            f"Tenacity: stop={instance.stop_after_attempt}, wait_min={instance.wait_min}, wait_max={instance.wait_max}"
        )
        return instance

    # Método auxiliar decorado para crear bucket
    # Usamos los atributos de instancia para la configuración de Tenacity
    def _get_retry_decorator(self):
        return retry(
            stop=stop_after_attempt(self.stop_after_attempt),
            wait=wait_exponential(multiplier=self.wait_multiplier, min=self.wait_min, max=self.wait_max),
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            before_sleep=before_sleep_log(logger, logging.WARNING)
        )

    def _ensure_bucket_exists_with_retry(self, bucket_name: str):
        decorated_func = self._get_retry_decorator()(self.__ensure_bucket_exists_logic)
        return decorated_func(bucket_name)

    def __ensure_bucket_exists_logic(self, bucket_name: str):
        logger.debug(f"Attempting to create/verify bucket: {bucket_name}")
        try:
            self.supabase_client.create_bucket_if_not_exists(bucket_name)
            logger.info(f"Supabase bucket '{bucket_name}' is ready.")
        except httpx.RequestError as e:
            logger.warning(f"Network error during bucket creation/verification for '{bucket_name}': {e}")
            raise SupabaseNetworkError(f"Network error for bucket '{bucket_name}': {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during bucket creation/verification for '{bucket_name}': {e}", exc_info=True)
            raise

    def open_spider(self, spider):
        logger.info(f"Opening spider {spider.name}. Ensuring Supabase bucket '{self.html_bucket_name}' exists.")
        try:
            self._ensure_bucket_exists_with_retry(self.html_bucket_name)
        except RetryError as e:
            logger.error(
                f"All attempts failed to create/verify Supabase bucket '{self.html_bucket_name}' "
                f"after {self.stop_after_attempt} attempts: {e}", exc_info=True
            )
            # from scrapy.exceptions import CloseSpider
            # raise CloseSpider(f"Failed to initialize Supabase bucket after retries: {self.html_bucket_name}")
        except Exception as e:
             logger.error(
                f"An unexpected, non-retryable error occurred in open_spider for bucket '{self.html_bucket_name}': {e}",
                exc_info=True
            )

    def close_spider(self, spider):
        logger.info(f"Closing spider {spider.name}. Closing Supabase client.")
        if hasattr(self.supabase_client, 'close') and callable(self.supabase_client.close):
            try:
                self.supabase_client.close()
            except Exception as e:
                logger.error(f"Error closing Supabase client: {e}", exc_info=True)

    # Métodos auxiliares para upload y upsert
    def _upload_to_storage_with_retry(self, bucket_name: str, file_path: str, file_content):
        decorated_func = self._get_retry_decorator()(self.__upload_to_storage_logic)
        return decorated_func(bucket_name, file_path, file_content)

    def __upload_to_storage_logic(self, bucket_name: str, file_path: str, file_content):
        logger.debug(f"Attempting to upload to storage: {bucket_name}/{file_path}")
        try:
            self.supabase_client.upload_to_storage(
                bucket_name=bucket_name,
                file_path=file_path,
                file_content=file_content
            )
        except httpx.RequestError as e:
            logger.warning(f"Network error during storage upload to '{bucket_name}/{file_path}': {e}")
            raise SupabaseNetworkError(f"Network error uploading to '{bucket_name}/{file_path}': {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during storage upload to '{bucket_name}/{file_path}': {e}", exc_info=True)
            raise

    def _upsert_articulo_with_retry(self, data):
        decorated_func = self._get_retry_decorator()(self.__upsert_articulo_logic)
        return decorated_func(data)

    def __upsert_articulo_logic(self, data):
        item_url = data.get('url', 'URL desconocida')
        logger.debug(f"Attempting to upsert article data for {item_url} via SupabaseClient")
        try:
            # Capture the response from the client's upsert_articulo method
            response_data = self.supabase_client.upsert_articulo(data)
            # SupabaseClient.upsert_articulo is expected to return data on success or None/raise on error
            if response_data:
                logger.info(f"SupabaseClient.upsert_articulo successful for {item_url}")
                return response_data # Return the actual data from Supabase
            else:
                # This case implies supabase_client.upsert_articulo returned None/empty without an exception,
                # which might indicate a logical failure or no actual upsert occurred.
                logger.warning(f"SupabaseClient.upsert_articulo for {item_url} returned no data or failed logically.")
                raise SupabaseAPIError(f"Upsert for article {item_url} returned no data.")
        except httpx.RequestError as e:
            logger.warning(f"Network error during DB upsert for article {item_url}: {e}")
            raise SupabaseNetworkError(f"Network error upserting article {item_url}: {e}") from e
        except SupabaseAPIError as e: 
            logger.warning(f"Supabase API error during DB upsert for article {item_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during DB upsert for article {item_url}: {e}", exc_info=True)
            raise

    def process_item(self, item, spider):
        if not isinstance(item, ArticuloInItem):
            logger.debug(f"Item no es una instancia de ArticuloInItem, omitiendo: {type(item)}")
            return item

        adapter = ItemAdapter(item)
        item_url_for_log = adapter.get('url', 'URL desconocida')
        logger.info(f"Processing item: {item_url_for_log}")

        if not adapter.get('fecha_recopilacion'):
            adapter['fecha_recopilacion'] = datetime.utcnow().isoformat()

        # 1. Handle HTML content storage
        html_content = adapter.get('contenido_html')
        if html_content:
            try:
                compressed_html = compress_html(html_content)
                medio_slug = adapter.get('medio', 'unknown_medio').lower().replace(' ', '_')
                fecha_pub_str = str(adapter.get('fecha_publicacion', 'unknown_date'))
                fecha_pub_path_part = fecha_pub_str.split('T')[0]
                file_name = f"{uuid.uuid4()}.html.gz"
                storage_file_path = f"{medio_slug}/{fecha_pub_path_part}/{file_name}"

                self._upload_to_storage_with_retry(
                    bucket_name=self.html_bucket_name,
                    file_path=storage_file_path,
                    file_content=compressed_html
                )
                adapter['storage_path'] = storage_file_path
                logger.info(f"Successfully stored HTML for {item_url_for_log} at {storage_file_path}")

            except RetryError as e:
                logger.error(
                    f"Failed to store HTML for {item_url_for_log} after {self.stop_after_attempt} attempts: {e}",
                    exc_info=True
                )
                adapter['error_detalle'] = (
                    f"HTML storage failed after retries: {e}; {adapter.get('error_detalle', '')}"
                )
            except Exception as e:
                logger.error(f"Failed to store HTML for {item_url_for_log}: {e}", exc_info=True)
                adapter['error_detalle'] = f"HTML storage failed: {e}; {adapter.get('error_detalle', '')}"
        else:
            logger.warning(f"No HTML content found for item {item_url_for_log}. Skipping HTML storage.")

        # 2. Prepare and upsert article metadata
        try:
            article_data_for_db = adapter.asdict()
            if 'contenido_html' in article_data_for_db:
                del article_data_for_db['contenido_html']
            
            for field_name, field_value in article_data_for_db.items():
                if isinstance(field_value, datetime):
                    article_data_for_db[field_name] = field_value.isoformat()

            upserted_data = self._upsert_articulo_with_retry(article_data_for_db)

            if upserted_data:
                logger.info(f"Successfully upserted article data for {item_url_for_log}. DB Response: {upserted_data}")
            else:
                logger.warning(f"Upsert article data for {item_url_for_log} did not return data, indicating a potential issue.")
                adapter['error_detalle'] = f"DB upsert for {item_url_for_log} returned no data; {adapter.get('error_detalle', '')}"

        except RetryError as e:
            logger.error(
                f"Failed to upsert article data for {item_url_for_log} after {self.stop_after_attempt} attempts: {e}",
                exc_info=True
            )
            adapter['error_detalle'] = f"DB upsert failed after retries: {e}; {adapter.get('error_detalle', '')}"
        except SupabaseNetworkError as e:
            logger.error(f"Supabase network error during article upsert for {item_url_for_log}: {e}", exc_info=True)
            adapter['error_detalle'] = f"DB upsert network error: {e}; {adapter.get('error_detalle', '')}"
        except SupabaseAPIError as e:
            logger.error(f"Supabase API error during article upsert for {item_url_for_log}: {e}", exc_info=True)
            adapter['error_detalle'] = f"DB upsert API error: {e}; {adapter.get('error_detalle', '')}"
        except Exception as e:
            logger.error(f"Unexpected error during article data upsert for {item_url_for_log}: {e}", exc_info=True)
            adapter['error_detalle'] = f"DB upsert failed unexpectedly: {e}; {adapter.get('error_detalle', '')}"
            
        if adapter.get('error_detalle'):
            logger.warning(f"Item {item_url_for_log} processed with errors: {adapter.get('error_detalle')}")
        else:
            logger.info(f"Item {item_url_for_log} processed successfully.")
            
        return item

class ExtractArticleItemsPipeline:
    def process_item(self, item, spider):
        # TODO: Implement item extraction logic for this pipeline stage.
        # This pipeline is intended to be the first stage for item processing.
        # See documentation: docs/Componentes/Módulo de Recopilación - Scrapy (module_scraper).md
        spider.logger.debug(f"ExtractArticleItemsPipeline: Processing item from {spider.name}")
        return item

class CleanArticleItemsPipeline:
    def process_item(self, item, spider):
        # TODO: Implement item cleaning logic for this pipeline stage.
        # This pipeline is intended for cleaning and normalizing items
        # before they are sent to the SupabaseStoragePipeline.
        # See documentation: docs/Componentes/Módulo de Recopilación - Scrapy (module_scraper).md
        spider.logger.debug(f"CleanArticleItemsPipeline: Processing item from {spider.name}")
        return item
