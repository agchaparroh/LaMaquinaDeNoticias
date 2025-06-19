"""
Supabase client service for Dashboard Review Backend
Implements singleton pattern for database connection
"""

import asyncio
import time
from typing import Optional, TypeVar, Callable, Any, Dict, List, Tuple
from supabase import create_client, Client
from loguru import logger

from ..utils.config import settings
from ..utils.exceptions import DatabaseConnectionError


# Type variable for generic return type
T = TypeVar('T')


class SupabaseClient:
    """
    Singleton Supabase client for database operations.
    
    This class ensures a single instance of the Supabase client is used
    throughout the application, reducing connection overhead and providing
    a centralized point for database access.
    
    Example:
        >>> client = SupabaseClient.get_client()
        >>> result = client.table('hechos').select('*').execute()
    """
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    _max_retries: int = 3
    _base_delay: float = 1.0  # Base delay in seconds
    
    def __new__(cls) -> 'SupabaseClient':
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Get the Supabase client instance.
        
        Creates the client on first call and returns the same instance
        on subsequent calls (singleton pattern).
        
        Returns:
            Client: The Supabase client instance
            
        Raises:
            DatabaseConnectionError: If client initialization fails
            
        Example:
            >>> client = SupabaseClient.get_client()
            >>> # Use client for database operations
        """
        if cls._client is None:
            cls._initialize_client()
        return cls._client
    
    @classmethod
    def _initialize_client(cls) -> None:
        """
        Initialize the Supabase client with credentials from settings.
        
        This is a private method that should only be called internally
        when the client needs to be created for the first time.
        
        Raises:
            DatabaseConnectionError: If initialization fails
        """
        try:
            logger.info("Initializing Supabase client...")
            
            # Validate required settings
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError("Supabase URL and key must be provided")
            
            # Create the client
            cls._client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_key
            )
            
            logger.info("Supabase client initialized successfully")
            
        except ValueError as e:
            logger.error(f"Invalid Supabase configuration: {str(e)}")
            raise DatabaseConnectionError(
                f"Invalid Supabase configuration: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise DatabaseConnectionError(
                f"Could not connect to Supabase: {str(e)}"
            )
    
    @classmethod
    async def execute_with_retry(
        cls,
        operation: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute a database operation with retry logic and exponential backoff.
        
        This method will attempt to execute the given operation up to max_retries
        times, with an exponentially increasing delay between attempts.
        
        Args:
            operation: The callable operation to execute (can be sync or async)
            *args: Positional arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            The result of the successful operation
            
        Raises:
            The last exception if all retry attempts fail
            
        Example:
            >>> async def get_hechos():
            ...     client = SupabaseClient.get_client()
            ...     return client.table('hechos').select('*').execute()
            >>> 
            >>> result = await SupabaseClient.execute_with_retry(get_hechos)
        """
        last_exception = None
        
        for attempt in range(cls._max_retries):
            try:
                # Execute the operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                # Success - return the result
                if attempt > 0:
                    logger.info(f"Operation succeeded after {attempt} retry attempts")
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this is the last attempt
                if attempt == cls._max_retries - 1:
                    logger.error(
                        f"Operation failed after {cls._max_retries} attempts: {str(e)}"
                    )
                    raise
                
                # Calculate exponential backoff delay
                delay = cls._base_delay * (attempt + 1)
                
                logger.warning(
                    f"Operation attempt {attempt + 1}/{cls._max_retries} failed: {str(e)}. "
                    f"Retrying in {delay:.1f} seconds..."
                )
                
                # Wait before retrying
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry logic")
    
    @classmethod
    def reset_client(cls) -> None:
        """
        Reset the client instance (useful for testing).
        
        This method clears the singleton instance, forcing a new
        client to be created on the next get_client() call.
        
        Example:
            >>> SupabaseClient.reset_client()
            >>> # Next get_client() will create a new instance
        """
        cls._client = None
        logger.debug("Supabase client reset")
    
    @classmethod
    async def select_with_pagination(
        cls,
        table_name: str,
        columns: str = "*",
        filters: Optional[Dict] = None,
        limit: int = 20,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> Tuple[List, int]:
        """
        Execute a SELECT query with pagination support.
        
        Args:
            table_name: Name of the table to query
            columns: Columns to select (default: "*")
            filters: Dictionary of filters to apply {column: value}
            limit: Number of records to return
            offset: Number of records to skip
            order_by: Column to order by
            order_desc: Whether to order descending (default: True)
            
        Returns:
            Tuple of (data list, total count)
            
        Example:
            >>> data, total = await SupabaseClient.select_with_pagination(
            ...     "hechos",
            ...     filters={"pais": "Argentina"},
            ...     limit=10,
            ...     offset=0
            ... )
        """
        def _execute_select():
            client = cls.get_client()
            
            # Build base query
            query = client.table(table_name).select(columns, count='exact')
            
            # Apply filters
            if filters:
                for column, value in filters.items():
                    if value is not None:
                        query = query.eq(column, value)
            
            # Apply ordering
            if order_by:
                query = query.order(order_by, desc=order_desc)
            
            # Apply pagination
            query = query.range(offset, offset + limit - 1)
            
            # Execute query
            return query.execute()
        
        # Execute with retry
        result = await cls.execute_with_retry(_execute_select)
        
        # Extract data and count
        data = result.data or []
        total_count = result.count or 0
        
        logger.debug(
            f"Selected {len(data)} records from {table_name} "
            f"(total: {total_count})"
        )
        
        return data, total_count
    
    @classmethod
    async def get_single_record(
        cls,
        table_name: str,
        record_id: Any,
        id_column: str = "id",
        columns: str = "*"
    ) -> Optional[Dict]:
        """
        Get a single record by ID.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to retrieve
            id_column: Name of the ID column (default: "id")
            columns: Columns to select (default: "*")
            
        Returns:
            The record data or None if not found
            
        Example:
            >>> hecho = await SupabaseClient.get_single_record(
            ...     "hechos",
            ...     record_id=123
            ... )
        """
        def _get_record():
            client = cls.get_client()
            return client.table(table_name)\
                .select(columns)\
                .eq(id_column, record_id)\
                .limit(1)\
                .execute()
        
        # Execute with retry
        result = await cls.execute_with_retry(_get_record)
        
        # Return first record or None
        if result.data and len(result.data) > 0:
            logger.debug(f"Found record {record_id} in {table_name}")
            return result.data[0]
        else:
            logger.debug(f"Record {record_id} not found in {table_name}")
            return None
    
    @classmethod
    async def update_record(
        cls,
        table_name: str,
        record_id: Any,
        data: Dict,
        id_column: str = "id"
    ) -> Dict:
        """
        Update a single record.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to update
            data: Dictionary of fields to update
            id_column: Name of the ID column (default: "id")
            
        Returns:
            The updated record data
            
        Raises:
            Exception if update fails
            
        Example:
            >>> updated = await SupabaseClient.update_record(
            ...     "hechos",
            ...     record_id=123,
            ...     data={"evaluacion_editorial": "verificado_ok_editorial"}
            ... )
        """
        def _update_record():
            client = cls.get_client()
            return client.table(table_name)\
                .update(data)\
                .eq(id_column, record_id)\
                .execute()
        
        # Execute with retry
        result = await cls.execute_with_retry(_update_record)
        
        if result.data and len(result.data) > 0:
            logger.info(f"Updated record {record_id} in {table_name}")
            return result.data[0]
        else:
            raise Exception(
                f"Failed to update record {record_id} in {table_name}"
            )
    
    @classmethod
    async def count_records(
        cls,
        table_name: str,
        filters: Optional[Dict] = None
    ) -> int:
        """
        Count records in a table with optional filters.
        
        Args:
            table_name: Name of the table
            filters: Dictionary of filters to apply {column: value}
            
        Returns:
            The count of matching records
            
        Example:
            >>> count = await SupabaseClient.count_records(
            ...     "hechos",
            ...     filters={"pais": "Mexico", "importancia": 8}
            ... )
        """
        def _count_records():
            client = cls.get_client()
            
            # Build query with count
            query = client.table(table_name).select('id', count='exact')
            
            # Apply filters
            if filters:
                for column, value in filters.items():
                    if value is not None:
                        query = query.eq(column, value)
            
            # Execute query
            return query.execute()
        
        # Execute with retry
        result = await cls.execute_with_retry(_count_records)
        
        count = result.count or 0
        logger.debug(
            f"Counted {count} records in {table_name} "
            f"with filters: {filters}"
        )
        
        return count
