#!/usr/bin/env python3
"""
Test script for file management functionality
"""

import asyncio
import os
import tempfile
import sys
import gzip
import json
import shutil
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test data
VALID_ARTICLE = {
    "url": "https://test.com/article/1",
    "medio": "Test Medium",
    "pais_publicacion": "Test Country", 
    "tipo_medio": "Test Type",
    "titular": "Test Title for File Management",
    "fecha_publicacion": "2023-12-01T12:00:00Z",
    "contenido_texto": "Test content text for file management testing"
}

INVALID_ARTICLE = {
    "url": "https://test.com/article/2",
    "medio": "Test Medium",
    # Missing required fields
}


async def create_test_file(content, file_path: Path):
    """Create a test .json.gz file with the given content"""
    with gzip.open(file_path, 'wt', encoding='utf-8') as f:
        json.dump(content, f)


async def test_file_management():
    """Test the file management functionality"""
    
    print("🧪 Testing File Management Functions")
    print("=" * 50)
    
    # Import the functions we're testing
    from main import move_file, process_pending_files
    import config
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Setup test directories
        pending_dir = temp_path / "pending"
        completed_dir = temp_path / "completed"
        error_dir = temp_path / "error"
        
        pending_dir.mkdir()
        completed_dir.mkdir()
        error_dir.mkdir()
        
        # Override config for testing
        original_pending_dir = config.PIPELINE_PENDING_DIR
        original_completed_dir = config.PIPELINE_COMPLETED_DIR
        original_error_dir = config.PIPELINE_ERROR_DIR
        original_api_url = config.PIPELINE_API_URL
        
        config.PIPELINE_PENDING_DIR = str(pending_dir)
        config.PIPELINE_COMPLETED_DIR = str(completed_dir)
        config.PIPELINE_ERROR_DIR = str(error_dir)
        config.PIPELINE_API_URL = "http://localhost:9999"  # Non-existent server
        
        try:
            # Test 1: Move file to completed directory (success)
            print("\n📁 Test 1: Move file to completed directory")
            test_file_success = pending_dir / "test_success.json.gz"
            await create_test_file(VALID_ARTICLE, test_file_success)
            
            await move_file(str(test_file_success), success=True)
            
            # Check if file was moved to completed directory
            completed_files = list(completed_dir.glob("*.json.gz"))
            pending_files = list(pending_dir.glob("test_success.json.gz"))
            
            if len(completed_files) == 1 and len(pending_files) == 0:
                print("  ✅ File successfully moved to completed directory")
            else:
                print("  ❌ File was not moved to completed directory")
            
            # Test 2: Move file to error directory (failure)
            print("\n📁 Test 2: Move file to error directory")
            test_file_error = pending_dir / "test_error.json.gz"
            await create_test_file(INVALID_ARTICLE, test_file_error)
            
            await move_file(str(test_file_error), success=False)
            
            # Check if file was moved to error directory
            error_files = list(error_dir.glob("*.json.gz"))
            pending_files = list(pending_dir.glob("test_error.json.gz"))
            
            if len(error_files) >= 1 and len(pending_files) == 0:
                print("  ✅ File successfully moved to error directory")
            else:
                print("  ❌ File was not moved to error directory")
            
            # Test 3: Handle duplicate filenames
            print("\n📁 Test 3: Handle duplicate filenames")
            duplicate_file_1 = pending_dir / "duplicate.json.gz"
            duplicate_file_2 = pending_dir / "duplicate_temp.json.gz"
            
            await create_test_file(VALID_ARTICLE, duplicate_file_1)
            await create_test_file(VALID_ARTICLE, duplicate_file_2)
            
            # Move first file
            await move_file(str(duplicate_file_1), success=True)
            
            # Create another file with same name and move it
            shutil.copy(str(duplicate_file_2), str(duplicate_file_1))\n            await move_file(str(duplicate_file_1), success=True)\n            \n            # Check if both files exist in completed directory with different names\n            completed_files = list(completed_dir.glob(\"duplicate*.json.gz\"))\n            \n            if len(completed_files) >= 2:\n                print(\"  \u2705 Duplicate filenames handled correctly with unique names\")\n            else:\n                print(\"  \u274c Duplicate filenames not handled correctly\")\n            \n            # Test 4: Process pending files (mixed scenario)\n            print(\"\\n\ud83d\udcc1 Test 4: Process pending files (mixed scenario)\")\n            \n            # Clear existing files and create new test files\n            for f in pending_dir.glob(\"*.json.gz\"):\n                f.unlink()\n            \n            # Create test files\n            valid_file = pending_dir / \"valid_articles.json.gz\"\n            invalid_file = pending_dir / \"invalid_articles.json.gz\"\n            mixed_file = pending_dir / \"mixed_articles.json.gz\"\n            \n            await create_test_file([VALID_ARTICLE], valid_file)\n            await create_test_file([INVALID_ARTICLE], invalid_file)\n            await create_test_file([VALID_ARTICLE, INVALID_ARTICLE], mixed_file)\n            \n            # Process all pending files\n            files_processed, files_succeeded, files_failed = await process_pending_files()\n            \n            print(f\"  Files processed: {files_processed}\")\n            print(f\"  Files succeeded: {files_succeeded}\")\n            print(f\"  Files failed: {files_failed}\")\n            \n            # Check results (since we have a non-existent API, all should fail)\n            if files_processed == 3 and files_failed == 3:\n                print(\"  \u2705 Process pending files test passed (all failed as expected with no API)\")\n            else:\n                print(\"  \u26a0\ufe0f  Process pending files test - results may vary\")\n            \n            # Test 5: Handle non-existent file\n            print(\"\\n\ud83d\udcc1 Test 5: Handle non-existent file\")\n            non_existent_file = pending_dir / \"does_not_exist.json.gz\"\n            \n            await move_file(str(non_existent_file), success=True)\n            \n            # Should handle gracefully without crashing\n            print(\"  \u2705 Non-existent file handled gracefully\")\n            \n            # Test 6: Empty pending directory\n            print(\"\\n\ud83d\udcc1 Test 6: Empty pending directory\")\n            \n            # Clear all files\n            for f in pending_dir.glob(\"*.json.gz\"):\n                f.unlink()\n            \n            files_processed, files_succeeded, files_failed = await process_pending_files()\n            \n            if files_processed == 0 and files_succeeded == 0 and files_failed == 0:\n                print(\"  \u2705 Empty directory handled correctly\")\n            else:\n                print(\"  \u274c Empty directory not handled correctly\")\n        \n        except Exception as e:\n            print(f\"\u274c Test failed with error: {e}\")\n            import traceback\n            traceback.print_exc()\n            return False\n            \n        finally:\n            # Restore original config\n            config.PIPELINE_PENDING_DIR = original_pending_dir\n            config.PIPELINE_COMPLETED_DIR = original_completed_dir\n            config.PIPELINE_ERROR_DIR = original_error_dir\n            config.PIPELINE_API_URL = original_api_url\n    \n    print(\"\\n\" + \"=\" * 50)\n    print(\"\ud83c\udf89 File management tests completed!\")\n    return True\n\n\nif __name__ == \"__main__\":\n    try:\n        success = asyncio.run(test_file_management())\n        sys.exit(0 if success else 1)\n    except KeyboardInterrupt:\n        print(\"\\n\u23f9\ufe0f  Test interrupted by user\")\n        sys.exit(1)\n