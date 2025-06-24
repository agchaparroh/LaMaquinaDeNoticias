# Guía de Usuario - Panel de Control de Noticias

Esta guía está diseñada para usuarios no técnicos que necesitan monitorear y gestionar la extracción de noticias.

## 📋 Índice
1. [Acceder al Panel](#acceder-al-panel)
2. [Pantalla Principal](#pantalla-principal)
3. [Ver Estado de los Spiders](#ver-estado-de-los-spiders)
4. [Programar Ejecuciones](#programar-ejecuciones)
5. [Ver Estadísticas](#ver-estadísticas)
6. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## 🔐 Acceder al Panel

### Pasos para entrar:
1. **Abrir navegador web** (Chrome, Firefox, Edge, etc.)
2. **Escribir la dirección**: `http://localhost:5000`
3. **Introducir credenciales**:
   - **Usuario**: `admin`
   - **Contraseña**: *(la que configuró el administrador)*
4. **Hacer clic en "Login"**

### ⚠️ Problemas comunes al acceder:
- **"No se puede acceder a este sitio"**: Contactar al administrador, el servicio puede estar apagado
- **"Contraseña incorrecta"**: Verificar mayúsculas/minúsculas, pedir nueva contraseña si es necesario

---

## 🏠 Pantalla Principal

Al entrar verás el **Dashboard** con información general:

### Secciones principales:

#### 1. **Barra Superior** 
- **Servers**: Estado de los servidores de spiders
- **Jobs**: Trabajos en ejecución
- **Timer**: Tareas programadas
- **Stats**: Estadísticas generales

#### 2. **Panel de Estado**
Muestra un resumen rápido:
- 🟢 **Verde**: Todo funcionando correctamente
- 🟡 **Amarillo**: Advertencias (revisar pero no crítico)
- 🔴 **Rojo**: Errores que requieren atención

#### 3. **Spiders Activos**
Lista de spiders que están trabajando ahora mismo:
- **Nombre del spider** (ej: "elpais_spider")
- **Estado**: Running (ejecutándose), Pending (esperando), Finished (terminado)
- **Items**: Cantidad de noticias extraídas
- **Duración**: Tiempo que lleva ejecutándose

---

## 👁️ Ver Estado de los Spiders

### Para ver qué está pasando con cada spider:

1. **Hacer clic en "Jobs"** en el menú superior
2. **Aparecerá una tabla** con todos los trabajos

### Interpretar la información:

#### Columnas importantes:
- **Spider**: Nombre del sitio web (ej: "elmundo", "lavanguardia")
- **Status**: 
  - `running` = 🏃 Trabajando ahora
  - `finished` = ✅ Completado
  - `error` = ❌ Falló
- **Items**: Número de noticias extraídas
- **Errors**: Cantidad de errores (ideal: 0)

#### Códigos de colores:
- **Fila verde**: Spider completado exitosamente
- **Fila amarilla**: Completado con advertencias
- **Fila roja**: Falló o tuvo muchos errores

### Ver detalles de un spider:
1. **Hacer clic en el nombre del spider**
2. Se abrirá una página con:
   - Registro detallado de la ejecución
   - Mensajes de error (si los hay)
   - Estadísticas específicas

---

## ⏰ Programar Ejecuciones

### Para automatizar la extracción de noticias:

1. **Ir a "Timer Tasks"** en el menú
2. **Hacer clic en "Add Task"** (Agregar tarea)
3. **Completar el formulario**:

#### Campos del formulario:
- **Project**: Seleccionar `scraper_core` (proyecto principal)
- **Spider**: Elegir el sitio web (ej: "elpais_spider")
- **Trigger**: Tipo de programación
  - `Interval`: Cada X minutos/horas
  - `Cron`: Horario específico (ej: todos los días a las 8 AM)
- **Settings**: Dejar en blanco (usa configuración por defecto)

#### Ejemplos de programación:
- **Cada hora**: Interval → 60 minutos
- **Cada mañana a las 6 AM**: Cron → `0 6 * * *`
- **Cada 4 horas**: Interval → 240 minutos

4. **Hacer clic en "Submit"** para guardar

### Gestionar tareas programadas:
- **Ver todas**: En la página "Timer Tasks"
- **Pausar**: Clic en "Pause" junto a la tarea
- **Eliminar**: Clic en "Delete"
- **Modificar**: Clic en "Edit"

---

## 📊 Ver Estadísticas

### Panel de estadísticas:

1. **Ir a "Stats"** en el menú
2. **Seleccionar periodo**: Hoy, Última semana, Último mes

### Métricas importantes:

#### Para supervisar la salud del sistema:
- **Total de noticias**: Cantidad extraída en el periodo
- **Tasa de éxito**: % de ejecuciones exitosas (ideal: >95%)
- **Tiempo promedio**: Duración típica de cada spider
- **Errores frecuentes**: Patrones de problemas

#### Gráficos disponibles:
- **Noticias por día**: Ver tendencias
- **Rendimiento por spider**: Identificar los más/menos productivos
- **Horarios de mayor actividad**: Cuándo se extraen más noticias

### Exportar datos:
- Hacer clic en "Export" para descargar en formato CSV
- Útil para reportes o análisis en Excel

---

## ❓ Preguntas Frecuentes

### "¿Qué significa que un spider está en rojo?"
El spider encontró problemas al extraer noticias. Posibles causas:
- El sitio web cambió su diseño
- Problemas de conexión a internet
- El sitio web está bloqueando las extracciones

**Qué hacer**: Informar al equipo técnico con el nombre del spider y la hora del error.

### "¿Puedo detener un spider que está ejecutándose?"
Sí:
1. Ir a "Jobs"
2. Buscar el spider en estado "running"
3. Hacer clic en "Cancel" o "Stop"

### "¿Cómo sé si se están extrayendo noticias nuevas?"
Ver la columna "Items" en la tabla de Jobs:
- Si aumenta = se están extrayendo noticias
- Si está en 0 = puede haber un problema

### "¿Qué hago si no aparecen noticias de un sitio específico?"
1. Verificar en "Jobs" si el spider se ejecutó recientemente
2. Si no se ejecutó: verificar en "Timer Tasks" si está programado
3. Si se ejecutó pero Items = 0: contactar al equipo técnico

### "¿Puedo agregar un nuevo sitio de noticias?"
No directamente. Necesitas solicitar al equipo técnico que cree un nuevo spider para ese sitio.

### "¿Los datos se actualizan en tiempo real?"
La página se actualiza automáticamente cada 10 segundos cuando hay spiders ejecutándose.

---

## 🆘 Necesitas ayuda adicional?

- **Problemas técnicos**: Contactar al administrador del sistema
- **Dudas sobre los datos**: Consultar con el equipo de análisis
- **Sugerencias**: Enviar feedback al equipo de desarrollo

---

📖 **Siguiente**: [Guía de Administración](ADMIN_GUIDE.md) - Para usuarios con permisos de gestión