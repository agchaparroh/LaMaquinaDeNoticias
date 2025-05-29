import os
import logging
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from typing import Optional, Dict, Any, List, Union # Added Union
from datetime import datetime # Added for default fecha_extraccion

class SupabaseClient:
    """
    A singleton class to manage Supabase client interactions.
    
    Handles connection management, loading credentials from environment variables,
    and provides common operations for Supabase Storage and database tables.
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
                # ClientOptions can be used for more advanced configurations if needed
                # e.g., options = ClientOptions(auto_refresh_token=True, persist_session=True)
                self.client: Client = create_client(self.supabase_url, self.supabase_key)
                self.logger.info("Supabase client initialized successfully.")
            except Exception as e:
                self.logger.error(f"Failed to initialize Supabase client: {e}")
                raise
            
            self._initialized = True

            # --- Table Name Configurations ---
            self.articulos_table_name = os.getenv('SUPABASE_ARTICULOS_TABLE', 'articulos')
            self.autores_table_name = os.getenv('SUPABASE_AUTORES_TABLE', 'autores')
            self.etiquetas_table_name = os.getenv('SUPABASE_ETIQUETAS_TABLE', 'etiquetas')
            self.medios_table_name = os.getenv('SUPABASE_MEDIOS_TABLE', 'medios')
            self.rel_articulos_autores_table_name = os.getenv('SUPABASE_REL_ARTICULOS_AUTORES_TABLE', 'rel_articulos_autores')
            self.rel_articulos_etiquetas_table_name = os.getenv('SUPABASE_REL_ARTICULOS_ETIQUETAS_TABLE', 'rel_articulos_etiquetas')
            self.logger.info(f"Table names configured: articulos='{self.articulos_table_name}', medios='{self.medios_table_name}', etc.")

    def get_client(self) -> Client:
        """Returns the raw Supabase client instance."""
        if not self.client:
            self.logger.error("Supabase client is not initialized.")
            raise ConnectionError("Supabase client not initialized. Call __init__ first.")
        return self.client

    def _get_or_create_medio(self, medio_nombre: str, medio_url_principal: str, 
                             pais_origen: Optional[str] = None, 
                             idioma_principal: Optional[str] = None, 
                             tipo_medio: Optional[str] = None) -> Optional[int]:
        """
        Retrieves an existing 'medio' by its URL or creates a new one if not found.
        Returns the ID of the 'medio'.
        """
        if not medio_url_principal:
            self.logger.error("medio_url_principal is required to get or create a medio.")
            return None

        try:
            # Check if medio exists by url_principal
            response = self.client.table(self.medios_table_name).select("id").eq("url_principal", medio_url_principal).limit(1).execute()
            if response.data:
                medio_id = response.data[0]['id']
                self.logger.info(f"Medio found with ID: {medio_id} for URL: {medio_url_principal}")
                return medio_id
            else:
                # Medio does not exist, create it
                self.logger.info(f"Medio not found for URL: {medio_url_principal}. Creating new medio: {medio_nombre}")
                medio_data_to_insert = {
                    "nombre_medio": medio_nombre,
                    "url_principal": medio_url_principal,
                    "pais_origen": pais_origen,
                    "idioma_principal": idioma_principal,
                    "tipo_medio": tipo_medio
                }
                # Filter out None values to avoid inserting them if the column doesn't have a default
                medio_data_to_insert = {k: v for k, v in medio_data_to_insert.items() if v is not None}

                insert_response = self.client.table(self.medios_table_name).insert(medio_data_to_insert).execute()
                if insert_response.data:
                    new_medio_id = insert_response.data[0]['id']
                    self.logger.info(f"Medio '{medio_nombre}' created successfully with ID: {new_medio_id}")
                    return new_medio_id
                else:
                    self.logger.error(f"Failed to create medio '{medio_nombre}'. Response: {insert_response}")
                    return None
        except Exception as e:
            self.logger.error(f"Error in _get_or_create_medio for '{medio_nombre}': {e}")
            return None

    def upload_file(self, bucket_name: str, supabase_path: str, local_file_path: Optional[str] = None, file_content: Optional[bytes] = None, file_options: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Uploads a file to Supabase Storage.
        Either local_file_path or file_content must be provided.

        Args:
            bucket_name: The name of the Supabase Storage bucket.
            supabase_path: The path (including filename) where the file will be stored in the bucket.
            local_file_path: The local path to the file to upload.
            file_content: The binary content of the file to upload.
            file_options: Optional dictionary for file options (e.g., {'content-type': 'image/png'}).

        Returns:
            A dictionary containing the response from Supabase, or None if an error occurs.
        """
        if not local_file_path and not file_content:
            self.logger.error("Either local_file_path or file_content must be provided for upload.")
            return None
        
        try:
            if local_file_path:
                with open(local_file_path, 'rb') as f:
                    response = self.client.storage.from_(bucket_name).upload(
                        path=supabase_path,
                        file=f,
                        file_options=file_options or {}
                    )
            elif file_content:
                response = self.client.storage.from_(bucket_name).upload(
                    path=supabase_path,
                    file=file_content, # Pass bytes directly
                    file_options=file_options or {}
                )
            
            self.logger.info(f"File uploaded to {bucket_name}/{supabase_path}. Response: {response.json()}")
            return response.json() 
        except Exception as e:
            self.logger.error(f"Error uploading file to {bucket_name}/{supabase_path}: {e}")
            # Check for specific Supabase errors if the SDK provides them, e.g., StorageApiError
            # from supabase.lib.errors import StorageApiError
            # if isinstance(e, StorageApiError):
            #     self.logger.error(f"Supabase Storage API Error: {e.message}, Status: {e.status_code}")
            return None

    def insert_data(self, table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        """
        Inserts data into a Supabase table.

        Args:
            table_name: The name of the table.
            data: A dictionary or a list of dictionaries representing the row(s) to insert.

        Returns:
            A dictionary containing the response from Supabase (inserted data), or None if an error occurs.
        """
        if not data:
            self.logger.warning(f"No data provided for insertion into table {table_name}.")
            return None
        try:
            response = self.client.table(table_name).insert(data).execute()
            self.logger.info(f"Data inserted into {table_name}. Response: {response.data}")
            return response.data
        except Exception as e:
            self.logger.error(f"Error inserting data into {table_name}: {e}")
            # Check for specific Supabase errors if the SDK provides them, e.g., APIError
            # from supabase.lib.errors import APIError
            # if isinstance(e, APIError):
            #     self.logger.error(f"Supabase API Error: {e.message}, Status: {e.status_code}, Details: {e.details}")
            return None

    def upsert_articulo(self, articulo_item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Upserts an article to the 'articulos' table, including handling the 'medio'.
        Autores and etiquetas linking will be handled separately or in a more comprehensive method.
        Expects articulo_item_data to be a dictionary-like object (e.g., from ArticuloInItem).
        """
        # Basic validation for required fields from ArticuloInItem perspective
        # The actual ArticuloInItem should have its own validation method for completeness
        required_keys_from_item = ['url', 'titular', 'medio', 'medio_url_principal', 'fecha_publicacion', 'contenido_texto', 'contenido_html']
        for key in required_keys_from_item:
            if key not in articulo_item_data or not articulo_item_data.get(key):
                self.logger.error(f"Missing required key '{key}' in articulo_item_data for upsert_articulo.")
                return None
        
        medio_id = self._get_or_create_medio(
            medio_nombre=articulo_item_data.get('medio'),
            medio_url_principal=articulo_item_data.get('medio_url_principal'),
            pais_origen=articulo_item_data.get('pais_publicacion'),
            idioma_principal=articulo_item_data.get('idioma'),
            tipo_medio=articulo_item_data.get('tipo_medio')
        )

        if medio_id is None:
            self.logger.error(f"Failed to get or create medio_id for article URL: {articulo_item_data.get('url')}. Aborting article upsert.")
            return None

        # Prepare articulo data for DB, mapping from ArticuloInItem fields
        db_articulo_data = {
            "url": articulo_item_data.get('url'),
            "url_original": articulo_item_data.get('url_original'), 
            "titulo": articulo_item_data.get('titular'), 
            "subtitulo": articulo_item_data.get('subtitulo'), 
            "contenido_texto": articulo_item_data.get('contenido_texto'),
            "contenido_html": articulo_item_data.get('contenido_html'),
            "fecha_publicacion": articulo_item_data.get('fecha_publicacion'),
            "fecha_extraccion": articulo_item_data.get('fecha_recopilacion', datetime.now().isoformat()), # Default to now if not present
            "medio_id": medio_id,
            "seccion": articulo_item_data.get('seccion'),
            "pais_principal": articulo_item_data.get('pais_publicacion'),
            "idioma": articulo_item_data.get('idioma', 'es'),
            "storage_path": articulo_item_data.get('storage_path'),
            "resumen": articulo_item_data.get('resumen'),
            "palabras_clave": articulo_item_data.get('etiquetas_fuente')
        }
        
        db_articulo_data_cleaned = {k: v for k, v in db_articulo_data.items() if v is not None}

        try:
            response = self.client.table(self.articulos_table_name).upsert(db_articulo_data_cleaned, on_conflict='url').execute()
            self.logger.info(f"Article upserted for URL {db_articulo_data_cleaned['url']}. Response: {response.data}")
            
            if response.data:
                # TODO: Handle autores and etiquetas linking here or in a subsequent call
                # For now, just return the article upsert response
                return response.data[0] 
            return None
        except Exception as e:
            self.logger.error(f"Error upserting article for URL {db_articulo_data_cleaned.get('url')}: {e}")
            return None

# Example usage (optional, for testing purposes)
if __name__ == '__main__':
    # This block will only run when the script is executed directly
    # For this to work, you'd need a .env file or environment variables set
    # Example: create a .env file with:
    # SUPABASE_URL="your_supabase_url"
    # SUPABASE_KEY="your_supabase_anon_key" 
    # And run: python -m dotenv run python supabase_client.py (if using python-dotenv)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Ensure environment variables are loaded if using a .env file for local testing
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info(".env file loaded for local testing.")
    except ImportError:
        logger.info("dotenv not installed, relying on system environment variables for local testing.")

    SUPABASE_URL_TEST = os.getenv('SUPABASE_URL')
    SUPABASE_KEY_TEST = os.getenv('SUPABASE_KEY')

    if not SUPABASE_URL_TEST or not SUPABASE_KEY_TEST:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in environment or .env for testing.")
    else:
        try:
            # Test Singleton
            client1 = SupabaseClient()
            client2 = SupabaseClient()
            logger.info(f"Client1 is Client2: {client1 is client2}")

            # Test get_client
            raw_client = client1.get_client()
            if raw_client:
                logger.info("Successfully retrieved raw Supabase client.")

            # --- Test insert_data (Example - replace with your actual table and data) ---
            # test_table = "test_items" # Make sure this table exists in your Supabase
            # test_item_data = {"name": "Test Item from Client", "description": "This is a test."}
            # inserted_data = client1.insert_data(test_table, test_item_data)
            # if inserted_data:
            #     logger.info(f"Test data inserted: {inserted_data}")
            # else:
            #     logger.error("Test data insertion failed.")

            # --- Test upload_file (Example - replace with your actual bucket and file) ---
            # test_bucket = "test-bucket-lmn" # Make sure this bucket exists and is public/configured for anon key
            # test_file_name = "test_upload.txt"
            # test_file_content = b"Hello from SupabaseClient test!"
            # uploaded_file_info = client1.upload_file(
            #     bucket_name=test_bucket,
            #     supabase_path=f"tests/{test_file_name}", # Path within the bucket
            #     file_content=test_file_content,
            #     file_options={'content-type': 'text/plain'}
            # )
            # if uploaded_file_info:
            #    logger.info(f"Test file uploaded: {uploaded_file_info}")
            #    # You can construct the public URL if needed:
            #    # public_url = f"{SUPABASE_URL_TEST}/storage/v1/object/public/{test_bucket}/tests/{test_file_name}"
            #    # logger.info(f"Test file public URL (if bucket is public): {public_url}")
            # else:
            #    logger.error("Test file upload failed.")

        except ValueError as ve:
            logger.error(f"Initialization error during testing: {ve}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during testing: {e}")
