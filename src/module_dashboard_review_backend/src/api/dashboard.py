"""
Dashboard API routes for editorial review of facts (hechos).

Provides endpoints for retrieving paginated lists of facts with filtering
capabilities and filter options for building dynamic UIs.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from datetime import datetime
from loguru import logger

# Import models
from ..models.requests import HechoFilterParams
from ..models.responses import HechoResponse, PaginatedResponse, FilterOptionsResponse

# Import services
from ..services.hechos_service import HechosService
from ..core.dependencies import get_hechos_service

# Create router instance
router = APIRouter()


@router.get(
    "/hechos_revision", 
    response_model=PaginatedResponse[HechoResponse],
    summary="Get facts for editorial revision",
    description="""
    Retrieve a paginated list of facts (hechos) for editorial review.
    
    This endpoint supports various filters including date ranges, media sources,
    countries, and importance levels. Results are paginated and include 
    associated article metadata through joins.
    """
)
async def get_hechos_for_revision(
    fecha_inicio: Optional[datetime] = Query(
        None, 
        description="Start date filter (inclusive)"
    ),
    fecha_fin: Optional[datetime] = Query(
        None, 
        description="End date filter (inclusive)"
    ),
    medio: Optional[str] = Query(
        None, 
        description="Filter by media source"
    ),
    pais_publicacion: Optional[str] = Query(
        None, 
        description="Filter by country of publication"
    ),
    importancia_min: Optional[int] = Query(
        None, 
        ge=1, 
        le=10,
        description="Minimum importance level (1-10)"
    ),
    importancia_max: Optional[int] = Query(
        None, 
        ge=1, 
        le=10,
        description="Maximum importance level (1-10)"
    ),
    limit: int = Query(
        20, 
        ge=1, 
        le=100,
        description="Number of items per page"
    ),
    offset: int = Query(
        0, 
        ge=0,
        description="Number of items to skip"
    ),
    hechos_service: HechosService = Depends(get_hechos_service)
) -> PaginatedResponse[HechoResponse]:
    """
    Get paginated list of facts for editorial review.
    
    Args:
        fecha_inicio: Filter facts occurring on or after this date
        fecha_fin: Filter facts occurring on or before this date
        medio: Filter by specific media outlet
        pais_publicacion: Filter by country where the fact occurred
        importancia_min: Minimum importance level (inclusive)
        importancia_max: Maximum importance level (inclusive)
        limit: Number of records to return per page
        offset: Number of records to skip (for pagination)
        hechos_service: Injected service for database operations
        
    Returns:
        PaginatedResponse containing list of facts and pagination metadata
        
    Raises:
        HTTPException: If validation fails or database error occurs
    """
    try:
        # Validate importance range
        if importancia_min is not None and importancia_max is not None:
            if importancia_min > importancia_max:
                raise HTTPException(
                    status_code=400,
                    detail="importancia_min must be less than or equal to importancia_max"
                )
        
        # Build filter parameters dictionary
        filter_params = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "medio": medio,
            "pais_publicacion": pais_publicacion,
            "importancia_min": importancia_min,
            "importancia_max": importancia_max,
            "limit": limit,
            "offset": offset
        }
        
        logger.info(
            "Fetching hechos for revision", 
            extra={"filter_params": filter_params}
        )
        
        # Call service to get facts
        hechos, total_count = await hechos_service.get_hechos_for_revision(filter_params)
        
        # Calculate pagination metadata
        page = (offset // limit) + 1
        total_pages = ((total_count - 1) // limit) + 1 if total_count > 0 else 0
        
        # Build response
        response = PaginatedResponse[HechoResponse](
            items=hechos,
            pagination={
                "total_items": total_count,
                "page": page,
                "per_page": limit,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        )
        
        logger.info(
            f"Successfully retrieved {len(hechos)} hechos "
            f"(page {page} of {total_pages})"
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving hechos for revision: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving facts"
        )


@router.get(
    "/filtros/opciones",
    response_model=FilterOptionsResponse,
    summary="Get filter options",
    description="""
    Retrieve available filter options for the dashboard UI.
    
    This endpoint provides lists of unique values for each filterable field,
    enabling dynamic filter interfaces. Returns available media sources,
    countries, and the valid importance range.
    """
)
async def get_filter_options(
    hechos_service: HechosService = Depends(get_hechos_service)
) -> FilterOptionsResponse:
    """
    Get available filter options for the dashboard.
    
    Args:
        hechos_service: Injected service for database operations
        
    Returns:
        FilterOptionsResponse containing lists of available filter values
        
    Raises:
        HTTPException: If database error occurs while retrieving options
    """
    try:
        logger.info("Fetching filter options for dashboard")
        
        # Call service to get filter options
        filter_options = await hechos_service.get_filter_options()
        
        logger.info(
            f"Successfully retrieved filter options: "
            f"{len(filter_options.get('medios_disponibles', []))} medios, "
            f"{len(filter_options.get('paises_disponibles', []))} paises"
        )
        
        return filter_options
        
    except Exception as e:
        logger.error(
            f"Error retrieving filter options: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Error retrieving filter options"
        )
