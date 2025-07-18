# H7: Verificación de Construcción del Diccionario

## ANÁLISIS DEL DICCIONARIO EN controller.py (líneas 198-217)

### Campos en el diccionario `articulo_data_procesable`:
```python
{
    "id_articulo": id_articulo,                          ✅ OK
    "contenido_texto": contenido,                         ✅ OK
    "medio": articulo_data['medio'],                      ✅ OK
    "titulo": articulo_data['titular'],                   ❌ ERROR: campo se llama 'titulo', no 'titular'
    "fecha_publicacion": str(articulo_data['fecha_publicacion']), ✅ OK
    "autor": articulo_data.get('autor'),                  ✅ OK
    "pais": articulo_data.get('area_geografica', 'España'), ❌ ERROR: campo se llama 'pais', modelo espera 'area_geografica'
    "tipo_medio": articulo_data['tipo_medio'],            ✅ OK
    "idioma": articulo_data.get('idioma', 'es'),          ✅ OK
    "seccion": articulo_data.get('seccion'),              ✅ OK
    "es_opinion": articulo_data.get('es_opinion', False), ✅ OK
    "es_oficial": articulo_data.get('es_oficial', False), ✅ OK
    "url": articulo_data.get('url'),                      ✅ OK
    "fuente_original": articulo_data.get('fuente_original'), ❌ ERROR: campo no existe en modelo
    "medio_url_principal": articulo_data.get('medio_url_principal'), ❌ ERROR: campo no existe en modelo
    "contenido_html": articulo_data.get('contenido_html'), ❌ ERROR: campo no existe en modelo
    "etiquetas_fuente": articulo_data.get('etiquetas_fuente'), ✅ OK
    "metadata_adicional": articulo_data.get('metadata', {}) ✅ OK
}
```

### PROBLEMAS IDENTIFICADOS:

1. **Línea 202**: Intenta leer `articulo_data['titular']` pero el JSON tiene `titulo`
   - Esto causará KeyError

2. **Línea 205**: Crea campo `pais` pero el modelo espera `area_geografica`
   - Esto causará ValidationError

3. **Líneas 212-214**: Agrega campos que el modelo no acepta
   - fuente_original
   - medio_url_principal  
   - contenido_html

### CONCLUSIÓN H7: ✅ CONFIRMADA

El diccionario está mal construido:
1. Lee campos con nombres incorrectos del JSON
2. Crea campos con nombres incorrectos para el modelo
3. Incluye campos que el modelo rechaza por `extra="forbid"`