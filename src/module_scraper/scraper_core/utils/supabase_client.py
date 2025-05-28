"""
Supabase Client Utility
======================

This module provides a singleton SupabaseClient class for managing Supabase connections
and operations throughout the scraper module.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
import time
from functools import wraps

# Load environment variables from module_scraper/.env
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path)

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying failed operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


class SupabaseClient:
    """
    Singleton class for managing Supabase connections and operations.
    
    This class provides a centralized way to interact with Supabase,
    including database operations and storage management.
    """
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None) -> 'SupabaseClient':
        """Ensure only one instance of SupabaseClient exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize the Supabase client if not already initialized."""
        if self._client is None:
            self._initialize_client(supabase_url, supabase_key)
    
    def _initialize_client(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize the Supabase client with credentials from environment variables."""
        try:
            # Use provided credentials or fall back to environment variables
            url = supabase_url or os.getenv('SUPABASE_URL')
            key = supabase_key or os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
            
            if not url or not key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY must be set in environment variables or provided as arguments"
                )
            
            # Use service role key for server-side operations
            options = ClientOptions(
                postgrest_client_timeout=10,
                storage_client_timeout=30,
            )
            
            self._client = create_client(url, key, options)
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    @property
    def client(self) -> Client:
        """Get the Supabase client instance."""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    @retry_on_failure(max_retries=3)
    def health_check(self) -> bool:
        """
        Check if the Supabase connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            # Try a simple query to check connection
            self.client.table('articulos').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    @retry_on_failure(max_retries=3)
    def insert_articulo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert an article into the articulos table.
        
        Args:
            data: Dictionary containing article data
            
        Returns:
            Dict containing the inserted record
        """
        try:
            response = self.client.table('articulos').insert(data).execute()
            logger.debug(f"Successfully inserted article: {data.get('url', 'unknown')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to insert article: {str(e)}")
            raise
    
    @retry_on_failure(max_retries=3)
    def upsert_articulo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert an article into the articulos table.
        
        Args:
            data: Dictionary containing article data
            
        Returns:
            Dict containing the upserted record
        """
        try:
            response = self.client.table('articulos').upsert(data).execute()
            logger.debug(f"Successfully upserted article: {data.get('url', 'unknown')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to upsert article: {str(e)}")
            raise
    
    @retry_on_failure(max_retries=3)
    def check_article_exists(self, url: str) -> bool:
        """
        Check if an article with the given URL already exists.
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if article exists, False otherwise
        """
        try:
            response = self.client.table('articulos').select('id').eq('url', url).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Failed to check article existence: {str(e)}")
            raise
    
    @retry_on_failure(max_retries=3)
    def upload_to_storage(
        self, 
        bucket_name: str, 
        file_path: str, 
        file_content: bytes,
        content_type: str = 'application/gzip'
    ) -> Dict[str, Any]:
        """
        Upload a file to Supabase Storage.
        
        Args:
            bucket_name: Name of the storage bucket
            file_path: Path where the file will be stored in the bucket
            file_content: Binary content of the file
            content_type: MIME type of the file
            
        Returns:
            Dict containing upload result
        """
        try:
            response = self.client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type}
            )
            logger.debug(f"Successfully uploaded file to storage: {file_path}")
            return response
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {str(e)}")
            raise
    
    @retry_on_failure(max_retries=3)
    def create_bucket_if_not_exists(self, bucket_name: str, public: bool = False) -> bool:
        """
        Create a storage bucket if it doesn't exist.
        
        Args:
            bucket_name: Name of the bucket to create
            public: Whether the bucket should be public
            
        Returns:
            bool: True if bucket was created or already exists
        """
        try:
            # Check if bucket exists
            buckets = self.client.storage.list_buckets()
            bucket_exists = any(b['name'] == bucket_name for b in buckets)
            
            if not bucket_exists:
                self.client.storage.create_bucket(
                    bucket_name,
                    options={"public": public}
                )
                logger.info(f"Created storage bucket: {bucket_name}")
            else:
                logger.debug(f"Storage bucket already exists: {bucket_name}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create/check bucket: {str(e)}")
            raise
    
    @property
    def table(self):
        """Direct access to Supabase table operations for test compatibility."""
        return self.client.table
    
    @property
    def storage(self):
        """Direct access to Supabase storage operations for test compatibility."""
        return self.client.storage
    
    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all storage buckets."""
        try:
            return self.client.storage.list_buckets()
        except Exception as e:
            logger.error(f"Failed to list buckets: {str(e)}")
            raise
    
    def create_bucket(self, bucket_name: str, public: bool = False) -> Dict[str, Any]:
        """Create a new storage bucket."""
        try:
            return self.client.storage.create_bucket(
                bucket_name,
                options={"public": public}
            )
        except Exception as e:
            logger.error(f"Failed to create bucket: {str(e)}")
            raise
    
    def close(self):
        """Close the Supabase client connection."""
        # Supabase client doesn't require explicit closing
        # but we can reset the instance for cleanup
        self._client = None
        logger.info("Supabase client closed")


# Convenience function to get the singleton instance
def get_supabase_client() -> SupabaseClient:
    """Get the singleton SupabaseClient instance."""
    return SupabaseClient()
