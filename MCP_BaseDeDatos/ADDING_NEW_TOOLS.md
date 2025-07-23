# Guía para agregar nuevas herramientas a supabase-mcp-server

Esta guía explica cómo extender el servidor MCP de Supabase con nuevas herramientas de forma sistemática.

## Resumen del proceso

1. Agregar el nombre de la herramienta al enum `ToolName`
2. Crear la descripción en YAML
3. Registrar la herramienta en `ToolRegistry`
4. Implementar la lógica en `FeatureManager`
5. (Opcional) Crear servicios o configuraciones de seguridad
6. Escribir tests

## Paso 1: Agregar al enum ToolName

Edita `supabase_mcp/tools/manager.py` y agrega tu herramienta:

```python
class ToolName(str, Enum):
    # Herramientas existentes...
    
    # Tu nueva herramienta
    MI_NUEVA_HERRAMIENTA = "mi_nueva_herramienta"
```

## Paso 2: Crear descripción en YAML

Crea o edita un archivo en `supabase_mcp/tools/descriptions/`. Por ejemplo, `supabase_mcp/tools/descriptions/mi_herramienta.yaml`:

```yaml
mi_nueva_herramienta: |
  Descripción breve de lo que hace la herramienta.
  
  Detalles adicionales sobre su funcionamiento y parámetros.
  
  SEGURIDAD: Especifica si requiere modo UNSAFE o tiene restricciones especiales.
```

## Paso 3: Registrar en ToolRegistry

Edita `supabase_mcp/tools/registry.py` y agrega el decorador de tu herramienta:

```python
@mcp.tool(description=tool_manager.get_description(ToolName.MI_NUEVA_HERRAMIENTA))
async def mi_nueva_herramienta(
    parametro1: str,
    parametro2: int = 10,
    parametro_opcional: str | None = None
) -> dict[str, Any]:
    """Docstring corto para la herramienta."""
    return await feature_manager.execute_tool(
        ToolName.MI_NUEVA_HERRAMIENTA,
        services_container=services_container,
        parametro1=parametro1,
        parametro2=parametro2,
        parametro_opcional=parametro_opcional
    )
```

## Paso 4: Implementar en FeatureManager

Edita `supabase_mcp/core/feature_manager.py`:

### 4.1 Agregar al switch de execute_tool:

```python
async def execute_tool(self, tool_name: ToolName, services_container: "ServicesContainer", **kwargs: Any) -> Any:
    # Validación existente...
    
    # Agregar tu caso
    elif tool_name == ToolName.MI_NUEVA_HERRAMIENTA:
        return await self.mi_nueva_herramienta(services_container, **kwargs)
```

### 4.2 Implementar el método:

```python
async def mi_nueva_herramienta(
    self, 
    container: "ServicesContainer",
    parametro1: str,
    parametro2: int = 10,
    parametro_opcional: str | None = None
) -> dict[str, Any]:
    """Implementación de la lógica de tu herramienta."""
    
    # Ejemplo usando servicios existentes
    query_manager = container.query_manager
    api_manager = container.api_manager
    
    # Si necesitas verificar seguridad
    safety_manager = container.safety_manager
    safety_manager.validate_operation(
        ClientType.DATABASE,  # o ClientType.API
        operation_info,
        has_confirmation=False
    )
    
    # Tu lógica aquí
    resultado = await api_manager.execute_request(
        method="GET",
        path=f"/v1/projects/{parametro1}",
        path_params={},
        request_params={"limit": parametro2},
        request_body={}
    )
    
    return {
        "status": "success",
        "data": resultado,
        "parametro_opcional": parametro_opcional
    }
```

## Paso 5: (Opcional) Crear servicios personalizados

Si tu herramienta requiere lógica compleja, crea un servicio dedicado:

### 5.1 Crear el servicio:

```python
# supabase_mcp/services/mi_servicio/mi_manager.py
from typing import Any
from supabase_mcp.logger import logger

class MiServicioManager:
    """Manager para operaciones de mi servicio."""
    
    def __init__(self, postgres_client, safety_manager):
        self.postgres_client = postgres_client
        self.safety_manager = safety_manager
    
    async def realizar_operacion(self, parametros: dict[str, Any]) -> dict[str, Any]:
        """Realiza la operación principal del servicio."""
        logger.info(f"Ejecutando operación con parámetros: {parametros}")
        
        # Tu lógica aquí
        query = "SELECT * FROM mi_tabla WHERE condicion = $1"
        result = await self.postgres_client.execute(query, [parametros["valor"]])
        
        return {
            "resultado": result,
            "procesado": True
        }
```

### 5.2 Agregar al ServicesContainer:

```python
# En supabase_mcp/core/container.py
def initialize_services(self, settings: Settings) -> None:
    # Servicios existentes...
    
    # Tu servicio
    self.mi_servicio_manager = MiServicioManager(
        postgres_client=self.postgres_client,
        safety_manager=self.safety_manager
    )
```

## Paso 6: Escribir tests

Crea tests para tu herramienta en `tests/`:

```python
# tests/tools/test_mi_herramienta.py
import pytest
from supabase_mcp.tools.manager import ToolName
from supabase_mcp.core.feature_manager import FeatureManager

@pytest.mark.asyncio
async def test_mi_nueva_herramienta(mock_services_container):
    """Test de mi nueva herramienta."""
    feature_manager = FeatureManager(mock_api_client)
    
    resultado = await feature_manager.execute_tool(
        ToolName.MI_NUEVA_HERRAMIENTA,
        mock_services_container,
        parametro1="test",
        parametro2=5
    )
    
    assert resultado["status"] == "success"
    assert "data" in resultado
```

## Ejemplo completo: Herramienta de estadísticas de base de datos

### 1. En `tools/manager.py`:
```python
DATABASE_STATS = "database_stats"
```

### 2. En `tools/descriptions/database.yaml`:
```yaml
database_stats: |
  Obtiene estadísticas detalladas de uso de la base de datos.
  
  Retorna información sobre:
  - Tamaño total de la base de datos
  - Número de conexiones activas
  - Queries más lentas
  - Tablas más grandes
  
  SEGURIDAD: Esta es una operación de solo lectura, segura en modo SAFE.
```

### 3. En `tools/registry.py`:
```python
@mcp.tool(description=tool_manager.get_description(ToolName.DATABASE_STATS))
async def database_stats(include_slow_queries: bool = True) -> QueryResult:
    """Obtiene estadísticas de la base de datos."""
    return await feature_manager.execute_tool(
        ToolName.DATABASE_STATS,
        services_container=services_container,
        include_slow_queries=include_slow_queries
    )
```

### 4. En `core/feature_manager.py`:
```python
elif tool_name == ToolName.DATABASE_STATS:
    return await self.database_stats(services_container, **kwargs)

async def database_stats(
    self, 
    container: "ServicesContainer",
    include_slow_queries: bool = True
) -> QueryResult:
    """Obtiene estadísticas detalladas de la base de datos."""
    query_manager = container.query_manager
    
    # Query para estadísticas básicas
    stats_query = """
    SELECT 
        pg_database_size(current_database()) as database_size,
        (SELECT count(*) FROM pg_stat_activity) as active_connections,
        (SELECT count(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')) as total_tables
    """
    
    result = await query_manager.handle_query(stats_query)
    
    if include_slow_queries:
        # Agregar queries lentas
        slow_queries = """
        SELECT query, mean_exec_time, calls 
        FROM pg_stat_statements 
        ORDER BY mean_exec_time DESC 
        LIMIT 5
        """
        slow_result = await query_manager.handle_query(slow_queries)
        result.data["slow_queries"] = slow_result.data
    
    return result
```

## Mejores prácticas

1. **Validación de parámetros**: Usa type hints y valida entrada
2. **Manejo de errores**: Captura excepciones específicas
3. **Logging**: Registra operaciones importantes con `logger`
4. **Seguridad**: Siempre considera el nivel de riesgo de tu operación
5. **Documentación**: Sé claro en las descripciones YAML
6. **Tests**: Incluye casos de éxito y error

## Conclusión

Este diseño modular permite agregar funcionalidad sin modificar el núcleo del sistema. Cada herramienta es independiente pero puede reutilizar toda la infraestructura existente de servicios, seguridad y logging.