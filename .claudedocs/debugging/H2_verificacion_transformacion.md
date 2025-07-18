# H2: Verificación de Error en Transformación

## PROBLEMA IDENTIFICADO

El código en controller.py línea 202 está intentando acceder a `articulo_data['titular']`, pero según el JSON de prueba, el campo se llama `'titulo'` no `'titular'`.

### Mapeo actual en controller.py (líneas 198-217):
```python
articulo_data_procesable = {
    "titulo": articulo_data['titular'],  # ❌ ERROR: busca 'titular' pero JSON tiene 'titulo'
    "pais": articulo_data.get('area_geografica', 'España'),  # ❌ ERROR: crea campo 'pais'
    # ... otros campos
}
```

### Problemas detectados:

1. **Campo 'titulo' vs 'titular'**:
   - Controller busca: `articulo_data['titular']`
   - JSON contiene: `'titulo'`
   - Modelo espera: `'titular'`
   - RESULTADO: KeyError o falta el campo

2. **Campo 'pais' vs 'area_geografica'**:
   - Controller crea: campo `'pais'`
   - Modelo espera: campo `'area_geografica'`
   - RESULTADO: ValidationError por campo extra no permitido

3. **Campos extra no esperados por el modelo**:
   - `fuente_original`
   - `medio_url_principal`
   - `contenido_html`
   - Estos campos se agregan al dict pero el modelo no los acepta

### CONCLUSIÓN H2: ✅ CONFIRMADA

La transformación está mal implementada:
1. Intenta leer campos que no existen en el JSON
2. Crea campos con nombres incorrectos para el modelo
3. Incluye campos que el modelo no acepta