import os
import logging
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

class SupabaseClient:
    """
    A singleton class to manage Supabase client interactions.
    
    Handles connection management, loading credentials from environment variables,
    and provides common operations for Supabase Storage and database tables.
    
    Updated to work with simplified schema without 'medios' table.
    """
    _instance: Optional['SupabaseClient'] = None

    def __new__(cls, *args, **kwargs) -> 'SupabaseClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  # Ensure __init__ runs only once
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            
            # Configure logging handler if not already configured by Scrapy/root
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)

            self.supabase_url: Optional[str] = os.getenv('SUPABASE_URL')
            self.supabase_key: Optional[str] = os.getenv('SUPABASE_KEY')

            if not self.supabase_url or not self.supabase_key:
                self.logger.error("SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
                raise ValueError("Supabase URL and Key not found in environment variables.")

            try:
                self.client: Client = create_client(self.supabase_url, self.supabase_key)
                self.logger.info("Supabase client initialized successfully.")
            except Exception as e:
                self.logger.error(f"Failed to initialize Supabase client: {e}")
                raise
            
            self._initialized = True

            # --- Table Name Configurations ---
            self.articulos_table_name = os.getenv('SUPABASE_ARTICULOS_TABLE', 'articulos')
            self.logger.info(f"SupabaseClient configured for simplified schema. Table: articulos='{self.articulos_table_name}'")

    def get_client(self) -> Client:
        """Returns the raw Supabase client instance."""
        if not self.client:
            self.logger.error("Supabase client is not initialized.")
            raise ConnectionError("Supabase client not initialized. Call __init__ first.")
        return self.client

    def upload_to_storage(self, bucket_name: str, file_path: str, file_content: bytes, 
                         file_options: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Uploads file content to Supabase Storage.
        
        Args:
            bucket_name: The name of the Supabase Storage bucket.
            file_path: The path (including filename) where the file will be stored.
            file_content: The binary content of the file to upload.
            file_options: Optional dictionary for file options.

        Returns:
            A dictionary containing the response from Supabase, or None if an error occurs.
        """
        try:
            response = self.client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options=file_options or {}
            )
            self.logger.info(f"File uploaded to {bucket_name}/{file_path}")
            return response.json() if hasattr(response, 'json') else response
        except Exception as e:
            self.logger.error(f"Error uploading file to {bucket_name}/{file_path}: {e}")
            return None

    def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        """
        Creates a bucket if it doesn't exist.
        
        Args:
            bucket_name: Name of the bucket to create.
            
        Returns:
            True if bucket exists or was created successfully, False otherwise.
        """
        try:
            # Try to list buckets to see if it exists
            buckets_response = self.client.storage.list_buckets()
            existing_buckets = [bucket.name for bucket in buckets_response]
            
            if bucket_name in existing_buckets:
                self.logger.info(f"Bucket '{bucket_name}' already exists")
                return True
            
            # Create the bucket
            create_response = self.client.storage.create_bucket(bucket_name)
            self.logger.info(f"Bucket '{bucket_name}' created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating bucket '{bucket_name}': {e}")
            return False

    def insert_data(self, table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """
        Inserts data into a Supabase table.

        Args:
            table_name: The name of the table.
            data: A dictionary or a list of dictionaries representing the row(s) to insert.

        Returns:
            The inserted data, or None if an error occurs.
        """
        if not data:
            self.logger.warning(f"No data provided for insertion into table {table_name}.")
            return None
        try:
            response = self.client.table(table_name).insert(data).execute()
            self.logger.info(f"Data inserted into {table_name}")
            return response.data
        except Exception as e:
            self.logger.error(f"Error inserting data into {table_name}: {e}")
            return None

    def upsert_articulo(self, articulo_item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Upserts an article to the 'articulos' table using the simplified schema.
        No longer requires 'medios' table - stores medio information directly in articulos.
        
        Args:
            articulo_item_data: Dictionary containing article data.
            
        Returns:
            The upserted article data, or None if an error occurs.
        """
        # Basic validation for required fields (simplified for current schema)
        required_keys = ['url', 'titular', 'medio', 'fecha_publicacion']
        missing_keys = [key for key in required_keys if key not in articulo_item_data or not articulo_item_data.get(key)]
        
        if missing_keys:
            self.logger.error(f"Missing required keys {missing_keys} in articulo_item_data for upsert_articulo.")
            return None

        # Map ArticuloInItem fields to database schema
        # Convert datetime objects to ISO strings if necessary
        fecha_pub = articulo_item_data.get('fecha_publicacion')
        if isinstance(fecha_pub, datetime):
            fecha_pub = fecha_pub.isoformat()
            
        fecha_recop = articulo_item_data.get('fecha_recopilacion')
        if isinstance(fecha_recop, datetime):
            fecha_recop = fecha_recop.isoformat()
        elif not fecha_recop:
            fecha_recop = datetime.now().isoformat()

        # Prepare article data for database
        db_articulo_data = {
            "url": articulo_item_data.get('url'),
            "storage_path": articulo_item_data.get('storage_path'),
            "medio": articulo_item_data.get('medio'),
            "pais_publicacion": articulo_item_data.get('pais_publicacion', 'España'),
            "tipo_medio": articulo_item_data.get('tipo_medio', 'digital'),
            "titular": articulo_item_data.get('titular'),
            "fecha_publicacion": fecha_pub,
            "autor": articulo_item_data.get('autor'),
            "idioma": articulo_item_data.get('idioma', 'es'),
            "seccion": articulo_item_data.get('seccion'),
            "etiquetas_fuente": articulo_item_data.get('etiquetas_fuente'),
            "es_opinion": articulo_item_data.get('es_opinion', False),
            "es_oficial": articulo_item_data.get('es_oficial', False),
            "resumen": articulo_item_data.get('resumen'),
            "categorias_asignadas": articulo_item_data.get('categorias_asignadas'),
            "puntuacion_relevancia": articulo_item_data.get('puntuacion_relevancia'),
            "fecha_recopilacion": fecha_recop,
            "estado_procesamiento": articulo_item_data.get('estado_procesamiento', 'completado'),
        }
        
        # Remove None values to avoid database issues
        db_articulo_data_cleaned = {k: v for k, v in db_articulo_data.items() if v is not None}

        try:
            response = self.client.table(self.articulos_table_name).upsert(
                db_articulo_data_cleaned, 
                on_conflict='url'
            ).execute()
            
            if response.data:
                self.logger.info(f"Article upserted successfully for URL: {db_articulo_data_cleaned['url']}")
                return response.data[0]
            else:
                self.logger.warning(f"Upsert returned no data for URL: {db_articulo_data_cleaned.get('url')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error upserting article for URL {db_articulo_data_cleaned.get('url')}: {e}")
            return None

    def get_articulo_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves an article by its URL.
        
        Args:
            url: The URL of the article to retrieve.
            
        Returns:
            The article data, or None if not found or error occurs.
        """
        try:
            response = self.client.table(self.articulos_table_name).select('*').eq('url', url).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving article by URL {url}: {e}")
            return None

    def update_articulo_status(self, url: str, status: str, error_detail: Optional[str] = None) -> bool:
        """
        Updates the processing status of an article.
        
        Args:
            url: The URL of the article to update.
            status: The new processing status.
            error_detail: Optional error detail if status indicates an error.
            
        Returns:
            True if update was successful, False otherwise.
        """
        try:
            update_data = {'estado_procesamiento': status}
            if error_detail:
                update_data['error_detalle'] = error_detail
            
            response = self.client.table(self.articulos_table_name).update(update_data).eq('url', url).execute()
            if response.data:
                self.logger.info(f"Updated article status for URL {url} to {status}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating article status for URL {url}: {e}")
            return False

# Example usage and testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load environment variables if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info(".env file loaded for local testing.")
    except ImportError:
        logger.info("dotenv not installed, relying on system environment variables.")

    SUPABASE_URL_TEST = os.getenv('SUPABASE_URL')
    SUPABASE_KEY_TEST = os.getenv('SUPABASE_KEY')

    if not SUPABASE_URL_TEST or not SUPABASE_KEY_TEST:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in environment for testing.")
    else:
        try:
            # Test Singleton pattern
            client1 = SupabaseClient()
            client2 = SupabaseClient()
            logger.info(f"Singleton working: {client1 is client2}")

            # Test get_client
            raw_client = client1.get_client()
            if raw_client:
                logger.info("Successfully retrieved raw Supabase client.")

        except ValueError as ve:
            logger.error(f"Initialization error during testing: {ve}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during testing: {e}")
