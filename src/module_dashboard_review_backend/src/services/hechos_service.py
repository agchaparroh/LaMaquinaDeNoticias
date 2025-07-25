"""
Business logic service for hechos (facts) operations.

This service handles all database operations related to hechos,
including filtering, pagination, and data formatting.
"""

from typing import Any, Dict, List, Tuple

from loguru import logger

from ..models.domain import HechoRelacionado
from ..models.responses import ArticuloMetadata, HechoRelacionInfo, HechoResponse
from ..utils.exceptions import DatabaseConnectionError
from .supabase_client import SupabaseClient


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
        self, filter_params: Dict[str, Any]
    ) -> Tuple[List[HechoResponse], int]:
        """
        Get hechos for editorial revision with filters and pagination.

        This method retrieves facts from the database along with their
        associated article metadata through a join operation.

        Args:
            filter_params: Dictionary containing filter parameters
                - fecha_inicio: Start date filter
                - fecha_fin: End date filter
                - medio: Media outlet filter
                - area_geografica: Country filter
                - importancia_min: Minimum importance filter
                - importancia_max: Maximum importance filter
                - limit: Number of records to return
                - offset: Number of records to skip

        Returns:
            Tuple containing:
                - List of HechoResponse objects with article metadata and relationships
                - Total count of matching records

        Raises:
            Exception: If database query fails
        """
        try:
            logger.info(
                "Fetching hechos for revision", extra={"filter_params": filter_params}
            )

            # Build base query with join to articulos table - EXPANDED FIELDS
            query = self.supabase_client.table("hechos").select(
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
                "area_geografica, tipo_medio, autor, seccion, "
                "es_opinion, es_oficial, resumen, categorias_asignadas, "
                "puntuacion_relevancia, estado_procesamiento)",
                count="exact",
            )

            # Order by fecha_ingreso descending (most recent first)
            # Note: fecha_ingreso is not in the select but can be used for ordering
            query = query.order("fecha_ingreso", desc=True)

            # Apply filters based on filter_params
            # Date filters
            if filter_params.get("fecha_inicio") is not None:
                # Convert datetime to ISO format for Supabase
                fecha_inicio_iso = filter_params["fecha_inicio"].isoformat()
                query = query.gte("fecha_ocurrencia", fecha_inicio_iso)
                logger.debug(f"Applied fecha_inicio filter: >= {fecha_inicio_iso}")

            if filter_params.get("fecha_fin") is not None:
                # Convert datetime to ISO format for Supabase
                fecha_fin_iso = filter_params["fecha_fin"].isoformat()
                query = query.lte("fecha_ocurrencia", fecha_fin_iso)
                logger.debug(f"Applied fecha_fin filter: <= {fecha_fin_iso}")

            # Content filters
            if filter_params.get("medio") is not None:
                # Filter by medio through the joined articulos table
                query = query.eq("articulos.medio", filter_params["medio"])
                logger.debug(f"Applied medio filter: {filter_params['medio']}")

            if filter_params.get("area_geografica") is not None:
                # Filter by country
                query = query.eq("pais", filter_params["area_geografica"])
                logger.debug(f"Applied pais filter: {filter_params['area_geografica']}")

            # Importance range filters
            if filter_params.get("importancia_min") is not None:
                # Validate range 1-10 (already validated in model)
                query = query.gte("importancia", filter_params["importancia_min"])
                logger.debug(
                    f"Applied importancia_min filter: >= {filter_params['importancia_min']}"
                )

            if filter_params.get("importancia_max") is not None:
                # Validate range 1-10 (already validated in model)
                query = query.lte("importancia", filter_params["importancia_max"])
                logger.debug(
                    f"Applied importancia_max filter: <= {filter_params['importancia_max']}"
                )

            # First, get the total count with a separate query
            # We need to build the same query but without pagination
            count_query = self.supabase_client.table("hechos").select(
                "id", count="exact"
            )

            # Apply the same filters to count query
            # Date filters
            if filter_params.get("fecha_inicio") is not None:
                fecha_inicio_iso = filter_params["fecha_inicio"].isoformat()
                count_query = count_query.gte("fecha_ocurrencia", fecha_inicio_iso)

            if filter_params.get("fecha_fin") is not None:
                fecha_fin_iso = filter_params["fecha_fin"].isoformat()
                count_query = count_query.lte("fecha_ocurrencia", fecha_fin_iso)

            # Content filters
            if filter_params.get("medio") is not None:
                # Note: For count query with joins, we need a different approach
                # Supabase doesn't support filtering by joined table in count queries
                # So we'll apply this filter later
                pass

            if filter_params.get("area_geografica") is not None:
                count_query = count_query.eq("pais", filter_params["area_geografica"])

            # Importance range filters
            if filter_params.get("importancia_min") is not None:
                count_query = count_query.gte(
                    "importancia", filter_params["importancia_min"]
                )

            if filter_params.get("importancia_max") is not None:
                count_query = count_query.lte(
                    "importancia", filter_params["importancia_max"]
                )

            # Execute count query
            count_result = count_query.execute()
            total_count = count_result.count or 0

            # Apply pagination to main query
            limit = filter_params.get("limit", 20)
            offset = filter_params.get("offset", 0)

            query = query.range(offset, offset + limit - 1)

            logger.debug(f"Applying pagination: limit={limit}, offset={offset}")

            # Execute main query with pagination
            result = query.execute()

            # Extract and format data
            hechos_data = result.data or []

            # Si no hay datos, retornar listas vacías
            if not hechos_data:
                logger.info("No se encontraron hechos que coincidan con los filtros")
                return [], total_count

            # Extraer IDs de hechos para buscar relaciones
            hecho_ids = [hecho["id"] for hecho in hechos_data]

            # Obtener relaciones para todos los hechos de la página
            relaciones_por_hecho = await self.get_relaciones_para_hechos(hecho_ids)

            # Crear objetos HechoResponse
            hechos_response = []
            for hecho_raw in hechos_data:
                # Extraer datos del artículo (viene como dict del JOIN)
                articulo_data = hecho_raw.pop("articulos", None) or {}

                # Crear ArticuloMetadata - manejar campos faltantes con valores por defecto
                try:
                    articulo_metadata = ArticuloMetadata(
                        medio=articulo_data.get("medio", "Unknown"),
                        titular=articulo_data.get("titular", "Sin titular"),
                        fecha_publicacion=articulo_data.get(
                            "fecha_publicacion", hecho_raw["fecha_ingreso"]
                        ),
                        url=articulo_data.get("url"),
                        area_geografica=articulo_data.get("area_geografica", "Unknown"),
                        tipo_medio=articulo_data.get("tipo_medio", "Unknown"),
                        autor=articulo_data.get("autor"),
                        seccion=articulo_data.get("seccion"),
                        es_opinion=articulo_data.get("es_opinion", False),
                        es_oficial=articulo_data.get("es_oficial", False),
                        resumen=articulo_data.get("resumen"),
                        categorias_asignadas=articulo_data.get(
                            "categorias_asignadas", []
                        ),
                        puntuacion_relevancia=articulo_data.get(
                            "puntuacion_relevancia"
                        ),
                        estado_procesamiento=articulo_data.get("estado_procesamiento"),
                    )
                except Exception as e:
                    logger.warning(
                        f"Error creando ArticuloMetadata para hecho {hecho_raw['id']}: {str(e)}. "
                        f"Usando valores por defecto."
                    )
                    # Crear metadata mínima en caso de error
                    articulo_metadata = ArticuloMetadata(
                        medio="Unknown",
                        titular="Sin titular",
                        fecha_publicacion=hecho_raw["fecha_ingreso"],
                        area_geografica="Unknown",
                        tipo_medio="Unknown",
                        es_opinion=False,
                        es_oficial=False,
                    )

                # Obtener relaciones para este hecho
                relaciones = relaciones_por_hecho.get(hecho_raw["id"], [])

                # Crear objeto HechoResponse
                try:
                    hecho_response = HechoResponse(
                        # Campos básicos
                        id=hecho_raw["id"],
                        contenido=hecho_raw["contenido"],
                        fecha_ocurrencia=hecho_raw["fecha_ocurrencia"],
                        precision_temporal=hecho_raw["precision_temporal"],
                        importancia=hecho_raw["importancia"],
                        tipo_hecho=hecho_raw["tipo_hecho"],
                        # Arrays de ubicación - manejar si vienen como strings o arrays
                        pais=hecho_raw.get("pais", [])
                        if isinstance(hecho_raw.get("pais"), list)
                        else [hecho_raw.get("pais")]
                        if hecho_raw.get("pais")
                        else [],
                        region=hecho_raw.get("region", [])
                        if isinstance(hecho_raw.get("region"), list)
                        else [hecho_raw.get("region")]
                        if hecho_raw.get("region")
                        else [],
                        ciudad=hecho_raw.get("ciudad", [])
                        if isinstance(hecho_raw.get("ciudad"), list)
                        else [hecho_raw.get("ciudad")]
                        if hecho_raw.get("ciudad")
                        else [],
                        # Metadata
                        etiquetas=hecho_raw.get("etiquetas", []),
                        frecuencia_citacion=hecho_raw.get("frecuencia_citacion", 0),
                        total_menciones=hecho_raw.get("total_menciones", 0),
                        menciones_confirmatorias=hecho_raw.get(
                            "menciones_confirmatorias", 0
                        ),
                        # Timestamps
                        fecha_ingreso=hecho_raw["fecha_ingreso"],
                        # Evaluación editorial
                        evaluacion_editorial=hecho_raw.get("evaluacion_editorial"),
                        editor_evaluador=hecho_raw.get("editor_evaluador"),
                        fecha_evaluacion_editorial=hecho_raw.get(
                            "fecha_evaluacion_editorial"
                        ),
                        justificacion_evaluacion_editorial=hecho_raw.get(
                            "justificacion_evaluacion_editorial"
                        ),
                        consenso_fuentes=hecho_raw.get("consenso_fuentes"),
                        # Eventos futuros
                        es_evento_futuro=hecho_raw.get("es_evento_futuro", False),
                        estado_programacion=hecho_raw.get("estado_programacion"),
                        # Metadata adicional
                        metadata=hecho_raw.get("metadata", {}),
                        # Datos relacionados
                        articulo_metadata=articulo_metadata,
                        relaciones=relaciones,
                    )
                    hechos_response.append(hecho_response)

                except Exception as e:
                    logger.error(
                        f"Error creando HechoResponse para hecho {hecho_raw['id']}: {str(e)}",
                        exc_info=True,
                    )
                    # Continuar con el siguiente hecho en lugar de fallar completamente
                    continue

            # Si medio filter fue aplicado, ajustar el conteo total
            # Esto es debido a una limitación de Supabase count con joins
            if filter_params.get("medio") is not None:
                total_count = result.count or len(hechos_response)

            logger.info(
                f"Retrieved {len(hechos_response)} hechos with relationships "
                f"(page: offset={offset}, limit={limit}, total={total_count})"
            )

            return hechos_response, total_count

        except DatabaseConnectionError:
            # Re-raise database connection errors as-is
            logger.error(
                "Database connection error in get_hechos_for_revision",
                extra={"filter_params": filter_params},
            )
            raise
        except Exception as e:
            # Log and re-raise other exceptions
            logger.error(
                f"Unexpected error fetching hechos for revision: {str(e)}",
                extra={"filter_params": filter_params},
                exc_info=True,
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
            medios_query = (
                self.supabase_client.table("articulos").select("medio").limit(1000)
            )
            medios_result = medios_query.execute()
            medios = list(
                set([item["medio"] for item in medios_result.data if item.get("medio")])
            )
            logger.debug(f"Successfully fetched {len(medios)} unique medios")
        except Exception as e:
            logger.error(f"Error fetching medios: {str(e)}")
            # Continue with empty list - graceful degradation

        # Query 2: Get unique paises from hechos table
        try:
            paises_query = (
                self.supabase_client.table("hechos").select("pais").limit(1000)
            )
            paises_result = paises_query.execute()
            paises = list(
                set([item["pais"] for item in paises_result.data if item.get("pais")])
            )
            logger.debug(f"Successfully fetched {len(paises)} unique paises")
        except Exception as e:
            logger.error(f"Error fetching paises: {str(e)}")
            # Continue with empty list - graceful degradation

        # Query 3a: Get minimum importancia
        try:
            min_importancia_query = (
                self.supabase_client.table("hechos")
                .select("importancia")
                .order("importancia", desc=False)
                .limit(1)
            )
            min_result = min_importancia_query.execute()
            if min_result.data:
                min_importancia = min_result.data[0]["importancia"]
            logger.debug(f"Successfully fetched min importancia: {min_importancia}")
        except Exception as e:
            logger.error(f"Error fetching min importancia: {str(e)}")
            # Continue with default value 1

        # Query 3b: Get maximum importancia
        try:
            max_importancia_query = (
                self.supabase_client.table("hechos")
                .select("importancia")
                .order("importancia", desc=True)
                .limit(1)
            )
            max_result = max_importancia_query.execute()
            if max_result.data:
                max_importancia = max_result.data[0]["importancia"]
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
            logger.warning("All filter option queries failed, returning defaults")

        return {
            "medios_disponibles": sorted(medios),
            "paises_disponibles": sorted(paises),
            "importancia_range": {"min": min_importancia, "max": max_importancia},
        }

    async def get_relaciones_para_hechos(
        self, hecho_ids: List[int]
    ) -> Dict[int, List[HechoRelacionInfo]]:
        """
        Obtiene las relaciones de primer grado para una lista de hechos.

        Busca en la tabla hecho_relacionado todas las relaciones donde los hechos
        aparezcan como origen o destino, y retorna un diccionario agrupado por hecho_id.

        Args:
            hecho_ids: Lista de IDs de hechos para buscar relaciones

        Returns:
            Diccionario donde las claves son hecho_ids y los valores son listas
            de HechoRelacionInfo con las relaciones encontradas

        Raises:
            Exception: Si la consulta a la base de datos falla
        """
        if not hecho_ids:
            logger.debug("No se proporcionaron hecho_ids, retornando diccionario vacío")
            return {}

        try:
            logger.info(f"Buscando relaciones para {len(hecho_ids)} hechos")

            # Consulta con filtro OR: buscar donde el hecho sea origen O destino
            # Usamos .or_ con .in_ para consultar arrays de manera eficiente
            relaciones_query = (
                self.supabase_client.table("hecho_relacionado")
                .select(
                    "hecho_origen_id, fecha_ocurrencia_origen, "
                    "hecho_destino_id, fecha_ocurrencia_destino, "
                    "tipo_relacion, fuerza_relacion, descripcion_relacion, fecha_deteccion"
                )
                .or_(
                    f"hecho_origen_id.in.({','.join(map(str, hecho_ids))}), "
                    f"hecho_destino_id.in.({','.join(map(str, hecho_ids))})"
                )
            )

            # Ejecutar consulta
            resultado = relaciones_query.execute()
            relaciones_raw = resultado.data or []

            logger.debug(f"Encontradas {len(relaciones_raw)} relaciones en total")

            # Procesar y agrupar relaciones por hecho_id
            relaciones_por_hecho: Dict[int, List[HechoRelacionInfo]] = {}

            for relacion_raw in relaciones_raw:
                # Crear objeto HechoRelacionado para usar sus métodos
                relacion = HechoRelacionado(**relacion_raw)

                # Para cada hecho en nuestra lista, verificar si está involucrado
                for hecho_id in hecho_ids:
                    if relacion.involves_hecho(hecho_id):
                        # Obtener el ID del hecho relacionado
                        hecho_relacionado_id = relacion.get_related_id(hecho_id)
                        direccion = relacion.get_direction_for_hecho(hecho_id)

                        if hecho_relacionado_id and direccion:
                            # Crear HechoRelacionInfo para la respuesta
                            relacion_info = HechoRelacionInfo(
                                hecho_relacionado_id=hecho_relacionado_id,
                                tipo_relacion=relacion.tipo_relacion,
                                fuerza_relacion=relacion.fuerza_relacion,
                                descripcion_relacion=relacion.descripcion_relacion,
                                direccion=direccion,
                            )

                            # Agregar al diccionario
                            if hecho_id not in relaciones_por_hecho:
                                relaciones_por_hecho[hecho_id] = []
                            relaciones_por_hecho[hecho_id].append(relacion_info)

            # Log de resultados
            for hecho_id, relaciones in relaciones_por_hecho.items():
                logger.debug(f"Hecho {hecho_id}: {len(relaciones)} relaciones")

            logger.info(
                f"Procesadas relaciones para {len(relaciones_por_hecho)} hechos "
                f"de {len(hecho_ids)} solicitados"
            )

            return relaciones_por_hecho

        except Exception as e:
            logger.error(
                f"Error obteniendo relaciones para hechos: {str(e)}",
                extra={
                    "hecho_ids": hecho_ids[:10]
                },  # Solo primeros 10 para evitar log extenso
                exc_info=True,
            )
            raise Exception(f"Failed to retrieve fact relationships: {str(e)}") from e
