# Guía de Solución de Problemas - Scrapyd + ScrapydWeb + Spidermon

Esta guía ayuda a resolver los problemas más comunes del sistema de extracción de noticias.

## 📋 Índice
1. [Problemas de Acceso](#problemas-de-acceso)
2. [Problemas con Servicios](#problemas-con-servicios)
3. [Problemas de Spiders](#problemas-de-spiders)
4. [Problemas de Extracción](#problemas-de-extracción)
5. [Problemas de Alertas](#problemas-de-alertas)
6. [Problemas de Rendimiento](#problemas-de-rendimiento)
7. [Comandos de Diagnóstico](#comandos-de-diagnóstico)

---

## 🔐 Problemas de Acceso

### "No puedo acceder a ScrapydWeb"

**Síntomas:**
- Navegador muestra "No se puede acceder a este sitio"
- ERR_CONNECTION_REFUSED

**Diagnóstico:**
```bash
# 1. Verificar que el servicio está corriendo
docker-compose ps | grep scrapydweb

# 2. Verificar logs
docker-compose logs scrapydweb --tail=50

# 3. Verificar puerto
netstat -tuln | grep 5000
```

**Soluciones:**
1. **Servicio no está corriendo:**
   ```bash
   docker-compose up -d scrapydweb
   ```

2. **Puerto ocupado:**
   ```bash
   # Ver qué usa el puerto
   sudo lsof -i :5000
   # Cambiar puerto en docker-compose.yml
   ```

3. **Firewall bloqueando:**
   ```bash
   # Permitir puerto (Ubuntu)
   sudo ufw allow 5000
   ```

### "Contraseña incorrecta en ScrapydWeb"

**Diagnóstico:**
```bash
# Ver configuración actual
docker-compose exec scrapydweb env | grep SCRAPYDWEB
```

**Soluciones:**
1. **Resetear contraseña:**
   ```bash
   # Editar .env
   SCRAPYDWEB_PASSWORD=nueva_contraseña
   
   # Reiniciar
   docker-compose restart scrapydweb
   ```

2. **Verificar mayúsculas/minúsculas**
   - Las contraseñas son sensibles a mayúsculas

---

## 🔧 Problemas con Servicios

### "Scrapyd no responde"

**Síntomas:**
- API devuelve error de conexión
- ScrapydWeb muestra servidor offline

**Diagnóstico:**
```bash
# 1. Estado del servicio
docker-compose ps scrapyd

# 2. Logs detallados
docker-compose logs scrapyd --tail=100

# 3. Probar API directamente
curl http://localhost:6800/daemonstatus.json
```

**Soluciones:**

1. **Servicio caído:**
   ```bash
   docker-compose restart scrapyd
   ```

2. **Error de configuración:**
   ```bash
   # Verificar archivo de configuración
   docker-compose exec scrapyd cat /etc/scrapyd/scrapyd.conf
   
   # Si está mal, corregir y reiniciar
   docker-compose restart scrapyd
   ```

3. **Problema de red Docker:**
   ```bash
   # Recrear servicios
   docker-compose down
   docker-compose up -d
   ```

### "ScrapydWeb no se conecta a Scrapyd"

**Síntomas:**
- Dashboard muestra "Connection Error"
- Servers aparecen en rojo

**Diagnóstico:**
```bash
# Verificar conectividad entre contenedores
docker-compose exec scrapydweb ping -c 3 scrapyd
```

**Soluciones:**

1. **Configuración incorrecta:**
   ```python
   # En scrapydweb_settings_v10.py debe ser:
   SCRAPYD_SERVERS = ['scrapyd:6800']  # NO localhost
   ```

2. **Problema de DNS interno:**
   ```bash
   # Verificar red Docker
   docker network ls
   docker network inspect lamaquina_network
   ```

---

## 🕷️ Problemas de Spiders

### "Spider no se ejecuta"

**Síntomas:**
- Click en "Run" pero nada pasa
- No aparece en Jobs

**Diagnóstico:**
```bash
# 1. Verificar que el proyecto está desplegado
curl http://localhost:6800/listprojects.json

# 2. Verificar que el spider existe
curl http://localhost:6800/listspiders.json?project=scraper_core

# 3. Ver logs de Scrapyd
docker-compose logs scrapyd | grep ERROR
```

**Soluciones:**

1. **Proyecto no desplegado:**
   ```bash
   cd src/module_scraper
   scrapyd-deploy default -p scraper_core
   ```

2. **Error en el spider:**
   ```bash
   # Probar localmente primero
   scrapy crawl nombre_spider -L DEBUG
   ```

3. **Falta de recursos:**
   ```bash
   # Ver uso de recursos
   docker stats
   
   # Aumentar límites en docker-compose.yml
   ```

### "Spider se ejecuta pero extrae 0 items"

**Síntomas:**
- Jobs muestra "Finished" pero Items = 0
- No hay errores visibles

**Diagnóstico:**
```bash
# 1. Ver logs completos del spider
# En ScrapydWeb: Jobs → Click en spider → Log

# 2. Buscar warnings
docker-compose logs module_scraper | grep -i "warning\|error" | grep nombre_spider
```

**Soluciones:**

1. **Selectores rotos (más común):**
   - El sitio cambió su HTML
   - Revisar selectores XPath/CSS
   - Actualizar spider

2. **Bloqueo por robots.txt:**
   ```python
   # Temporalmente en settings.py
   ROBOTSTXT_OBEY = False  # Solo para debug
   ```

3. **Redirecciones no seguidas:**
   ```python
   # En spider
   meta={'dont_redirect': False}
   ```

---

## 📊 Problemas de Extracción

### "Muchos errores 403 Forbidden"

**Síntomas:**
- Alerta: "Tasa de error HTTP: 15%"
- Logs muestran muchos 403

**Diagnóstico:**
```bash
# Contar errores por código
docker-compose logs module_scraper | grep -o "status=[0-9]*" | sort | uniq -c
```

**Soluciones:**

1. **Ajustar velocidad:**
   ```python
   # En settings.py o custom_settings del spider
   DOWNLOAD_DELAY = 3  # Aumentar delay
   CONCURRENT_REQUESTS = 1  # Reducir concurrencia
   ```

2. **Rotar User-Agent:**
   ```python
   # Ya está configurado, verificar que funcione
   DOWNLOADER_MIDDLEWARES = {
       'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
   }
   ```

3. **Usar proxies:**
   ```python
   # Agregar middleware de proxies
   # Configurar lista de proxies
   ```

### "Campos críticos vacíos"

**Síntomas:**
- Alerta: "Campo crítico titulo: 15% con problemas"
- Items incompletos en base de datos

**Diagnóstico:**
```python
# Script de diagnóstico
docker-compose exec module_scraper python -c "
from scrapy.selector import Selector
import requests

url = 'https://ejemplo.com/noticia'
response = requests.get(url)
sel = Selector(text=response.text)

# Probar selectores
titulo = sel.xpath('//h1/text()').get()
print(f'Titulo: {titulo}')
"
```

**Soluciones:**

1. **Actualizar selectores:**
   ```python
   # Usar selectores más robustos
   # Malo:
   titulo = response.xpath('//div[@class="title"]/text()').get()
   
   # Mejor:
   titulo = response.xpath('//h1/text() | //div[contains(@class,"title")]/text()').get()
   ```

2. **Manejar casos especiales:**
   ```python
   # Valores por defecto
   titulo = response.xpath('//h1/text()').get(default='Sin título')
   ```

---

## 🔔 Problemas de Alertas

### "No recibo alertas por email"

**Diagnóstico:**
```bash
# 1. Verificar configuración
docker-compose exec module_scraper env | grep SMTP

# 2. Buscar errores de envío
docker-compose logs module_scraper | grep -i "smtp\|email\|alert"
```

**Soluciones:**

1. **Configuración SMTP incorrecta:**
   ```env
   # Gmail requiere contraseña de aplicación
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=tu-email@gmail.com
   SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # Contraseña de aplicación
   ```

2. **Firewall bloqueando puerto:**
   ```bash
   # Probar conexión
   telnet smtp.gmail.com 587
   ```

3. **Credenciales incorrectas:**
   - Generar contraseña de aplicación en Gmail
   - No usar contraseña normal de la cuenta

### "Webhook no funciona"

**Diagnóstico:**
```bash
# Probar webhook manualmente
curl -X POST https://tu-webhook-url.com \
  -H "Content-Type: application/json" \
  -d '{"test": "mensaje"}'
```

**Soluciones:**

1. **URL incorrecta:**
   - Verificar que incluye https://
   - Comprobar que no hay espacios

2. **Timeout:**
   ```python
   # Aumentar timeout en actions.py
   response = requests.post(url, timeout=30)
   ```

---

## ⚡ Problemas de Rendimiento

### "Spiders muy lentos"

**Síntomas:**
- Extracción toma horas
- Timeout frecuentes

**Diagnóstico:**
```bash
# 1. Ver métricas de tiempo
docker-compose logs module_scraper | grep "download_latency"

# 2. Verificar recursos
docker stats module_scraper
```

**Soluciones:**

1. **Optimizar configuración:**
   ```python
   # Aumentar concurrencia (con cuidado)
   CONCURRENT_REQUESTS = 8
   CONCURRENT_REQUESTS_PER_DOMAIN = 4
   
   # Reducir delays si es seguro
   DOWNLOAD_DELAY = 1
   ```

2. **Usar caché HTTP:**
   ```python
   # En settings.py
   HTTPCACHE_ENABLED = True
   HTTPCACHE_EXPIRATION_SECS = 3600
   ```

### "Sistema consume mucha memoria"

**Diagnóstico:**
```bash
# Ver uso de memoria
docker stats --no-stream
```

**Soluciones:**

1. **Limitar items en memoria:**
   ```python
   # Procesar en lotes
   CONCURRENT_ITEMS = 100
   ```

2. **Limitar memoria Docker:**
   ```yaml
   # docker-compose.yml
   services:
     module_scraper:
       mem_limit: 2g
   ```

---

## 🛠️ Comandos de Diagnóstico

### Comandos esenciales para debugging:

```bash
# 1. Ver todos los logs en tiempo real
docker-compose logs -f

# 2. Logs de un servicio específico
docker-compose logs -f scrapyd --tail=100

# 3. Buscar errores en todos los logs
docker-compose logs | grep -i error | less

# 4. Ver estado de todos los servicios
docker-compose ps

# 5. Inspeccionar red Docker
docker network inspect lamaquina_network

# 6. Ejecutar comandos dentro del contenedor
docker-compose exec module_scraper bash

# 7. Ver procesos del sistema
docker-compose exec module_scraper ps aux

# 8. Verificar conectividad
docker-compose exec scrapydweb curl http://scrapyd:6800/daemonstatus.json

# 9. Limpiar y reiniciar todo
docker-compose down
docker-compose up -d

# 10. Ver uso de recursos en tiempo real
watch docker stats
```

### Script de diagnóstico completo:

```bash
#!/bin/bash
# diagnostic.sh

echo "=== DIAGNÓSTICO DEL SISTEMA ==="
echo "1. Estado de servicios:"
docker-compose ps

echo -e "\n2. Conectividad Scrapyd:"
curl -s http://localhost:6800/daemonstatus.json | python -m json.tool || echo "FALLO"

echo -e "\n3. Conectividad ScrapydWeb:"
curl -s -I http://localhost:5000 | head -n 1

echo -e "\n4. Últimos errores:"
docker-compose logs --tail=50 | grep -i error | tail -10

echo -e "\n5. Uso de recursos:"
docker stats --no-stream

echo -e "\n6. Spiders disponibles:"
curl -s http://localhost:6800/listspiders.json?project=scraper_core | python -m json.tool

echo -e "\nDiagnóstico completado"
```

---

## 🆘 Soporte adicional

Si el problema persiste después de intentar estas soluciones:

1. **Recopilar información:**
   - Logs completos del servicio afectado
   - Configuración actual (.env, settings.py)
   - Pasos para reproducir el problema

2. **Buscar en documentación:**
   - [Scrapy docs](https://docs.scrapy.org)
   - [Scrapyd docs](https://scrapyd.readthedocs.io)
   - [Spidermon docs](https://spidermon.readthedocs.io)

3. **Contactar soporte:**
   - Incluir output del script de diagnóstico
   - Describir qué se intentó resolver
   - Indicar urgencia del problema

---

📖 **Siguiente**: [Guía de Deployment](DEPLOYMENT_GUIDE.md) - Cómo desplegar spiders en producción