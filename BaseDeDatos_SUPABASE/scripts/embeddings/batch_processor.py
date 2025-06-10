#!/usr/bin/env python3
"""
Framework de procesamiento batch para generación de embeddings
Tarea 26.2: Implement Batch Processing Framework

Este script implementa un sistema robusto para procesar grandes volúmenes 
de registros de base de datos generando embeddings en lotes.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
import numpy as np
from tqdm import tqdm

from embedding_config import EmbeddingModel
from database_config import DatabaseConnection

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BatchProcessingConfig:
    """
    Configuración para el procesamiento batch
    """
    batch_size: int = 32
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_progress_bar: bool = True
    transaction_size: int = 100  # Número de lotes por transacción
    log_interval: int = 10  # Log cada N lotes
    validate_embeddings: bool = True
    skip_existing: bool = True


@dataclass
class ProcessingStats:
    """
    Estadísticas del procesamiento
    """
    total_records: int = 0
    processed_records: int = 0
    skipped_records: int = 0
    failed_records: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    batch_count: int = 0
    error_count: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.processed_records == 0:
            return 0.0
        return (self.processed_records - self.failed_records) / self.processed_records * 100
    
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def records_per_second(self) -> Optional[float]:
        if self.duration and self.duration > 0:
            return self.processed_records / self.duration
        return None


class EmbeddingBatchProcessor:
    """
    Procesador batch para generación de embeddings vectoriales
    """
    
    def __init__(self, config: BatchProcessingConfig = None):
        """
        Inicializar procesador batch
        
        Args:
            config: Configuración del procesamiento
        """
        self.config = config or BatchProcessingConfig()
        self.embedding_model = None
        self.db_connection = None
        self.stats = ProcessingStats()
        
    def setup(self) -> bool:
        """
        Configurar modelo de embeddings y conexión a BD
        
        Returns:
            True si la configuración fue exitosa
        """
        try:
            logger.info("Configurando procesador batch...")
            
            # Configurar modelo de embeddings
            logger.info("Cargando modelo de embeddings...")
            self.embedding_model = EmbeddingModel()
            
            # Configurar conexión a BD
            logger.info("Configurando conexión a base de datos...")
            self.db_connection = DatabaseConnection()
            
            if not self.db_connection.connect():
                logger.error("No se pudo conectar a la base de datos")
                return False
            
            logger.info("✅ Procesador batch configurado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando procesador: {e}")
            return False
    
    def cleanup(self):
        """
        Limpiar recursos
        """
        if self.db_connection:
            self.db_connection.disconnect()
    
    def get_records_to_process(self, table_name: str, 
                              text_column: str,
                              id_column: str = 'id',
                              additional_columns: List[str] = None) -> List[Dict[str, Any]]:
        """
        Obtener registros que necesitan embeddings
        
        Args:
            table_name: Nombre de la tabla
            text_column: Columna con texto para embedding
            id_column: Columna ID
            additional_columns: Columnas adicionales a incluir
            
        Returns:
            Lista de registros a procesar
        """
        additional_cols = ', '.join(additional_columns) if additional_columns else ''
        if additional_cols:
            additional_cols = ', ' + additional_cols
        
        # Construir query
        where_clause = "embedding IS NULL" if self.config.skip_existing else "1=1"
        
        query = f"""
        SELECT {id_column}, {text_column}{additional_cols}
        FROM {table_name}
        WHERE {where_clause}
        ORDER BY {id_column}
        """
        
        try:
            records = self.db_connection.execute_query(query)
            logger.info(f"Encontrados {len(records)} registros en {table_name} para procesar")
            return records
            
        except Exception as e:
            logger.error(f"Error obteniendo registros de {table_name}: {e}")
            return []
    
    def process_text_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Procesar un lote de textos para generar embeddings
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de embeddings
        """
        try:
            embeddings = self.embedding_model.generate_batch_embeddings(
                texts, 
                batch_size=self.config.batch_size
            )
            return embeddings
            
        except Exception as e:
            logger.error(f"Error procesando lote de textos: {e}")
            # Fallback: procesar individualmente
            embeddings = []
            for text in texts:
                try:
                    emb = self.embedding_model.generate_embedding(text)
                    embeddings.append(emb)
                except:
                    # Vector de ceros como fallback
                    embeddings.append(np.zeros(384))
                    self.stats.failed_records += 1
            
            return embeddings
    
    def update_embeddings_batch(self, table_name: str,
                               records_embeddings: List[Tuple[Any, np.ndarray]],
                               id_column: str = 'id') -> int:
        """
        Actualizar embeddings en la base de datos
        
        Args:
            table_name: Nombre de la tabla
            records_embeddings: Lista de tuplas (id, embedding)
            id_column: Nombre de la columna ID
            
        Returns:
            Número de registros actualizados
        """
        if not records_embeddings:
            return 0
        
        # Preparar datos para update
        update_data = []
        for record_id, embedding in records_embeddings:
            # Convertir numpy array a lista para PostgreSQL
            embedding_list = embedding.tolist()
            update_data.append((embedding_list, record_id))
        
        # Query de update
        query = f"UPDATE {table_name} SET embedding = %s WHERE {id_column} = %s"
        
        try:
            updated_count = self.db_connection.execute_batch_update(query, update_data)
            return updated_count
            
        except Exception as e:
            logger.error(f"Error actualizando embeddings en {table_name}: {e}")
            raise
    
    def validate_embeddings_batch(self, embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """
        Validar un lote de embeddings
        
        Args:
            embeddings: Lista de embeddings a validar
            
        Returns:
            Diccionario con resultados de validación
        """
        validation_results = {
            'total_embeddings': len(embeddings),
            'valid_embeddings': 0,
            'zero_vectors': 0,
            'invalid_embeddings': 0,
            'dimension_errors': 0,
            'value_errors': 0
        }
        
        for embedding in embeddings:
            # Validar dimensiones
            if len(embedding) != 384:
                validation_results['dimension_errors'] += 1
                validation_results['invalid_embeddings'] += 1
                continue
            
            # Validar valores
            if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
                validation_results['value_errors'] += 1
                validation_results['invalid_embeddings'] += 1
                continue
            
            # Detectar vectores de ceros
            if np.allclose(embedding, 0):
                validation_results['zero_vectors'] += 1
            
            validation_results['valid_embeddings'] += 1
        
        return validation_results
    
    def process_table(self, table_name: str,
                     text_column: str,
                     id_column: str = 'id',
                     additional_columns: List[str] = None,
                     text_combiner: Callable[[Dict], str] = None) -> ProcessingStats:
        """
        Procesar una tabla completa
        
        Args:
            table_name: Nombre de la tabla
            text_column: Columna principal de texto
            id_column: Columna ID
            additional_columns: Columnas adicionales para combinar texto
            text_combiner: Función para combinar múltiples columnas de texto
            
        Returns:
            Estadísticas del procesamiento
        """
        logger.info(f"🚀 Iniciando procesamiento de tabla: {table_name}")
        
        # Resetear estadísticas
        self.stats = ProcessingStats()
        self.stats.start_time = datetime.now()
        
        try:
            # Obtener registros a procesar
            records = self.get_records_to_process(
                table_name, text_column, id_column, additional_columns
            )
            
            if not records:
                logger.info(f"No hay registros para procesar en {table_name}")
                return self.stats
            
            self.stats.total_records = len(records)
            
            # Configurar barra de progreso
            if self.config.enable_progress_bar:
                progress_bar = tqdm(
                    total=len(records),
                    desc=f"Procesando {table_name}",
                    unit="registros"
                )
            
            # Procesar en lotes
            batch_embeddings = []
            current_transaction_batches = 0
            
            for i in range(0, len(records), self.config.batch_size):
                batch_records = records[i:i + self.config.batch_size]
                self.stats.batch_count += 1
                
                try:
                    # Extraer textos del lote
                    if text_combiner:
                        texts = [text_combiner(record) for record in batch_records]
                    else:
                        texts = [record[text_column] or "" for record in batch_records]
                    
                    # Generar embeddings
                    embeddings = self.process_text_batch(texts)
                    
                    # Validar embeddings si está habilitado
                    if self.config.validate_embeddings:
                        validation = self.validate_embeddings_batch(embeddings)
                        if validation['invalid_embeddings'] > 0:
                            logger.warning(f"Lote {self.stats.batch_count}: {validation['invalid_embeddings']} embeddings inválidos")
                    
                    # Preparar para actualización
                    records_embeddings = [
                        (record[id_column], embeddings[idx])
                        for idx, record in enumerate(batch_records)
                    ]
                    
                    batch_embeddings.extend(records_embeddings)
                    current_transaction_batches += 1
                    
                    # Actualizar BD cada N lotes (transaction_size)
                    if current_transaction_batches >= self.config.transaction_size or i + self.config.batch_size >= len(records):
                        updated_count = self.update_embeddings_batch(
                            table_name, batch_embeddings, id_column
                        )
                        
                        logger.info(f"Actualizados {updated_count} registros en transacción")
                        
                        self.stats.processed_records += len(batch_embeddings)
                        batch_embeddings = []
                        current_transaction_batches = 0
                    
                    # Actualizar progreso
                    if self.config.enable_progress_bar:
                        progress_bar.update(len(batch_records))
                    
                    # Log periódico
                    if self.stats.batch_count % self.config.log_interval == 0:
                        logger.info(f"Procesados {self.stats.batch_count} lotes, "
                                   f"{self.stats.processed_records} registros")
                
                except Exception as e:
                    logger.error(f"Error procesando lote {self.stats.batch_count}: {e}")
                    self.stats.error_count += 1
                    
                    # Retry logic
                    retry_count = 0
                    while retry_count < self.config.max_retries:
                        try:
                            time.sleep(self.config.retry_delay)
                            logger.info(f"Reintentando lote {self.stats.batch_count} (intento {retry_count + 1})")
                            
                            # Repetir procesamiento
                            if text_combiner:
                                texts = [text_combiner(record) for record in batch_records]
                            else:
                                texts = [record[text_column] or "" for record in batch_records]
                            
                            embeddings = self.process_text_batch(texts)
                            
                            # Actualizar BD
                            records_embeddings = [
                                (record[id_column], embeddings[idx])
                                for idx, record in enumerate(batch_records)
                            ]
                            
                            updated_count = self.update_embeddings_batch(
                                table_name, records_embeddings, id_column
                            )
                            
                            self.stats.processed_records += len(records_embeddings)
                            logger.info(f"✅ Lote {self.stats.batch_count} reintentado exitosamente")
                            break
                            
                        except Exception as retry_error:
                            retry_count += 1
                            logger.error(f"Error en reintento {retry_count}: {retry_error}")
                            
                            if retry_count >= self.config.max_retries:
                                logger.error(f"❌ Lote {self.stats.batch_count} falló después de {self.config.max_retries} reintentos")
                                self.stats.failed_records += len(batch_records)
            
            # Cerrar barra de progreso
            if self.config.enable_progress_bar:
                progress_bar.close()
            
            self.stats.end_time = datetime.now()
            
            # Log final
            logger.info(f"✅ Procesamiento de {table_name} completado:")
            logger.info(f"  📊 Total registros: {self.stats.total_records}")
            logger.info(f"  ✅ Procesados: {self.stats.processed_records}")
            logger.info(f"  ❌ Fallidos: {self.stats.failed_records}")
            logger.info(f"  📈 Tasa de éxito: {self.stats.success_rate:.1f}%")
            logger.info(f"  ⏱️  Duración: {self.stats.duration:.1f}s")
            logger.info(f"  ⚡ Velocidad: {self.stats.records_per_second:.1f} registros/seg")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Error general procesando {table_name}: {e}")
            self.stats.end_time = datetime.now()
            raise


def test_batch_processing():
    """
    Probar el framework de procesamiento batch
    """
    logger.info("=== PROBANDO FRAMEWORK DE PROCESAMIENTO BATCH ===")
    
    # Configuración de prueba
    config = BatchProcessingConfig(
        batch_size=5,  # Lotes pequeños para prueba
        max_retries=2,
        enable_progress_bar=True,
        transaction_size=2
    )
    
    processor = EmbeddingBatchProcessor(config)
    
    try:
        # Configurar procesador
        if not processor.setup():
            logger.error("❌ No se pudo configurar el procesador")
            return False
        
        # Probar obtención de registros (tabla con menos datos)
        logger.info("Probando obtención de registros...")
        records = processor.get_records_to_process(
            'hilos_narrativos',
            'titulo',
            'id',
            ['descripcion']
        )
        
        if records:
            logger.info(f"✅ Obtenidos {len(records)} registros de hilos_narrativos")
            
            # Probar procesamiento de textos
            logger.info("Probando procesamiento de embeddings...")
            sample_texts = [record['titulo'] for record in records[:3]]
            embeddings = processor.process_text_batch(sample_texts)
            
            if len(embeddings) == len(sample_texts):
                logger.info(f"✅ Generados {len(embeddings)} embeddings correctamente")
                
                # Validar embeddings
                validation = processor.validate_embeddings_batch(embeddings)
                logger.info(f"📊 Validación: {validation['valid_embeddings']}/{validation['total_embeddings']} válidos")
                
                if validation['valid_embeddings'] > 0:
                    logger.info("🎉 Framework de procesamiento batch funcionando correctamente")
                    return True
                else:
                    logger.error("❌ No se generaron embeddings válidos")
                    return False
            else:
                logger.error(f"❌ Error en generación: {len(embeddings)} vs {len(sample_texts)}")
                return False
        else:
            logger.warning("⚠️  No hay registros para probar, pero la configuración es correcta")
            return True
    
    except Exception as e:
        logger.error(f"Error en prueba: {e}")
        return False
    
    finally:
        processor.cleanup()


if __name__ == "__main__":
    test_batch_processing()
