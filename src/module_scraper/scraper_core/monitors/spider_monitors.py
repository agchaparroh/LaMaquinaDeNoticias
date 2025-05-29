# C:\Users\DELL\Desktop\Prueba con Windsurf AI\La Máquina de Noticias\src\module_scraper\scraper_core\monitors\spider_monitors.py
from spidermon import Monitor, MonitorSuite, monitors
from spidermon.contrib.actions.slack.notifiers import SendSlackMessageSpiderFinished
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

class SpiderCloseMonitorSuite(MonitorSuite):
    """
    Suite de monitores que se ejecutarán cuando una araña finalice.
    """
    monitors = [
        CustomItemValidationMonitor,
        BasicStatsMonitor,
        # Aquí se pueden agregar más monitores que se ejecuten al cierre de la araña
    ]

    # Acciones a tomar si algún monitor falla
    actions_on_failure = [
        SendSlackMessageSpiderFinished,
    ]
    # actions_on_success = [
    #     SendSlackMessageSpiderFinished, # Opcional: notificar también en caso de éxito
    # ]
    # actions_always = [
    #     # Acciones que se ejecutan siempre, independientemente del resultado de los monitores
    # ]
