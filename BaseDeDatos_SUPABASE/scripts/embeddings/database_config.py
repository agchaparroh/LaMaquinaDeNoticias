"""
Configuración de conexión a base de datos para generación de embeddings
Tarea 26: Generate Vector Embeddings for All Existing Database Records
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Manejo de conexión a PostgreSQL/Supabase
    """
    
    def __init__(self, connection_params: Optional[Dict[str, str]] = None):
        """
        Inicializar conexión a base de datos
        
        Args:
            connection_params: Parámetros de conexión opcional
        """
        self.connection_params = connection_params or self._get_default_params()
        self.connection = None
        self.cursor = None
    
    def _get_default_params(self) -> Dict[str, str]:
        """
        Obtener parámetros por defecto desde variables de entorno
        """
        # Parámetros para Supabase proyecto: aukbzqbcvbsnjdhflyvr
        default_params = {
            'host': 'db.aukbzqbcvbsnjdhflyvr.supabase.co',
            'port': '5432',
            'database': 'postgres',
            'user': os.getenv('SUPABASE_USER', 'postgres'),
            'password': os.getenv('SUPABASE_PASSWORD', ''),  # Requerido
            'sslmode': 'require'
        }
        
        return default_params
    
    def connect(self):
        """
        Establecer conexión a la base de datos
        """
        try:
            logger.info(f"Conectando a {self.connection_params['host']}...")
            
            self.connection = psycopg2.connect(**self.connection_params)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Verificar conexión
            self.cursor.execute("SELECT version()")
            version = self.cursor.fetchone()
            logger.info(f"Conectado exitosamente: {version['version']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a base de datos: {e}")
            return False
    
    def disconnect(self):
        """
        Cerrar conexión
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Conexión cerrada")
    
    def execute_query(self, query: str, params: tuple = None):
        """
        Ejecutar consulta SELECT
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            raise
    
    def execute_update(self, query: str, params: tuple = None):
        """
        Ejecutar consulta UPDATE/INSERT
        """
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            logger.error(f"Error ejecutando actualización: {e}")
            self.connection.rollback()
            raise
    
    def execute_batch_update(self, query: str, params_list):
        """
        Ejecutar múltiples actualizaciones en batch
        """
        try:
            from psycopg2.extras import execute_batch
            execute_batch(self.cursor, query, params_list)
            self.connection.commit()
            return len(params_list)
        except Exception as e:
            logger.error(f"Error ejecutando batch update: {e}")
            self.connection.rollback()
            raise
    
    def get_table_record_count(self, table_name: str, where_clause: str = "") -> int:
        """
        Obtener conteo de registros en una tabla
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        result = self.execute_query(query)
        return result[0]['count']
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas actuales de embeddings
        """
        tables_with_embeddings = [
            'fragmentos_extensos',
            'hechos', 
            'entidades',
            'hilos_narrativos',
            'citas_textuales',
            'datos_cuantitativos'
        ]
        
        stats = {}
        
        for table in tables_with_embeddings:
            try:
                # Conteo total
                total = self.get_table_record_count(table)
                
                # Conteo con embeddings
                with_embeddings = self.get_table_record_count(table, "embedding IS NOT NULL")
                
                # Conteo sin embeddings
                without_embeddings = total - with_embeddings
                
                stats[table] = {
                    'total_records': total,
                    'with_embeddings': with_embeddings,
                    'without_embeddings': without_embeddings,
                    'completion_percentage': (with_embeddings / total * 100) if total > 0 else 0
                }
                
            except Exception as e:
                logger.warning(f"Error obteniendo stats para {table}: {e}")
                stats[table] = {'error': str(e)}
        
        return stats


def test_connection():
    """
    Probar conexión a base de datos
    """
    logger.info("=== PROBANDO CONEXIÓN A BASE DE DATOS ===")
    
    # Verificar variables de entorno
    password = os.getenv('SUPABASE_PASSWORD')
    if not password:
        logger.error("❌ Variable SUPABASE_PASSWORD no configurada")
        logger.info("Configurar con: export SUPABASE_PASSWORD='tu_password'")
        return False
    
    # Probar conexión
    db = DatabaseConnection()
    
    if db.connect():
        logger.info("✅ Conexión exitosa")
        
        # Obtener estadísticas actuales
        stats = db.get_embedding_stats()
        
        logger.info("📊 Estadísticas actuales de embeddings:")
        for table, table_stats in stats.items():
            if 'error' in table_stats:
                logger.warning(f"  {table}: ERROR - {table_stats['error']}")
            else:
                logger.info(f"  {table}: {table_stats['with_embeddings']}/{table_stats['total_records']} "
                           f"({table_stats['completion_percentage']:.1f}%) completado")
        
        db.disconnect()
        return True
    else:
        logger.error("❌ No se pudo conectar a la base de datos")
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_connection()
