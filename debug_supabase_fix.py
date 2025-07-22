#!/usr/bin/env python3
"""Parche temporal para debug del error de Supabase"""

import json

# Función para agregar al archivo supabase_service.py
debug_code = '''
# INICIO PARCHE DEBUG
def actualizar_articulo_procesado_debug(self, payload):
    """Versión debug de actualizar_articulo_procesado"""
    try:
        self.logger.info("DEBUG: Entrando a actualizar_articulo_procesado")
        self.logger.info(f"DEBUG: Tipo de payload recibido: {type(payload)}")
        
        # Validar estructura
        if payload is None:
            self.logger.error("DEBUG: payload es None!")
            return None
            
        payload_dict = self._validar_estructura_payload(payload, 'articulo')
        
        self.logger.info(f"DEBUG: payload_dict después de validar: {type(payload_dict)}")
        self.logger.info(f"DEBUG: articulo_id: {payload_dict.get('articulo_id')}")
        
        # Construir parámetros RPC
        rpc_params = {'datos_json': payload_dict}
        self.logger.info(f"DEBUG: rpc_params: {json.dumps(rpc_params, default=str)[:300]}")
        
        # Verificar que realmente no es None
        if rpc_params.get('datos_json') is None:
            self.logger.error("DEBUG: datos_json es None en rpc_params!")
            return None
            
        # Llamar RPC original
        return self.actualizar_articulo_procesado(payload)
        
    except Exception as e:
        self.logger.error(f"DEBUG: Error en actualizar_articulo_procesado_debug: {e}")
        import traceback
        self.logger.error(f"DEBUG: Traceback: {traceback.format_exc()}")
        return None
# FIN PARCHE DEBUG
'''

print("Código de debug generado. Para aplicar:")
print("1. docker exec -it d164a3364a1c bash")
print("2. vi /app/src/services/supabase_service.py")
print("3. Agregar el código antes del método actualizar_articulo_procesado")
print("4. En controller.py, cambiar la llamada a actualizar_articulo_procesado_debug")