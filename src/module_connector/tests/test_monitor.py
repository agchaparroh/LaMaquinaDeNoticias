#!/usr/bin/env python3
"""
Test script for directory monitoring functionality
"""

import asyncio
import os
import tempfile
import shutil
import sys
import gzip
import json
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test data
TEST_ARTICLE = {
    "url": "https://test.com/article/1",
    "medio": "Test Medium",
    "pais_publicacion": "Test Country", 
    "tipo_medio": "Test Type",
    "titular": "Test Title",
    "fecha_publicacion": "2023-12-01T12:00:00Z",
    "contenido_texto": "Test content text"
}


async def test_directory_monitoring():
    """Test the directory monitoring functionality"""
    
    print("🧪 Testing Directory Monitoring Function")
    print("=" * 50)
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Setup test directories
        input_dir = temp_path / "input"
        pending_dir = temp_path / "pending"
        completed_dir = temp_path / "completed"
        error_dir = temp_path / "error"
        
        input_dir.mkdir()
        pending_dir.mkdir()
        completed_dir.mkdir()
        error_dir.mkdir()
        
        print(f"📁 Created test directories in: {temp_dir}")
        
        # Override config for testing
        import config
        original_scraper_dir = config.SCRAPER_OUTPUT_DIR
        original_pending_dir = config.PIPELINE_PENDING_DIR
        original_completed_dir = config.PIPELINE_COMPLETED_DIR
        original_error_dir = config.PIPELINE_ERROR_DIR
        original_polling = config.POLLING_INTERVAL
        
        config.SCRAPER_OUTPUT_DIR = str(input_dir)
        config.PIPELINE_PENDING_DIR = str(pending_dir)
        config.PIPELINE_COMPLETED_DIR = str(completed_dir)
        config.PIPELINE_ERROR_DIR = str(error_dir)
        config.POLLING_INTERVAL = 1  # Fast polling for testing
        
        try:
            # Create a test .json.gz file
            test_file = input_dir / "test_article.json.gz"
            
            with gzip.open(test_file, 'wt', encoding='utf-8') as f:
                json.dump(TEST_ARTICLE, f)
            
            print(f"📄 Created test file: {test_file.name}")
            
            # Import and test the monitor function
            from main import monitor_directory
            
            print("🔍 Starting monitoring (will run for 3 seconds)...")
            
            # Run monitoring for a short time
            monitor_task = asyncio.create_task(monitor_directory())
            
            # Let it run for a few seconds
            await asyncio.sleep(3)
            
            # Cancel the monitoring task
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
            
            # Check results
            print("\n📊 Test Results:")
            
            # Check if file was moved from input to pending
            input_files = list(input_dir.glob("*.json.gz"))
            pending_files = list(pending_dir.glob("*.json.gz"))
            
            print(f"  Files in input directory: {len(input_files)}")
            print(f"  Files in pending directory: {len(pending_files)}")
            
            if len(input_files) == 0 and len(pending_files) == 1:
                print("  ✅ File successfully moved to pending directory")
                print(f"     Pending file: {pending_files[0].name}")
            elif len(input_files) == 1:
                print("  ❌ File was not moved from input directory")
            else:
                print("  ⚠️  Unexpected file state")
            
            # Test directory creation
            dirs_exist = all([
                input_dir.exists(),
                pending_dir.exists(), 
                completed_dir.exists(),
                error_dir.exists()
            ])
            
            print(f"  Directory structure: {'✅ Created' if dirs_exist else '❌ Missing'}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Restore original config
            config.SCRAPER_OUTPUT_DIR = original_scraper_dir
            config.PIPELINE_PENDING_DIR = original_pending_dir
            config.PIPELINE_COMPLETED_DIR = original_completed_dir
            config.PIPELINE_ERROR_DIR = original_error_dir
            config.POLLING_INTERVAL = original_polling
    
    print("\n" + "=" * 50)
    print("🎉 Directory monitoring test completed!")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_directory_monitoring())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
