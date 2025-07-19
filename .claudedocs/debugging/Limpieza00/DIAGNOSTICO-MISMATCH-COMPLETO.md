# Diagnóstico Completo: Mismatch entre Pipeline y Supabase RPC

## Resumen Ejecutivo

Existe un **desajuste crítico** entre la estructura de datos que genera el pipeline de procesamiento y lo que esperan las funciones RPC de Supabase. Este mismatch ocurre en múltiples niveles y afecta la persistencia de artículos completos.

## 1. Análisis del Flujo de Datos

### 1.1 Flujo de Generación del Payload

```
PipelineCoordinator._generar_payload_articulo_completo()
    ↓
PayloadBuilder.construir_payload_articulo_from_model()
    ↓
SupabaseService.insertar_articulo_completo()
    ↓
RPC: insertar_articulo_completo(datos_json JSONB)
```

### 1.2 Transformaciones en Cada Paso

#### Paso 1: PipelineCoordinator genera estructura inicial
```python
# En _generar_payload_articulo_completo (línea 753-821)
hechos_data = [{
    "id_temporal_hecho": str(hecho.id_hecho),
    "descripcion_hecho": hecho.texto_original_del_hecho,
    "tipo_hecho": hecho.metadata_hecho.tipo_hecho if hasattr(hecho.metadata_hecho, 'tipo_hecho') else "evento",
    # ... más campos
}]

entidades_data = [{
    "id": str(entidad.id_entidad),  # ⚠️ Campo "id" en lugar de "id_temporal_entidad"
    "nombre": entidad.nombre_entidad_normalizada or entidad.texto_entidad,
    "tipo": entidad.tipo_entidad,
    # ... más campos
}]
```

#### Paso 2: PayloadBuilder NO transforma correctamente
```python
# En construir_payload_articulo_from_model (línea 304-323)
metadatos_articulo = {
    "url": articulo_model.url,
    "storage_path": None,  # ⚠️ Campo requerido por RPC pero no se proporciona
    "fuente_original": None,  # ⚠️ Campo no existe en ArticuloProcesableItem
    "medio": articulo_model.medio,
    # ... más campos
}
```

#### Paso 3: SupabaseService envía estructura incorrecta
```python
# En insertar_articulo_completo (línea 254-256)
response = self.client.rpc(
    'insertar_articulo_completo',
    {'datos_json': payload_dict}  # ✓ Correcto: envuelve en 'datos_json'
).execute()
```

## 2. Mismatches Específicos Identificados

### 2.1 Estructura Principal del Payload

**Pipeline genera:**
```json
{
    // Campos planos mezclados
    "url": "...",
    "medio": "...",
    "hechos_extraidos": [...],
    "entidades_autonomas": [...]
}
```

**RPC espera:**
```json
{
    "articulo_metadata": {
        "url": "...",
        "storage_path": "...",  // REQUERIDO
        "medio": "..."
    },
    "hechos": [...],
    "entidades": [...],
    "relaciones": {
        "hecho_entidad": [...],
        "hecho_relacionado": [...],
        "entidad_relacion": [...]
    }
}
```

### 2.2 Campo storage_path

- **Estado**: CRÍTICO - Campo requerido faltante
- **Validación SQL** (línea 195-201):
```sql
IF NOT (datos_json->'articulo_metadata'->>'storage_path' ~ '^[^/]+/\d{4}/\d{2}/\d{2}/[^/]+\.(html|txt)\.gz$') THEN
    RETURN jsonb_build_object(
        'status', 'error',
        'mensaje', 'Formato de storage_path inválido...'
    );
END IF;
```
- **Impacto**: La RPC falla inmediatamente sin este campo

### 2.3 Estructura de Entidades

**Pipeline genera:**
```json
{
    "id": "123",  // ⚠️ Debería ser "id_temporal_entidad"
    "nombre": "Pedro Sánchez",
    "tipo": "PERSONA",
    "metadata_entidad": {...}
}
```

**RPC espera:**
```json
{
    "id": "123",  // ID temporal para mapeo
    "nombre": "Pedro Sánchez",
    "tipo": "PERSONA",
    "db_id": 456,  // Si ya existe en BD
    "alias": ["alias1", "alias2"],
    "metadata": {...}  // Sin el sufijo "_entidad"
}
```

### 2.4 Estructura de Hechos

**Pipeline genera:**
```json
{
    "id_temporal_hecho": "1",
    "descripcion_hecho": "...",
    "fecha_ocurrencia_hecho_inicio": "2024-01-01T00:00:00Z",
    "fecha_ocurrencia_hecho_fin": "2024-01-01T00:00:00Z"
}
```

**RPC espera:**
```json
{
    "id": "1",
    "contenido": "...",  // ⚠️ Campo diferente
    "fecha": {
        "inicio": "2024-01-01T00:00:00Z",
        "fin": "2024-01-01T00:00:00Z"
    }
}
```

### 2.5 Relaciones

**Pipeline NO genera estructura de relaciones**

**RPC espera:**
```json
{
    "relaciones": {
        "hecho_entidad": [{
            "hecho_id": "1",
            "entidad_id": "2",
            "tipo_relacion": "protagonista"
        }],
        "hecho_relacionado": [...],
        "entidad_relacion": [...]
    }
}
```

## 3. Root Cause Analysis

### 3.1 Decisiones Arquitectónicas Problemáticas

1. **Modelos de persistencia desacoplados**: Los modelos en `persistencia.py` no reflejan la estructura esperada por las RPCs.

2. **Falta de capa de transformación**: No existe una capa que transforme los modelos del pipeline a la estructura exacta de la RPC.

3. **Campos legacy**: El código mantiene compatibilidad con estructuras antiguas (ej: "titulo" vs "titular").

4. **Información faltante**: El pipeline no tiene acceso a cierta información requerida (ej: storage_path).

### 3.2 Flujo de Información Roto

```
ArticuloProcesableItem (entrada)
    ↓
    No tiene: storage_path, fuente_original, medio_url_principal
    ↓
PipelineCoordinator (procesamiento)
    ↓
    Genera estructura plana, no anidada
    ↓
PayloadBuilder (construcción)
    ↓
    No transforma a estructura esperada por RPC
    ↓
SupabaseService (persistencia)
    ↓
    Envía estructura incorrecta
    ↓
RPC falla o procesa incorrectamente
```

## 4. Impactos Específicos

### 4.1 Fallos Inmediatos
- ❌ Validación de storage_path falla
- ❌ Estructura articulo_metadata no existe
- ❌ Campos de entidades incorrectos

### 4.2 Pérdida de Datos
- ⚠️ Relaciones entre hechos y entidades no se persisten
- ⚠️ Metadata de entidades se pierde
- ⚠️ Información de fechas se malforma

### 4.3 Inconsistencias
- 🔄 IDs temporales vs IDs de BD mal mapeados
- 🔄 Campos con nombres diferentes causan valores null

## 5. Solución Propuesta

### 5.1 Crear Capa de Transformación

```python
class RPCPayloadTransformer:
    """Transforma payloads del pipeline al formato RPC."""
    
    def transform_articulo_payload(self, payload_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma payload de artículo al formato esperado por RPC."""
        
        # Extraer y reorganizar metadata
        articulo_metadata = {
            "url": payload_dict.get("url"),
            "storage_path": self._generate_storage_path(payload_dict),
            "medio": payload_dict.get("medio"),
            # ... mapear todos los campos
        }
        
        # Transformar hechos
        hechos = self._transform_hechos(payload_dict.get("hechos_extraidos", []))
        
        # Transformar entidades
        entidades = self._transform_entidades(payload_dict.get("entidades_autonomas", []))
        
        # Extraer relaciones
        relaciones = self._extract_relaciones(hechos, entidades)
        
        return {
            "articulo_metadata": articulo_metadata,
            "hechos": hechos,
            "entidades": entidades,
            "relaciones": relaciones,
            "citas_textuales": payload_dict.get("citas_textuales_extraidas", []),
            "datos_cuantitativos": payload_dict.get("datos_cuantitativos_extraidos", [])
        }
```

### 5.2 Modificar SupabaseService

```python
def insertar_articulo_completo(self, payload: Union[Dict[str, Any], BaseModel]) -> Optional[Dict[str, Any]]:
    """Llama a la RPC insertar_articulo_completo con transformación."""
    
    # Convertir a dict si es necesario
    payload_dict = self._validar_estructura_payload(payload, 'articulo')
    
    # NUEVO: Transformar al formato RPC
    transformer = RPCPayloadTransformer()
    rpc_payload = transformer.transform_articulo_payload(payload_dict)
    
    # Llamar RPC con payload transformado
    response = self.client.rpc(
        'insertar_articulo_completo',
        {'datos_json': rpc_payload}
    ).execute()
```

### 5.3 Actualizar ArticuloProcesableItem

```python
class ArticuloProcesableItem(BaseModel):
    # Campos existentes...
    
    # Nuevos campos requeridos
    storage_path: Optional[str] = None
    fuente_original: Optional[str] = None
    medio_url_principal: Optional[str] = None
    
    def generate_storage_path(self) -> str:
        """Genera storage_path según formato requerido."""
        from datetime import datetime
        import hashlib
        
        fecha = self.fecha_publicacion or datetime.now()
        url_hash = hashlib.md5(self.url.encode()).hexdigest()[:8]
        
        return f"{self.medio}/{fecha.year:04d}/{fecha.month:02d}/{fecha.day:02d}/{url_hash}.html.gz"
```

## 6. Recomendaciones Inmediatas

1. **CRÍTICO**: Implementar generación de storage_path
2. **ALTO**: Crear transformador de payloads
3. **MEDIO**: Actualizar modelos de entrada con campos faltantes
4. **MEDIO**: Documentar estructura exacta esperada por RPCs
5. **BAJO**: Refactorizar modelos de persistencia para alinearse con RPCs

## 7. Conclusión

El mismatch entre el pipeline y las RPCs es sistemático y requiere una intervención arquitectónica. La solución más práctica es implementar una capa de transformación que adapte los payloads generados por el pipeline a la estructura exacta esperada por las RPCs de Supabase.

---

**Fecha de diagnóstico**: 2025-07-19
**Versión del sistema**: 1.0.0
**Componentes analizados**: 
- PipelineCoordinator v1.0
- PayloadBuilder v1.0
- SupabaseService v1.0
- RPC insertar_articulo_completo v1.0