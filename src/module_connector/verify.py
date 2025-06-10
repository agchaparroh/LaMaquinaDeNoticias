#!/usr/bin/env python3
"""
Quick Verification Test - Validates code structure and imports
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all modules can be imported correctly"""
    print("🔍 Testing imports...")
    
    # Add src to path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    try:
        # Test config import
        import config
        print("  ✅ config.py imports successfully")
        
        # Verify config has required variables
        required_vars = [
            'SCRAPER_OUTPUT_DIR', 'PIPELINE_PENDING_DIR', 
            'PIPELINE_API_URL', 'POLLING_INTERVAL'
        ]
        
        for var in required_vars:
            if hasattr(config, var):
                print(f"     ✅ {var}: {getattr(config, var)}")
            else:
                print(f"     ❌ Missing: {var}")
                return False
        
        # Test models import
        from models import ArticuloInItem, prepare_articulo
        print("  ✅ models.py imports successfully")
        
        # Test model instantiation
        test_data = {
            "medio": "Test",
            "pais_publicacion": "Test",
            "tipo_medio": "Test",
            "titular": "Test Title", 
            "fecha_publicacion": "2023-12-01T12:00:00Z",
            "contenido_texto": "Test content"
        }
        
        article = prepare_articulo(test_data)
        print(f"     ✅ Model validation works: {article.titular}")
        
        # Test main import (without running)
        import main
        print("  ✅ main.py imports successfully")
        
        # Verify main functions exist
        required_functions = [
            'monitor_directory', 'process_file', 'send_to_pipeline',
            'move_file', 'process_pending_files', 'main'
        ]
        
        for func in required_functions:
            if hasattr(main, func):
                print(f"     ✅ Function exists: {func}")
            else:
                print(f"     ❌ Missing function: {func}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\n📁 Testing file structure...")
    
    base_path = Path(__file__).parent
    
    required_files = [
        "src/main.py",
        "src/models.py", 
        "src/config.py",
        "requirements.txt",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml",
        "README.md"
    ]
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ Missing: {file_path}")
            return False
    
    return True

def test_dependencies():
    """Test that key dependencies are available"""
    print("\n📦 Testing dependencies...")
    
    required_packages = [
        'asyncio', 'json', 'gzip', 'os', 'shutil',
        'typing', 'datetime', 'pathlib'
    ]
    
    # Test standard library imports
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ Missing: {package}")
            return False
    
    # Test external dependencies (may not be installed yet)
    external_packages = [
        'aiohttp', 'tenacity', 'loguru', 'pydantic', 'dotenv'
    ]
    
    print("\n📦 Checking external dependencies (may need installation):")
    missing_packages = []
    
    for package in external_packages:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ⚠️  Not installed: {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 To install missing packages:")
        print(f"   pip install -r requirements.txt")
    
    return True  # Don't fail for missing external packages

def main():
    """Run all verification tests"""
    print("🧪 Module Connector - Quick Verification")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dependencies", test_dependencies),
        ("Imports & Code", test_imports),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All verification tests passed!")
        print("✅ Module Connector structure is valid")
        return True
    else:
        print("⚠️  Some verification tests failed")
        print("🔧 Fix issues before running full tests")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
