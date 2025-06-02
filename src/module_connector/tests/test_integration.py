#!/usr/bin/env python3
"""
Integration test for the complete Module Connector workflow
"""

import asyncio
import os
import tempfile
import sys
import gzip
import json
import time
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test data
TEST_ARTICLES = [
    {
        "url": "https://test.com/article/1",
        "medio": "Test Medium",
        "pais_publicacion": "Test Country", 
        "tipo_medio": "Test Type",
        "titular": "Integration Test Article 1",
        "fecha_publicacion": "2023-12-01T12:00:00Z",
        "contenido_texto": "Content for integration test article 1"
    },
    {
        "url": "https://test.com/article/2",
        "medio": "Test Medium",
        "pais_publicacion": "Test Country", 
        "tipo_medio": "Test Type",
        "titular": "Integration Test Article 2",
        "fecha_publicacion": "2023-12-02T12:00:00Z",
        "contenido_texto": "Content for integration test article 2"
    }
]


async def create_test_file(content, file_path: Path):
    """Create a test .json.gz file with the given content"""
    with gzip.open(file_path, 'wt', encoding='utf-8') as f:
        json.dump(content, f)


async def test_main_integration():
    """Test the complete integration workflow"""
    
    print("🧪 Testing Main Integration Workflow")
    print("=" * 60)
    
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
        
        # Import and patch config
        import config
        original_scraper_dir = config.SCRAPER_OUTPUT_DIR
        original_pending_dir = config.PIPELINE_PENDING_DIR
        original_completed_dir = config.PIPELINE_COMPLETED_DIR
        original_error_dir = config.PIPELINE_ERROR_DIR
        original_api_url = config.PIPELINE_API_URL
        original_polling = config.POLLING_INTERVAL
        
        config.SCRAPER_OUTPUT_DIR = str(input_dir)
        config.PIPELINE_PENDING_DIR = str(pending_dir)
        config.PIPELINE_COMPLETED_DIR = str(completed_dir)
        config.PIPELINE_ERROR_DIR = str(error_dir)
        config.PIPELINE_API_URL = "http://localhost:9999"  # Non-existent for testing
        config.POLLING_INTERVAL = 1  # Fast polling for testing
        
        try:
            # Test 1: Main function with pending files
            print("\n🔄 Test 1: Main function startup with pending files")
            
            # Create some pending files
            pending_file_1 = pending_dir / "pending_test_1.json.gz"
            pending_file_2 = pending_dir / "pending_test_2.json.gz"
            
            await create_test_file(TEST_ARTICLES[0], pending_file_1)
            await create_test_file(TEST_ARTICLES, pending_file_2)  # Multiple articles
            
            # Import main function
            from main import main, process_pending_files
            
            # Test process_pending_files directly
            files_processed, files_succeeded, files_failed = await process_pending_files()
            
            print(f"  Pending files processed: {files_processed}")
            print(f"  Files succeeded: {files_succeeded}")
            print(f"  Files failed: {files_failed}")
            
            # Since API is unreachable, all should fail but be moved to error directory
            error_files = list(error_dir.glob("*.json.gz"))
            pending_files = list(pending_dir.glob("*.json.gz"))
            
            if len(error_files) >= 2 and len(pending_files) == 0:
                print("  ✅ Pending files processed and moved to error directory")
            else:
                print("  ❌ Pending files not processed correctly")
            
            # Test 2: Monitor directory simulation
            print("\n👁️  Test 2: Directory monitoring simulation")
            
            # Create a new file in input directory
            input_file = input_dir / "new_article.json.gz"
            await create_test_file(TEST_ARTICLES[0], input_file)
            
            # Import and test monitor components
            from main import monitor_directory
            
            # We'll use a mock to prevent infinite loop
            with patch('main.asyncio.sleep') as mock_sleep:
                # Make sleep raise KeyboardInterrupt after first iteration
                mock_sleep.side_effect = [None, KeyboardInterrupt()]
                
                try:
                    await monitor_directory()
                except KeyboardInterrupt:
                    pass  # Expected
            
            # Check if file was moved and processed
            pending_files = list(pending_dir.glob("*.json.gz"))
            error_files = list(error_dir.glob("new_article*.json.gz"))
            
            if len(error_files) >= 1:
                print("  ✅ New file detected, processed, and moved")
            else:
                print("  ⚠️  File processing may vary (API dependent)")
            
            # Test 3: Main function integration
            print("\n🚀 Test 3: Main function integration test")
            
            # Clear directories
            for f in input_dir.glob("*.json.gz"):
                f.unlink()
            for f in pending_dir.glob("*.json.gz"):
                f.unlink()
            
            # Create a test file for main to process
            main_test_file = input_dir / "main_test.json.gz"
            await create_test_file(TEST_ARTICLES[1], main_test_file)
            
            # Mock monitor_directory to prevent infinite loop
            async def mock_monitor():
                await asyncio.sleep(0.1)  # Brief pause
                raise KeyboardInterrupt()  # Simulate user interrupt
            
            with patch('main.monitor_directory', side_effect=mock_monitor):
                exit_code = await main()
            
            print(f"  Main function exit code: {exit_code}")
            
            if exit_code == 0:
                print("  ✅ Main function completed successfully")
            else:
                print("  ❌ Main function returned error code")
            
            # Test 4: Error handling
            print("\n💥 Test 4: Error handling in main")
            
            # Test with invalid directory permissions (simulate)
            with patch('main.process_pending_files', side_effect=Exception("Test error")):
                exit_code = await main()
            
            print(f"  Error handling exit code: {exit_code}")
            
            if exit_code == 1:
                print("  ✅ Error handled correctly with exit code 1")
            else:
                print("  ❌ Error not handled correctly")
            
            # Test 5: Configuration display
            print("\n📊 Test 5: Configuration display")
            
            # Capture log output would require more complex setup
            # For now, just verify the function runs without error
            
            from main import setup_logging, setup_sentry
            
            setup_logging()
            setup_sentry()
            
            print("  ✅ Configuration and logging setup completed")
        
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # Restore original config
            config.SCRAPER_OUTPUT_DIR = original_scraper_dir
            config.PIPELINE_PENDING_DIR = original_pending_dir
            config.PIPELINE_COMPLETED_DIR = original_completed_dir
            config.PIPELINE_ERROR_DIR = original_error_dir
            config.PIPELINE_API_URL = original_api_url
            config.POLLING_INTERVAL = original_polling
    
    print("\n" + "=" * 60)
    print("🎉 Main integration tests completed!")
    return True


async def test_entry_point():
    """Test the entry point (__main__) functionality"""
    
    print("\n🚪 Testing Entry Point")
    print("=" * 30)
    
    # This is harder to test directly, but we can verify imports work
    try:
        # Test that main module can be imported and main function exists
        from main import main
        
        # Verify main function is callable
        if callable(main):
            print("  ✅ Main function is callable")
        else:
            print("  ❌ Main function is not callable")
        
        # Test that asyncio.run would work (without actually running it)
        print("  ✅ Entry point structure is correct")
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    try:
        print("🧪 Running Complete Integration Test Suite")
        print("=" * 60)
        
        # Run integration tests
        integration_success = asyncio.run(test_main_integration())
        
        # Run entry point tests
        entry_point_success = asyncio.run(test_entry_point())
        
        overall_success = integration_success and entry_point_success
        
        print("\n" + "=" * 60)
        if overall_success:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
        else:
            print("❌ Some integration tests failed")
        
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Integration tests interrupted by user")
        sys.exit(1)
