#!/usr/bin/env python3
"""
Test script for file processing functionality
"""

import asyncio
import os
import tempfile
import sys
import gzip
import json
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test data
VALID_ARTICLE = {
    "url": "https://test.com/article/1",
    "medio": "Test Medium",
    "pais_publicacion": "Test Country", 
    "tipo_medio": "Test Type",
    "titular": "Test Title",
    "fecha_publicacion": "2023-12-01T12:00:00Z",
    "contenido_texto": "Test content text"
}

INVALID_ARTICLE = {
    "url": "https://test.com/article/2",
    "medio": "Test Medium",
    # Missing required fields: pais_publicacion, tipo_medio, titular, fecha_publicacion, contenido_texto
}

MULTIPLE_ARTICLES = [
    VALID_ARTICLE,
    {
        "medio": "Another Medium",
        "pais_publicacion": "Another Country",
        "tipo_medio": "Another Type", 
        "titular": "Another Title",
        "fecha_publicacion": "2023-12-02T12:00:00Z",
        "contenido_texto": "Another content text"
    },
    INVALID_ARTICLE  # This one should fail validation
]


async def create_test_file(content, file_path: Path, compress=True):
    """Create a test file with the given content"""
    if compress:
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            json.dump(content, f)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f)


async def test_file_processing():
    """Test the file processing functionality"""
    
    print("🧪 Testing File Processing Function")
    print("=" * 50)
    
    # Import the function we're testing
    from main import process_file
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test 1: Valid single article
        print("\n📄 Test 1: Valid single article")
        valid_file = temp_path / "valid_single.json.gz"
        await create_test_file(VALID_ARTICLE, valid_file)
        
        valid_articles, invalid_articles, has_valid = await process_file(str(valid_file))
        
        print(f"  Valid articles: {len(valid_articles)}")
        print(f"  Invalid articles: {len(invalid_articles)}")
        print(f"  Has valid: {has_valid}")
        
        if len(valid_articles) == 1 and len(invalid_articles) == 0 and has_valid:
            print("  ✅ Single valid article test passed")
        else:
            print("  ❌ Single valid article test failed")
        
        # Test 2: Invalid single article
        print("\n📄 Test 2: Invalid single article")
        invalid_file = temp_path / "invalid_single.json.gz"
        await create_test_file(INVALID_ARTICLE, invalid_file)
        
        valid_articles, invalid_articles, has_valid = await process_file(str(invalid_file))
        
        print(f"  Valid articles: {len(valid_articles)}")
        print(f"  Invalid articles: {len(invalid_articles)}")
        print(f"  Has valid: {has_valid}")
        
        if len(valid_articles) == 0 and len(invalid_articles) == 1 and not has_valid:
            print("  ✅ Single invalid article test passed")
        else:
            print("  ❌ Single invalid article test failed")
        
        # Test 3: Multiple articles (mixed valid/invalid)
        print("\n📄 Test 3: Multiple articles (mixed)")
        multiple_file = temp_path / "multiple_mixed.json.gz"
        await create_test_file(MULTIPLE_ARTICLES, multiple_file)
        
        valid_articles, invalid_articles, has_valid = await process_file(str(multiple_file))
        
        print(f"  Valid articles: {len(valid_articles)}")
        print(f"  Invalid articles: {len(invalid_articles)}")
        print(f"  Has valid: {has_valid}")
        
        if len(valid_articles) == 2 and len(invalid_articles) == 1 and has_valid:
            print("  ✅ Multiple mixed articles test passed")
        else:
            print("  ❌ Multiple mixed articles test failed")
        
        # Test 4: Malformed JSON
        print("\n📄 Test 4: Malformed JSON")
        malformed_file = temp_path / "malformed.json.gz"
        
        # Create a file with invalid JSON
        with gzip.open(malformed_file, 'wt', encoding='utf-8') as f:
            f.write('{\"invalid\": json content}')
        
        valid_articles, invalid_articles, has_valid = await process_file(str(malformed_file))
        
        print(f"  Valid articles: {len(valid_articles)}")
        print(f"  Invalid articles: {len(invalid_articles)}")
        print(f"  Has valid: {has_valid}")
        
        if len(valid_articles) == 0 and len(invalid_articles) == 0 and not has_valid:
            print("  ✅ Malformed JSON test passed")
        else:
            print("  ❌ Malformed JSON test failed")
        
        # Test 5: Non-existent file
        print("\n📄 Test 5: Non-existent file")
        nonexistent_file = temp_path / "does_not_exist.json.gz"
        
        valid_articles, invalid_articles, has_valid = await process_file(str(nonexistent_file))
        
        print(f"  Valid articles: {len(valid_articles)}")
        print(f"  Invalid articles: {len(invalid_articles)}")
        print(f"  Has valid: {has_valid}")
        
        if len(valid_articles) == 0 and len(invalid_articles) == 0 and not has_valid:
            print("  ✅ Non-existent file test passed")
        else:
            print("  ❌ Non-existent file test failed")
        
        # Test 6: Invalid gzip file
        print("\n📄 Test 6: Invalid gzip file")
        fake_gz_file = temp_path / "fake_gzip.json.gz"
        
        # Create a file that's not actually gzipped
        with open(fake_gz_file, 'w', encoding='utf-8') as f:
            f.write("This is not a gzip file")
        
        valid_articles, invalid_articles, has_valid = await process_file(str(fake_gz_file))
        
        print(f"  Valid articles: {len(valid_articles)}")
        print(f"  Invalid articles: {len(invalid_articles)}")
        print(f"  Has valid: {has_valid}")
        
        if len(valid_articles) == 0 and len(invalid_articles) == 0 and not has_valid:
            print("  ✅ Invalid gzip file test passed")
        else:
            print("  ❌ Invalid gzip file test failed")
    
    print("\n" + "=" * 50)
    print("🎉 File processing tests completed!")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_file_processing())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
