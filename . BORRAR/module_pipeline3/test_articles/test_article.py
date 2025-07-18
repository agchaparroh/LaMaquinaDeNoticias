#!/usr/bin/env python3
"""
test_article.py - Prueba artículos guardados contra el pipeline
"""
import json
import requests
import sys
import os
import argparse
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def reset_article_states(urls=None):
    """
    Resetea el estado de procesamiento de los artículos a 'pendiente'
    
    Args:
        urls: Lista de URLs específicas para resetear. Si es None, resetea todos los artículos de prueba.
    """
    # Configurar cliente Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("⚠️  No se encontraron credenciales de Supabase. Saltando reset de estados.")
        return
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        if urls:
            # Resetear artículos específicos en batch usando IN
            # Dividir en lotes de 100 URLs para evitar límites de la query
            batch_size = 100
            total_reset = 0
            
            for i in range(0, len(urls), batch_size):
                batch_urls = urls[i:i + batch_size]
                result = supabase.table('articulos').update({
                    'estado_procesamiento': 'pendiente',
                    'fecha_procesamiento': None,
                    'error_detalle': None
                }).in_('url', batch_urls).execute()
                
                count = len(result.data) if result.data else 0
                total_reset += count
            
            print(f"✓ Estados reseteados: {total_reset} de {len(urls)} artículos")
        else:
            # Resetear todos los artículos de Infobae (asumiendo que son los de prueba)
            result = supabase.table('articulos').update({
                'estado_procesamiento': 'pendiente',
                'fecha_procesamiento': None,
                'error_detalle': None
            }).eq('medio', 'Infobae').execute()
            
            count = len(result.data) if result.data else 0
            print(f"✓ Estados reseteados: {count} artículos de Infobae")
            
    except Exception as e:
        print(f"⚠️  Error al resetear estados: {e}")
        print("   Continuando con las pruebas de todas formas...")

def test_article_with_stats(json_file):
    """
    Envía un artículo al pipeline y devuelve estadísticas.
    
    Returns:
        dict: Diccionario con estadísticas del procesamiento
    """
    stats = {
        'exitoso': False,
        'hechos': 0,
        'entidades': 0,
        'citas': 0
    }
    
    try:
        # Leer archivo
        with open(json_file, 'r', encoding='utf-8') as f:
            article = json.load(f)
        
        # URL del pipeline
        url = "http://localhost:8003/procesar_articulo"
        
        print(f"Probando: {Path(json_file).name}")
        print(f"Medio: {article.get('medio', 'Unknown')}")
        print(f"Título: {article.get('titular', 'Sin título')[:80]}...")
        
        # Enviar al pipeline
        response = requests.post(url, json=article, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Procesado exitosamente")
            print(f"  Request ID: {result.get('request_id')}")
            
            # Buscar elementos extraídos en diferentes posibles ubicaciones
            elementos = None
            if 'elementos_extraidos' in result:
                elementos = result['elementos_extraidos']
            elif 'data' in result and isinstance(result['data'], dict):
                # A veces los datos vienen dentro de 'data'
                if 'elementos_extraidos' in result['data']:
                    elementos = result['data']['elementos_extraidos']
                elif 'metricas' in result['data']:
                    # O dentro de métricas
                    metricas = result['data']['metricas']
                    if 'conteos_elementos' in metricas:
                        conteos = metricas['conteos_elementos']
                        elementos = {
                            'hechos': conteos.get('hechos_extraidos', 0),
                            'entidades': conteos.get('entidades_extraidas', 0),
                            'citas': conteos.get('citas_extraidas', 0)
                        }
            
            if elementos:
                stats['hechos'] = elementos.get('hechos', elementos.get('total_hechos', 0))
                stats['entidades'] = elementos.get('entidades', elementos.get('total_entidades', 0))
                stats['citas'] = elementos.get('citas', elementos.get('total_citas', 0))
                
                print(f"  Hechos: {stats['hechos']}")
                print(f"  Entidades: {stats['entidades']}")
                print(f"  Citas: {stats['citas']}")
            
            stats['exitoso'] = True
        else:
            print(f"✗ Error: {response.text[:200]}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Error de conexión: {e}")
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
    
    return stats

def test_article(json_file):
    """Versión simple de test_article para uso individual"""
    test_article_with_stats(json_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prueba artículos guardados contra el pipeline de procesamiento",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python test_article.py archivo.json              # Probar un archivo específico
  python test_article.py all                       # Probar todos los archivos
  python test_article.py all --limit 10            # Probar solo 10 archivos
  python test_article.py all -n 5                  # Probar solo 5 archivos

Nota: El reset de estados se hace automáticamente antes de cada prueba.
        """
    )
    
    parser.add_argument(
        'target',
        help='Archivo JSON específico o "all" para probar todos'
    )
    
    parser.add_argument(
        '--limit', '-n',
        type=int,
        metavar='N',
        help='Número máximo de artículos a procesar (solo con "all")'
    )
    
    args = parser.parse_args()
    
    if args.target == "all":
        # Probar todos los archivos JSON en la carpeta
        json_dir = Path("json")  # Ruta relativa desde test_articles
        if not json_dir.exists():
            json_dir = Path("src/module_pipeline/test_articles/json")  # Ruta absoluta
        
        json_files = list(json_dir.glob("*.json"))
        if not json_files:
            print("No se encontraron archivos JSON en la carpeta json/")
            sys.exit(1)
        
        # Aplicar límite si se especificó
        if args.limit and args.limit > 0:
            total_disponibles = len(list(json_dir.glob('*.json')))
            json_files = json_files[:args.limit]
            print(f"\n📋 Limitando a {args.limit} artículos de {total_disponibles} disponibles")
        
        # SIEMPRE resetear estados automáticamente
        print("\n=== Reseteando estados de artículos ===")
        urls = []
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    article = json.load(f)
                    if 'url' in article:
                        urls.append(article['url'])
            except Exception as e:
                print(f"⚠️  Error leyendo {json_file}: {e}")
        
        if urls:
            reset_article_states(urls)
        else:
            # Si no se pueden obtener las URLs, resetear todos los de Infobae
            print("⚠️  No se pudieron obtener URLs, reseteando todos los artículos de Infobae")
            reset_article_states()
        print()
        
        # Procesar artículos con contador de progreso
        print(f"🚀 Procesando {len(json_files)} artículos...")
        
        # Contadores para resumen
        exitosos = 0
        fallidos = 0
        total_hechos = 0
        total_entidades = 0
        total_citas = 0
        
        for idx, json_file in enumerate(json_files, 1):
            print(f"\n[{idx}/{len(json_files)}] ", end="")
            resultado = test_article_with_stats(json_file)
            
            if resultado['exitoso']:
                exitosos += 1
                total_hechos += resultado.get('hechos', 0)
                total_entidades += resultado.get('entidades', 0)
                total_citas += resultado.get('citas', 0)
            else:
                fallidos += 1
        
        # Mostrar resumen
        print("\n\n" + "="*50)
        print("📊 RESUMEN DE PROCESAMIENTO")
        print("="*50)
        print(f"✅ Exitosos: {exitosos}")
        print(f"❌ Fallidos: {fallidos}")
        print(f"📝 Total de elementos extraídos:")
        print(f"   - Hechos: {total_hechos}")
        print(f"   - Entidades: {total_entidades}")
        print(f"   - Citas: {total_citas}")
        if exitosos > 0:
            print(f"📈 Promedios por artículo:")
            print(f"   - Hechos: {total_hechos/exitosos:.1f}")
            print(f"   - Entidades: {total_entidades/exitosos:.1f}")
            print(f"   - Citas: {total_citas/exitosos:.1f}")
            
    else:
        # Probar archivo específico
        json_file_path = Path(args.target)
        if not json_file_path.exists():
            print(f"❌ Error: No se encontró el archivo {args.target}")
            sys.exit(1)
            
        # SIEMPRE resetear estado del artículo automáticamente
        print("\n=== Reseteando estado del artículo ===")
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                article = json.load(f)
                if 'url' in article:
                    reset_article_states([article['url']])
                else:
                    print("⚠️  El artículo no tiene URL, no se puede resetear el estado")
        except Exception as e:
            print(f"⚠️  Error al leer el artículo: {e}")
        print()
        
        test_article(json_file_path)