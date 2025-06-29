# Plan de Implementación: 3 Técnicas de Evasión Esenciales

## Introducción

Este documento detalla el plan de implementación para las 3 técnicas de evasión identificadas como esenciales para mejorar la efectividad del sistema de scraping de La Máquina de Noticias. La implementación se basa en la documentación oficial de Scrapy y aprovecha las capacidades nativas del framework.

## 1. Headers HTTP Realistas (30 minutos)

### 1.1 Documentación Scrapy Relevante

Según la documentación oficial de Scrapy:
- **Setting**: `DEFAULT_REQUEST_HEADERS`
- **Middleware**: `DefaultHeadersMiddleware` (orden 400)
- **Ubicación**: `scrapy.downloadermiddlewares.defaultheaders`

### 1.2 Análisis de la Situación Actual

Los headers por defecto de Scrapy son mínimos:
```python
{
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en"
}
```

Esto es una señal clara para los sistemas anti-bot de que no es un navegador real.

### 1.3 Plan de Implementación

#### Paso 1: Actualizar settings.py
**Archivo**: `/src/module_scraper/scraper_core/settings.py`
**Acción**: Reemplazar DEFAULT_REQUEST_HEADERS con headers completos de navegador

Headers realistas a implementar:
```
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8
Accept-Language: es-ES,es;q=0.9,en;q=0.8,en-US;q=0.7
Accept-Encoding: gzip, deflate, br
Cache-Control: no-cache
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Pragma: no-cache
```

#### Paso 2: Actualizar templates de Spider Factory
**Archivos**:
- `/src/spider_factory/templates/spiders/base_spider.j2`
- `/src/spider_factory/templates/spiders/scraping_spider.j2`

**Acción**: Agregar opción para headers personalizados en custom_settings del spider

### 1.4 Validación
- Verificar headers enviados con herramienta de debugging
- Probar en sitios que previamente detectaban bot
- Comparar con headers de navegador real

## 2. Referer Middleware Inteligente (2 horas)

### 2.1 Documentación Scrapy Relevante

Según la documentación oficial:
- **Middleware**: `RefererMiddleware` (Spider Middleware, orden 700)
- **Setting**: `REFERER_ENABLED` (default: True)
- **Setting**: `REFERRER_POLICY` (default: 'DefaultReferrerPolicy')
- **Ubicación**: `scrapy.spidermiddlewares.referer`

NOTA IMPORTANTE: RefererMiddleware es un **Spider Middleware**, no un Downloader Middleware.

### 2.2 Análisis de la Situación Actual

El sistema tiene RefererMiddleware habilitado pero usa la política por defecto que puede no ser óptima para evasión. La política actual envía referer incluso entre dominios diferentes, lo cual puede parecer sospechoso.

### 2.3 Plan de Implementación

#### Opción A: Configurar RefererMiddleware Existente
**Archivo**: `/src/module_scraper/scraper_core/settings.py`
**Acción**: Ajustar la política de referer

Configuración recomendada:
```python
REFERER_ENABLED = True
REFERRER_POLICY = 'scrapy.spidermiddlewares.referer.OriginWhenCrossOriginPolicy'
```

#### Opción B: Crear Downloader Middleware Personalizado
**Archivo nuevo**: `/src/module_scraper/scraper_core/middlewares/smart_referer_middleware.py`
**Propósito**: Control más granular del referer por dominio

Características del middleware personalizado:
1. Mantener referer dentro del mismo dominio
2. Usar página principal como referer para primera visita
3. Simular navegación natural (homepage → sección → artículo)
4. Cache de referers por dominio

#### Paso 1: Crear el middleware
**Ubicación**: `/src/module_scraper/scraper_core/middlewares/smart_referer_middleware.py`

Funcionalidad clave:
- Rastrear última URL visitada por dominio
- Establecer referer lógico basado en navegación
- Manejar casos especiales (primera visita, cambio de dominio)

#### Paso 2: Registrar en settings.py
```python
DOWNLOADER_MIDDLEWARES = {
    # ... otros middlewares ...
    'scraper_core.middlewares.smart_referer_middleware.SmartRefererMiddleware': 585,
}
```

### 2.4 Validación
- Verificar headers Referer en logs
- Confirmar navegación lógica
- Probar en sitios que validan referer

## 3. Mejora de User-Agent List (30 minutos)

### 3.1 Documentación Scrapy Relevante

Según la documentación oficial:
- **Middleware**: `UserAgentMiddleware` (orden 500)
- **Setting**: `USER_AGENT` (default: "Scrapy/VERSION")
- **Atributo Spider**: `user_agent` (override por spider)

El sistema actual usa `scrapy-user-agents` que necesita actualización.

### 3.2 Análisis de la Situación Actual

El middleware de rotación ya está implementado pero la lista de user agents puede estar desactualizada.

### 3.3 Plan de Implementación

#### Paso 1: Crear archivo de User Agents actualizado
**Archivo nuevo**: `/src/module_scraper/scraper_core/utils/user_agents.py`

Estructura:
```python
DESKTOP_AGENTS = [
    # Chrome Windows (40%)
    # Chrome Mac (20%)
    # Firefox Windows (15%)
    # Safari Mac (10%)
    # Edge Windows (10%)
    # Otros (5%)
]

MOBILE_AGENTS = [
    # Chrome Android
    # Safari iOS
]
```

Fuentes para UAs actualizados:
- whatismybrowser.com/guides/the-latest-user-agent/
- useragentstring.com/pages/useragentstring.php

#### Paso 2: Actualizar configuración
**Archivo**: `/src/module_scraper/scraper_core/settings.py`

Verificar configuración de scrapy-user-agents o migrar a solución propia:
```python
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scraper_core.middlewares.rotate_useragent.RotateUserAgentMiddleware': 400,
}
```

#### Paso 3: Actualizar Spider Factory
**Archivo**: `/src/spider_factory/src/config.py`

Agregar configuración para tipo de UA por defecto (desktop vs mobile)

### 3.4 Validación
- Verificar rotación de UAs en logs
- Confirmar UAs modernos y realistas
- Distribución estadística correcta

## 4. Integración con Spider Factory

### 4.1 Modificaciones en analyzer.py
**Archivo**: `/src/spider_factory/src/analyzer.py`

Agregar detección de nivel de protección:
- Básico: Solo headers
- Medio: Headers + Referer
- Alto: Todo activado

### 4.2 Modificaciones en generator.py
**Archivo**: `/src/spider_factory/src/generator.py`

Aplicar configuración según nivel detectado:
```python
if protection_level == 'high':
    custom_settings['DEFAULT_REQUEST_HEADERS'] = STEALTH_HEADERS
    custom_settings['REFERER_ENABLED'] = True
    custom_settings['USER_AGENT_ROTATION'] = True
```

### 4.3 Actualización de Templates
Todos los templates deben soportar custom_settings extendidos

## 5. Orden de Implementación y Testing

### Fase 1: Headers HTTP (Día 1 - Mañana)
1. Actualizar DEFAULT_REQUEST_HEADERS
2. Probar en 5 sitios problemáticos
3. Medir mejora en tasa de éxito

### Fase 2: User-Agent List (Día 1 - Tarde)
1. Crear lista actualizada de 30 UAs
2. Integrar con sistema existente
3. Verificar rotación correcta

### Fase 3: Referer Middleware (Día 2)
1. Implementar middleware personalizado
2. Testing exhaustivo de navegación
3. Validar en sitios con verificación de referer

### Fase 4: Integración Spider Factory (Día 2 - Tarde)
1. Actualizar analyzer y generator
2. Testing end-to-end
3. Documentación de uso

## 6. Métricas de Éxito

### KPIs a Medir
1. **Tasa de éxito pre-implementación**: Baseline actual
2. **Tasa de éxito post-headers**: Esperado +40%
3. **Tasa de éxito post-UA**: Esperado +10%
4. **Tasa de éxito post-referer**: Esperado +15%
5. **Tasa de éxito final**: Objetivo 80-85%

### Sitios de Prueba
- 5 sitios con detección básica
- 3 sitios con rate limiting
- 2 sitios con verificación de referer

## 7. Consideraciones Finales

### Mantenimiento
- User Agents: Actualizar cada 3-6 meses
- Headers: Revisar anualmente
- Referer: Sin mantenimiento requerido

### Riesgos
- Mínimos: Todas son técnicas estándar
- Sin dependencias externas
- Compatible con infraestructura actual

### Documentación
- Actualizar README con nuevas capacidades
- Documentar configuración por dominio
- Crear guía de troubleshooting

---

*Documento preparado basándose en la documentación oficial de Scrapy*
*Tiempo total estimado: 3-4 horas de implementación*
*Efectividad esperada: 80-85% de sitios accesibles*