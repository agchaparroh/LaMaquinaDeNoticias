"""
Configuración para tests de API
"""

import sys
from pathlib import Path

# Agregar el directorio de mocks al path antes de importar
test_dir = Path(__file__).parent.parent
sys.path.insert(0, str(test_dir))

# Monkey patch para reemplazar el import de module_connector
sys.modules['module_connector'] = type(sys)('module_connector')
sys.modules['module_connector.src'] = type(sys)('module_connector.src')
sys.modules['module_connector.src.models'] = type(sys)('module_connector.src.models')

# Importar el mock de ArticuloInItem
from mocks.models import ArticuloInItem

# Asignar el mock al módulo falso
sys.modules['module_connector.src.models'].ArticuloInItem = ArticuloInItem
