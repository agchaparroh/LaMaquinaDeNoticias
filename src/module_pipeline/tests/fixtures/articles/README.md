# Test Articles

Carpeta para almacenar artículos de prueba extraídos de spiders reales.

## Estructura
- `raw/` - Archivos .json.gz originales del spider
- `json/` - Archivos JSON descomprimidos listos para usar

## Uso

### 1. Capturar artículos nuevos
```bash
cd ~/projects/LaMaquinaDeNoticias
chmod +x capture_articles.sh
./capture_articles.sh
```

### 2. Probar un artículo
```bash
cd src/module_pipeline/test_articles
python test_article.py json/articulo1.json
```

### 3. Probar todos los artículos
```bash
python test_article.py all
```

## Notas
- Los archivos se extraen del spider infobae_america_latina
- Por defecto extrae 100 artículos
- El module_connector se detiene temporalmente durante la captura