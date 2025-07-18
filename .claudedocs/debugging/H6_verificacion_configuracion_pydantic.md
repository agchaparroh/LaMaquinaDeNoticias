# H6: Verificación de Configuración de Pydantic

## HALLAZGO CRÍTICO

ArticuloProcesableItem hereda de PipelineBaseModel, que tiene:

```python
model_config = {
    "extra": "forbid",  # ❌ PROHIBE CAMPOS EXTRA
    ...
}
```

### Implicaciones:

1. **ArticuloProcesableItem NO acepta campos extra**
2. Si el diccionario contiene campos no definidos en el modelo, fallará
3. Los campos problemáticos del diccionario:
   - `titulo` (modelo espera `titular`)
   - `pais` (modelo espera `area_geografica`)
   - `fuente_original` (no existe en modelo)
   - `medio_url_principal` (no existe en modelo)
   - `contenido_html` (no existe en modelo)

### CONCLUSIÓN H6: ✅ CONFIRMADA

La configuración `extra="forbid"` en PipelineBaseModel está causando que 
ArticuloProcesableItem rechace campos extra. Esto explica los errores:
- "Extra inputs are not permitted"