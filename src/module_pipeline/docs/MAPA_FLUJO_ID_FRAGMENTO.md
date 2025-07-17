# Mapa Visual del Flujo de `id_fragmento`

## Flujo Completo del Pipeline

```mermaid
graph TD
    Start[Controller.py<br/>Línea 185] -->|Genera UUID| A[id_fragmento: uuid4]
    
    A --> F1[Fase 1: Triaje<br/>✅ 45 referencias]
    F1 -->|Propaga| F2[Fase 2: Simplificación<br/>✅ 6 referencias]
    F2 -->|Propaga| F3[Fase 3: Entidades<br/>✅ 12 referencias]
    F3 -->|Propaga| F4[Fase 4: Hechos<br/>✅ 12 referencias]
    F4 -->|Propaga| F5[Fase 5: Datos<br/>✅ 13 referencias]
    F5 -->|Propaga| F6[Fase 6: Citas<br/>✅ 13 referencias]
    F6 -->|Propaga| F7[Fase 7: Normalización<br/>✅ 3 referencias]
    
    F7 --> Build[Controller.py<br/>Línea 949<br/>Construir Payload]
    
    Build --> MetaDatos[metadatos_fragmento<br/>❌ NO incluye id_fragmento]
    
    MetaDatos --> PayloadBuilder[payload_builder.py<br/>construir_payload_fragmento]
    
    PayloadBuilder --> Model[FragmentoPersistenciaPayload<br/>❌ NO define id_fragmento]
    
    Model --> Supabase[supabase_service.py<br/>insertar_fragmento_completo]
    
    Supabase --> Error[ERROR E012<br/>Campo id_fragmento faltante]
    
    style A fill:#90EE90
    style F1 fill:#90EE90
    style F2 fill:#90EE90
    style F3 fill:#90EE90
    style F4 fill:#90EE90
    style F5 fill:#90EE90
    style F6 fill:#90EE90
    style F7 fill:#90EE90
    style MetaDatos fill:#FF6B6B
    style Model fill:#FF6B6B
    style Error fill:#FF0000,color:#FFFFFF
```

## Detalle del Problema

### 1. Generación (✅ CORRECTO)
```python
# controller.py, línea 185
fragmento_data = {
    "id_fragmento": str(uuid.uuid4()),  # ✅ Se genera correctamente
    "texto_original": contenido,
    "id_articulo_fuente": str(articulo_id),
}
```

### 2. Propagación por Fases (✅ CORRECTO)
Todas las fases mantienen y propagan el `id_fragmento`:
- **Fase 1**: Recibe como parámetro, retorna en resultado
- **Fases 2-6**: Toman de resultado anterior, incluyen en su resultado
- **Fase 7**: Lo toma de los hechos (posible punto débil)

### 3. Construcción del Payload (❌ PROBLEMA)
```python
# controller.py, línea 949
metadatos_fragmento = {
    # ❌ FALTA: "id_fragmento": str(fragmento.id_fragmento),
    "indice_secuencial_fragmento": fragmento.orden_en_articulo or 0,
    "titulo_seccion_fragmento": fragmento.metadata_adicional.get("titulo_seccion"),
    "contenido_texto_original_fragmento": fragmento.texto_original,
    "num_pagina_inicio_fragmento": fragmento.metadata_adicional.get("pagina_inicio"),
    "num_pagina_fin_fragmento": fragmento.metadata_adicional.get("pagina_fin")
}
```

### 4. Modelo de Persistencia (❌ PROBLEMA)
```python
# persistencia.py, línea 214
class FragmentoPersistenciaPayload(PersistenciaBaseModel):
    # ❌ NO define id_fragmento como campo
    indice_secuencial_fragmento: int
    titulo_seccion_fragmento: Optional[str]
    contenido_texto_original_fragmento: str
    # ... otros campos
```

## Puntos de Pérdida del ID

1. **Principal**: Entre el resultado del pipeline y `metadatos_fragmento`
2. **Secundario**: El modelo de persistencia no lo espera/valida

## Solución Inmediata

```python
# En controller.py, línea 949, añadir:
metadatos_fragmento = {
    "id_fragmento": str(fragmento.id_fragmento),  # ← AÑADIR ESTA LÍNEA
    "indice_secuencial_fragmento": fragmento.orden_en_articulo or 0,
    # ... resto de campos
}
```

## Verificación Post-Fix

1. El `id_fragmento` fluirá: Controller → PayloadBuilder → Supabase
2. La RPC `insertar_fragmento_completo` recibirá el ID
3. No más errores E012 de campo faltante

## Timeline del Error

```
[✅] Generación inicial del UUID
 ↓
[✅] Procesamiento Fase 1-7 (ID se mantiene)
 ↓
[❌] Construcción metadatos_fragmento (ID se pierde)
 ↓
[❌] PayloadBuilder recibe datos sin ID
 ↓
[❌] Supabase RPC falla al buscar ID
 ↓
[💥] ERROR E012
```

## Impacto

- **Fragmentos afectados**: 100% (todos fallan en persistencia)
- **Datos perdidos**: Todos los fragmentos procesados no se guardan
- **Criticidad**: ALTA - Bloquea todo el pipeline de persistencia