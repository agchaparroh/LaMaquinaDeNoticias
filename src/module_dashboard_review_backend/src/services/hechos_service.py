"""
Business logic service for hechos (facts) operations.

This service handles all database operations related to hechos,
including filtering, pagination, and data formatting.
"""

from typing import Dict, List, Tuple, Any
from loguru import logger

from .supabase_client import SupabaseClient
from ..utils.exceptions import DatabaseConnectionError


class HechosService:
    """
    Service class for handling hechos-related operations.
    
    Provides methods for querying, filtering, and formatting
    facts data from the database.
    """
    
    def __init__(self):
        """Initialize the service with Supabase client."""
        self.supabase_client = SupabaseClient.get_client()
        logger.debug("HechosService initialized")
    
    async def get_hechos_for_revision(
        self, 
        filter_params: Dict[str, Any]
    ) -> Tuple[List[Dict], int]:
        """
        Get hechos for editorial revision with filters and pagination.
        
        This method retrieves facts from the database along with their
        associated article metadata through a join operation.
        
        Args:
            filter_params: Dictionary containing filter parameters
                - fecha_inicio: Start date filter
                - fecha_fin: End date filter  
                - medio: Media outlet filter
                - pais_publicacion: Country filter
                - importancia_min: Minimum importance filter
                - importancia_max: Maximum importance filter
                - limit: Number of records to return
                - offset: Number of records to skip
                
        Returns:
            Tuple containing:
                - List of hechos with article metadata
                - Total count of matching records
                
        Raises:
            Exception: If database query fails
        """
        try:
            logger.info(
                "Fetching hechos for revision",
                extra={"filter_params": filter_params}
            )
            
            # Build base query with join to articulos table - EXPANDED FIELDS
            query = self.supabase_client.table('hechos').select(
                # Core hecho fields
                "id, contenido, fecha_ocurrencia, precision_temporal, "
                "importancia, tipo_hecho, pais, region, ciudad, "
                # Metadata and tags
                "etiquetas, frecuencia_citacion, total_menciones, menciones_confirmatorias, "
                # Timestamps and processing info
                "fecha_ingreso, "
                # Editorial evaluation fields
                "evaluacion_editorial, editor_evaluador, fecha_evaluacion_editorial, "
                "justificacion_evaluacion_editorial, consenso_fuentes, "
                # Future events and status
                "es_evento_futuro, estado_programacion, "
                # Additional metadata
                "metadata, "
                # Expanded articulos fields
                "articulos(medio, titular, fecha_publicacion, url, "
                "pais_publicacion, tipo_medio, autor, seccion, "
                "es_opinion, es_oficial, resumen, categorias_asignadas, "
                "puntuacion_relevancia, estado_procesamiento)",
                count='exact'
            )
            
            # Order by fecha_ingreso descending (most recent first)
            # Note: fecha_ingreso is not in the select but can be used for ordering
            query = query.order('fecha_ingreso', desc=True)
            
            # Apply filters based on filter_params
            # Date filters
            if filter_params.get('fecha_inicio') is not None:
                # Convert datetime to ISO format for Supabase
                fecha_inicio_iso = filter_params['fecha_inicio'].isoformat()
                query = query.gte('fecha_ocurrencia', fecha_inicio_iso)
                logger.debug(f"Applied fecha_inicio filter: >= {fecha_inicio_iso}")
            
            if filter_params.get('fecha_fin') is not None:
                # Convert datetime to ISO format for Supabase
                fecha_fin_iso = filter_params['fecha_fin'].isoformat()
                query = query.lte('fecha_ocurrencia', fecha_fin_iso)
                logger.debug(f"Applied fecha_fin filter: <= {fecha_fin_iso}")
            
            # Content filters
            if filter_params.get('medio') is not None:
                # Filter by medio through the joined articulos table
                query = query.eq('articulos.medio', filter_params['medio'])
                logger.debug(f"Applied medio filter: {filter_params['medio']}")
            
            if filter_params.get('pais_publicacion') is not None:
                # Filter by country
                query = query.eq('pais', filter_params['pais_publicacion'])
                logger.debug(f"Applied pais filter: {filter_params['pais_publicacion']}")
            
            # Importance range filters
            if filter_params.get('importancia_min') is not None:
                # Validate range 1-10 (already validated in model)
                query = query.gte('importancia', filter_params['importancia_min'])
                logger.debug(f"Applied importancia_min filter: >= {filter_params['importancia_min']}")
            
            if filter_params.get('importancia_max') is not None:
                # Validate range 1-10 (already validated in model)
                query = query.lte('importancia', filter_params['importancia_max'])
                logger.debug(f"Applied importancia_max filter: <= {filter_params['importancia_max']}")
            
            # First, get the total count with a separate query
            # We need to build the same query but without pagination
            count_query = self.supabase_client.table('hechos').select(
                'id', count='exact'
            )
            
            # Apply the same filters to count query
            # Date filters
            if filter_params.get('fecha_inicio') is not None:
                fecha_inicio_iso = filter_params['fecha_inicio'].isoformat()
                count_query = count_query.gte('fecha_ocurrencia', fecha_inicio_iso)
            
            if filter_params.get('fecha_fin') is not None:
                fecha_fin_iso = filter_params['fecha_fin'].isoformat()
                count_query = count_query.lte('fecha_ocurrencia', fecha_fin_iso)
            
            # Content filters
            if filter_params.get('medio') is not None:
                # Note: For count query with joins, we need a different approach
                # Supabase doesn't support filtering by joined table in count queries
                # So we'll apply this filter later
                pass
            
            if filter_params.get('pais_publicacion') is not None:
                count_query = count_query.eq('pais', filter_params['pais_publicacion'])
            
            # Importance range filters
            if filter_params.get('importancia_min') is not None:
                count_query = count_query.gte('importancia', filter_params['importancia_min'])
            
            if filter_params.get('importancia_max') is not None:
                count_query = count_query.lte('importancia', filter_params['importancia_max'])
            
            # Execute count query
            count_result = count_query.execute()
            total_count = count_result.count or 0
            
            # Apply pagination to main query
            limit = filter_params.get('limit', 20)
            offset = filter_params.get('offset', 0)
            
            query = query.range(
                offset,
                offset + limit - 1
            )
            
            logger.debug(f"Applying pagination: limit={limit}, offset={offset}")
            
            # Execute main query with pagination
            result = query.execute()
            
            # Extract and format data
            hechos_data = result.data or []
            
            # Format response: separate articulo metadata
            formatted_hechos = []
            for hecho in hechos_data:
                # Extract articulos data (it comes as a dict from the join)
                articulo = hecho.pop('articulos', None)
                
                # Build formatted hecho with articulo_metadata
                formatted_hecho = {
                    **hecho,
                    'articulo_metadata': articulo if articulo else {}
                }
                formatted_hechos.append(formatted_hecho)
            
            # If medio filter was applied, we need to adjust the total count
            # This is because the count query couldn't filter by joined table
            if filter_params.get('medio') is not None:
                # The actual total is what we got from the paginated query
                # This is a limitation of Supabase count with joins
                total_count = result.count or len(hechos_data)
            
            logger.info(
                f"Retrieved {len(formatted_hechos)} hechos "
                f"(page: offset={offset}, limit={limit}, total={total_count})"
            )
            
            return formatted_hechos, total_count
            
        except DatabaseConnectionError:
            # Re-raise database connection errors as-is
            logger.error(
                "Database connection error in get_hechos_for_revision",
                extra={"filter_params": filter_params}
            )
            raise
        except Exception as e:
            # Log and re-raise other exceptions
            logger.error(
                f"Unexpected error fetching hechos for revision: {str(e)}",
                extra={"filter_params": filter_params},
                exc_info=True
            )
            raise Exception(f"Failed to retrieve hechos: {str(e)}") from e
    
    async def get_filter_options(self) -> Dict[str, Any]:
        """
        Get available filter options from the database.
        
        This method queries the database to retrieve unique values for
        filterable fields, enabling dynamic filter interfaces in the UI.
        
        Returns:
            Dictionary containing:
                - medios_disponibles: List of unique media sources
                - paises_disponibles: List of unique countries
                - importancia_range: Min and max importance values
                
        Raises:
            Exception: If any database query fails
        """
        logger.info("Fetching filter options from database")
        
        # Initialize defaults for graceful degradation
        medios = []
        paises = []
        min_importancia = 1
        max_importancia = 10
        
        # Query 1: Get unique medios from articulos table
        try:
            medios_query = self.supabase_client.table('articulos')\
                .select('medio')\
                .limit(1000)
            medios_result = medios_query.execute()
            medios = list(set([item['medio'] for item in medios_result.data if item.get('medio')]))
            logger.debug(f"Successfully fetched {len(medios)} unique medios")
        except Exception as e:
            logger.error(f"Error fetching medios: {str(e)}")
            # Continue with empty list - graceful degradation
        
        # Query 2: Get unique paises from hechos table
        try:
            paises_query = self.supabase_client.table('hechos')\
                .select('pais')\
                .limit(1000)
            paises_result = paises_query.execute()
            paises = list(set([item['pais'] for item in paises_result.data if item.get('pais')]))
            logger.debug(f"Successfully fetched {len(paises)} unique paises")
        except Exception as e:
            logger.error(f"Error fetching paises: {str(e)}")
            # Continue with empty list - graceful degradation
        
        # Query 3a: Get minimum importancia
        try:
            min_importancia_query = self.supabase_client.table('hechos')\
                .select('importancia')\
                .order('importancia', desc=False)\
                .limit(1)
            min_result = min_importancia_query.execute()
            if min_result.data:
                min_importancia = min_result.data[0]['importancia']
            logger.debug(f"Successfully fetched min importancia: {min_importancia}")
        except Exception as e:
            logger.error(f"Error fetching min importancia: {str(e)}")
            # Continue with default value 1
        
        # Query 3b: Get maximum importancia
        try:
            max_importancia_query = self.supabase_client.table('hechos')\
                .select('importancia')\
                .order('importancia', desc=True)\
                .limit(1)
            max_result = max_importancia_query.execute()
            if max_result.data:
                max_importancia = max_result.data[0]['importancia']
            logger.debug(f"Successfully fetched max importancia: {max_importancia}")
        except Exception as e:
            logger.error(f"Error fetching max importancia: {str(e)}")
            # Continue with default value 10
        
        # Log final results
        logger.info(
            f"Retrieved filter options: {len(medios)} medios, "
            f"{len(paises)} paises, importance range {min_importancia}-{max_importancia}"
        )
        
        # Check if all queries failed
        if not medios and not paises:
            logger.warning(
                "All filter option queries failed, returning defaults"
            )
        
        return {
            "medios_disponibles": sorted(medios),
            "paises_disponibles": sorted(paises),
            "importancia_range": {
                "min": min_importancia,
                "max": max_importancia
            }
        }
