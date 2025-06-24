# C:\Users\DELL\Desktop\Prueba con Windsurf AI\La Máquina de Noticias\src\module_scraper\scraper_core\monitors\spider_monitors.py
from spidermon import Monitor, MonitorSuite, monitors
from spidermon.contrib.monitors.mixins import StatsMonitorMixin

# Aquí definiremos nuestros monitores personalizados y la suite de monitores.
from spidermon.contrib.scrapy.monitors import ItemValidationMonitor
import json, os

# Suponiendo que el esquema está en scraper_core/schemas/articulo_schema.json
# Ajusta la ruta si es necesario.
SCHEMA_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # Directorio actual (monitors)
    '..',  # Subir un nivel a scraper_core
    'schemas',
    'articulo_schema.json'
)

# Cargar el esquema (esto se haría una vez cuando se carga el módulo)
# En un caso real, manejarías el FileNotFoundError si el esquema no existe.
try:
    with open(SCHEMA_FILE_PATH, 'r') as f:
        ARTICULO_SCHEMA = json.load(f)
except FileNotFoundError:
    # Si el archivo no existe, usa un esquema vacío o un placeholder.
    # Esto es para evitar que el código falle si el archivo no está creado aún.
    # Deberías crear el archivo de esquema para una validación real.
    print(f"ADVERTENCIA: Archivo de esquema no encontrado en {SCHEMA_FILE_PATH}. Usando esquema de validación vacío.")
    ARTICULO_SCHEMA = {}


@monitors.name('Item Validation Monitor')
class CustomItemValidationMonitor(ItemValidationMonitor):
    """
    Monitor para validar cada ítem scrapeado contra un esquema JSON.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aquí podrías cargar dinámicamente diferentes esquemas por tipo de ítem si fuera necesario.
        # Por ahora, usamos un único esquema para todos los ítems.
        self.item_schemas = {
            # Asume que tu Item se llama 'ArticuloInItem' o similar.
            # Ajusta el nombre de la clase del Item si es diferente.
            # Si no estás seguro, puedes inspeccionar self.data.items
            # o usar un nombre genérico si todos los ítems usan el mismo esquema.
            'ArticuloInItem': ARTICULO_SCHEMA 
        }
        # Si no sabes el nombre exacto de la clase del Item, puedes omitir
        # item_schemas aquí y Spidermon intentará validar todos los ítems
        # contra un esquema por defecto si se define SPIDERMON_VALIDATION_SCHEMAS
        # en settings.py, o puedes sobreescribir el método `get_item_schema`.


@monitors.name('Basic Stats Monitor')
class BasicStatsMonitor(Monitor, StatsMonitorMixin):

    @monitors.name('Minimum items scraped')
    def test_minimum_items_scraped(self):
        item_scraped_count = self.stats.get('item_scraped_count', 0)
        # Este umbral podría ser configurable por araña o globalmente en settings.py
        minimum_threshold = self.crawler.settings.getint('SPIDERMON_MIN_ITEMS_SCRAPED', 1) # Default a 1

        self.assertFalse(
            item_scraped_count < minimum_threshold,
            msg=f'Se rasparon {item_scraped_count} ítems. Se esperaban al menos {minimum_threshold}.'
        )

    @monitors.name('Maximum critical errors')
    def test_maximum_critical_errors(self):
        critical_errors_count = self.stats.get('log_count/CRITICAL', 0)
        # Este umbral podría ser configurable
        max_critical_errors = self.crawler.settings.getint('SPIDERMON_MAX_CRITICAL_ERRORS', 0) # Default a 0

        self.assertFalse(
            critical_errors_count > max_critical_errors,
            msg=f'Se encontraron {critical_errors_count} errores críticos. Se permiten como máximo {max_critical_errors}.'
        )

    @monitors.name('Maximum error messages')
    def test_maximum_error_messages(self):
        error_messages_count = self.stats.get('log_count/ERROR', 0)
        # Permitir algunos errores no críticos, configurable
        max_error_messages = self.crawler.settings.getint('SPIDERMON_MAX_ERROR_MESSAGES', 5) # Default a 5

        self.assertFalse(
            error_messages_count > max_error_messages,
            msg=f'Se encontraron {error_messages_count} mensajes de error. Se permiten como máximo {max_error_messages}.'
        )


@monitors.name('Structure Change Monitor')
class StructureChangeMonitor(Monitor, StatsMonitorMixin):
    """
    Monitor que detecta cuando los selectores XPath/CSS dejan de funcionar,
    lo cual puede indicar cambios en la estructura HTML del sitio web.
    """
    
    @monitors.name('Selectors effectiveness')
    def test_selectors_effectiveness(self):
        """Verificar efectividad de los selectores"""
        total_items = self.stats.get('item_scraped_count', 0)
        
        # Si no hay items, no podemos verificar
        if total_items == 0:
            return
        
        # Campos críticos que deben estar presentes
        critical_fields = ['titulo', 'contenido_texto', 'url', 'medio']
        
        for field in critical_fields:
            empty_count = self.stats.get(f'spidermon/validation/fields/{field}_empty', 0)
            
            if total_items > 0:
                empty_ratio = empty_count / total_items
                threshold = 0.1  # 10% máximo de campos vacíos
                
                self.assertFalse(
                    empty_ratio > threshold,
                    msg=f'{empty_ratio*100:.1f}% de artículos sin {field}. '
                        f'Posible cambio en estructura HTML del sitio.'
                )


@monitors.name('Critical Fields Monitor')
class CriticalFieldsMonitor(Monitor, StatsMonitorMixin):
    """
    Monitor que verifica que los campos críticos estén presentes y no vacíos.
    """
    
    @monitors.name('Critical fields not empty')
    def test_critical_fields_populated(self):
        """Verificar que los campos críticos estén poblados"""
        total_items = self.stats.get('item_scraped_count', 0)
        
        if total_items == 0:
            return
        
        # Campos críticos con umbrales específicos
        critical_fields_thresholds = {
            'titulo': 0.05,  # 5% máximo vacío
            'contenido_texto': 0.05,
            'url': 0.0,  # 0% - siempre debe estar presente
            'medio': 0.0,
            'fecha_recopilacion': 0.0
        }
        
        for field, max_empty_ratio in critical_fields_thresholds.items():
            # Obtener estadísticas de validación
            empty_count = self.stats.get(f'spidermon/validation/fields/{field}_empty', 0)
            invalid_count = self.stats.get(f'spidermon/validation/fields/{field}_invalid', 0)
            
            # Calcular ratio de problemas
            problem_count = empty_count + invalid_count
            problem_ratio = problem_count / total_items if total_items > 0 else 0
            
            self.assertFalse(
                problem_ratio > max_empty_ratio,
                msg=f'Campo crítico {field}: {problem_ratio*100:.1f}% con problemas '
                    f'(vacío o inválido). Máximo permitido: {max_empty_ratio*100:.1f}%'
            )


@monitors.name('Response Time Monitor')
class ResponseTimeMonitor(Monitor, StatsMonitorMixin):
    """
    Monitor que detecta sitios lentos o problemas de red basándose
    en los tiempos de respuesta.
    """
    
    @monitors.name('Average response time')
    def test_response_time_acceptable(self):
        """Verificar que el tiempo de respuesta promedio sea aceptable"""
        # Obtener latencia promedio en milisegundos
        avg_latency = self.stats.get('downloader/response_latency', 0)
        max_acceptable = self.crawler.settings.getfloat('SPIDERMON_MAX_RESPONSE_TIME', 5000)
        
        self.assertFalse(
            avg_latency > max_acceptable,
            msg=f'Tiempo de respuesta promedio: {avg_latency:.0f}ms '
                f'(máximo aceptable: {max_acceptable:.0f}ms). '
                f'El sitio puede estar lento o hay problemas de red.'
        )
    
    @monitors.name('Response time variance')
    def test_response_time_variance(self):
        """Verificar la variabilidad en tiempos de respuesta"""
        # Si hay mucha variabilidad, puede indicar problemas intermitentes
        response_count = self.stats.get('downloader/response_count', 0)
        
        if response_count < 10:  # Necesitamos suficientes muestras
            return
        
        # Obtener tiempos por código de estado
        slow_responses = 0
        for status in [200, 301, 302, 304]:
            status_count = self.stats.get(f'downloader/response_status_count/{status}', 0)
            if status_count > 0:
                # Aproximación: si el tiempo promedio es alto, probablemente hay respuestas lentas
                if self.stats.get('downloader/response_latency', 0) > 3000:
                    slow_responses += status_count * 0.2  # Estimación conservadora
        
        slow_ratio = slow_responses / response_count if response_count > 0 else 0
        
        self.assertFalse(
            slow_ratio > 0.3,
            msg=f'Aproximadamente {slow_ratio*100:.1f}% de respuestas son lentas. '
                f'Considere ajustar DOWNLOAD_DELAY o verificar la conexión.'
        )


@monitors.name('HTTP Error Rate Monitor')
class HTTPErrorRateMonitor(Monitor, StatsMonitorMixin):
    """
    Monitor que detecta tasas altas de errores HTTP que pueden indicar
    bloqueos, rate limiting o problemas del servidor.
    """
    
    @monitors.name('HTTP error rate')
    def test_http_error_rate_acceptable(self):
        """Verificar que la tasa de errores HTTP sea aceptable"""
        total_responses = self.stats.get('downloader/response_count', 0)
        
        if total_responses == 0:
            return
        
        # Códigos de error a monitorear
        error_codes = {
            403: 'Forbidden - Posible bloqueo',
            429: 'Too Many Requests - Rate limiting activo',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable',
            504: 'Gateway Timeout'
        }
        
        total_errors = 0
        error_details = []
        
        for code, description in error_codes.items():
            count = self.stats.get(f'downloader/response_status_count/{code}', 0)
            if count > 0:
                total_errors += count
                error_details.append(f'{code} {description}: {count}')
        
        error_rate = total_errors / total_responses
        max_error_rate = 0.1  # 10% máximo
        
        error_msg = f'Tasa de error HTTP: {error_rate*100:.1f}% '
        if error_details:
            error_msg += f'(Detalles: {", ".join(error_details)})'
        
        self.assertFalse(
            error_rate > max_error_rate,
            msg=error_msg
        )
    
    @monitors.name('Specific error patterns')
    def test_specific_error_patterns(self):
        """Detectar patrones específicos de errores"""
        # Verificar si hay muchos 403 o 429 que indiquen bloqueo
        forbidden_count = self.stats.get('downloader/response_status_count/403', 0)
        rate_limit_count = self.stats.get('downloader/response_status_count/429', 0)
        total_responses = self.stats.get('downloader/response_count', 0)
        
        if total_responses > 0:
            # Si más del 5% son 403 o 429, es probable un bloqueo
            block_ratio = (forbidden_count + rate_limit_count) / total_responses
            
            self.assertFalse(
                block_ratio > 0.05,
                msg=f'Posible bloqueo detectado: {block_ratio*100:.1f}% de respuestas '
                    f'son 403 Forbidden ({forbidden_count}) o 429 Rate Limit ({rate_limit_count}). '
                    f'Considere usar proxies o ajustar DOWNLOAD_DELAY.'
            )


class SpiderCloseMonitorSuite(MonitorSuite):
    """
    Suite de monitores que se ejecutarán cuando una araña finalice.
    """
    monitors = [
        CustomItemValidationMonitor,
        BasicStatsMonitor,
        # Monitores específicos para La Máquina de Noticias
        StructureChangeMonitor,
        CriticalFieldsMonitor,
        ResponseTimeMonitor,
        HTTPErrorRateMonitor,
    ]

    # Acciones a tomar si algún monitor falla
    # Importar las acciones personalizadas
    @property
    def actions_on_failure(self):
        from scraper_core.monitors.actions import SendAllAlerts
        return [SendAllAlerts]
    
    # Opcional: acciones en caso de éxito
    # @property
    # def actions_on_success(self):
    #     from scraper_core.monitors.actions import LogStructuredAlert
    #     return [LogStructuredAlert]
    
    # Opcional: acciones que siempre se ejecutan
    # @property
    # def actions_always(self):
    #     from scraper_core.monitors.actions import LogStructuredAlert
    #     return [LogStructuredAlert]
