# Tests Pendientes - nginx_reverse_proxy

## Tests de Configuración
* Validar que nginx.conf tiene sintaxis correcta
* Verificar que las variables de entorno se cargan correctamente
* Comprobar que los upstreams están definidos (dashboard_backend, dashboard_frontend)
* Validar configuración de rate limiting (zonas api y general)

## Tests de Routing
* GET / debe redirigir a dashboard_frontend
* GET /api/health debe redirigir a dashboard_backend/health
* GET /api/cualquier-ruta debe quitar /api y redirigir a dashboard_backend
* GET /nginx-health debe retornar 200 OK
* Archivos estáticos (js, css, images) deben servirse con headers de cache correctos

## Tests de Headers de Seguridad
* Verificar X-Frame-Options: DENY en todas las respuestas
* Verificar X-Content-Type-Options: nosniff
* Verificar X-XSS-Protection presente
* Verificar headers CORS en rutas /api/*

## Tests de Rate Limiting
* API: No más de 100 requests/minuto por IP
* General: No más de 300 requests/minuto por IP
* Verificar que burst funciona correctamente

## Tests de Health Checks
* /nginx-health retorna 200 con "nginx OK"
* Health check del contenedor Docker funciona
* Verificar que los upstreams marcan servidores como down después de 3 fallos

## Tests de Compresión
* Verificar que gzip está activo para tipos MIME configurados
* Comprobar que archivos < 1000 bytes no se comprimen
* Validar header Content-Encoding: gzip

## Tests de Integración con Docker
* Container se levanta correctamente con docker-compose
* Container se conecta a la red lamacquina_network
* Logs se escriben en /var/log/nginx/
* Container responde en puerto 80

## Tests de Manejo de Errores
* Error 502 cuando backend no está disponible
* Error 504 en timeout de backend
* Páginas de error personalizadas se muestran correctamente
