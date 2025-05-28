"""
Tests for HTML compression utilities.
"""
import unittest
import gzip
from scraper_core.utils.compression import (
    compress_html, 
    decompress_html, 
    estimate_compression_ratio,
    is_compressed,
    get_compression_info
)


class TestCompressionUtils(unittest.TestCase):
    """Test cases for compression utility functions."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Test Article</title>
        </head>
        <body>
            <h1>Sample News Article</h1>
            <p>This is a test article with some content that should compress well.</p>
            <p>Repeated content repeated content repeated content repeated content.</p>
            <p>More repeated content repeated content repeated content.</p>
        </body>
        </html>
        """
        self.sample_bytes = self.sample_html.encode('utf-8')
    
    def test_compress_html_string(self):
        """Test compressing HTML from string."""
        compressed = compress_html(self.sample_html)
        
        self.assertIsInstance(compressed, bytes)
        self.assertLess(len(compressed), len(self.sample_bytes))
        self.assertTrue(is_compressed(compressed))
    
    def test_compress_html_bytes(self):
        """Test compressing HTML from bytes."""
        compressed = compress_html(self.sample_bytes)
        
        self.assertIsInstance(compressed, bytes)
        self.assertLess(len(compressed), len(self.sample_bytes))
        self.assertTrue(is_compressed(compressed))
    
    def test_compress_with_different_levels(self):
        """Test compression with different compression levels."""
        sizes = {}
        
        for level in [0, 1, 6, 9]:
            compressed = compress_html(self.sample_html, compression_level=level)
            sizes[level] = len(compressed)
        
        # Higher compression levels should generally produce smaller files
        self.assertGreaterEqual(sizes[0], sizes[1])
        self.assertGreaterEqual(sizes[1], sizes[6])
        self.assertGreaterEqual(sizes[6], sizes[9])
    
    def test_compress_invalid_level(self):
        """Test compression with invalid compression level."""
        with self.assertRaises(ValueError):
            compress_html(self.sample_html, compression_level=-1)
        
        with self.assertRaises(ValueError):
            compress_html(self.sample_html, compression_level=10)
    
    def test_decompress_to_string(self):
        """Test decompressing to string."""
        compressed = compress_html(self.sample_html)
        decompressed = decompress_html(compressed)
        
        self.assertIsInstance(decompressed, str)
        self.assertEqual(decompressed, self.sample_html)
    
    def test_decompress_to_bytes(self):
        """Test decompressing to bytes."""
        compressed = compress_html(self.sample_html)
        decompressed = decompress_html(compressed, return_bytes=True)
        
        self.assertIsInstance(decompressed, bytes)
        self.assertEqual(decompressed, self.sample_bytes)
    
    def test_decompress_invalid_data(self):
        """Test decompressing invalid data."""
        with self.assertRaises(gzip.BadGzipFile):
            decompress_html(b'invalid gzip data')
    
    def test_round_trip_compression(self):
        """Test that compression and decompression preserve content."""
        original = self.sample_html
        
        # Test multiple compression levels
        for level in [1, 6, 9]:
            compressed = compress_html(original, compression_level=level)
            decompressed = decompress_html(compressed)
            self.assertEqual(original, decompressed)
    
    def test_estimate_compression_ratio(self):
        """Test compression ratio estimation."""
        ratio = estimate_compression_ratio(self.sample_html)
        
        self.assertIsInstance(ratio, float)
        self.assertGreater(ratio, 0.0)
        self.assertLess(ratio, 1.0)
    
    def test_estimate_compression_ratio_with_sample(self):
        """Test compression ratio estimation with sample size."""
        # Large HTML content
        large_html = self.sample_html * 100
        
        # Estimate with full content
        full_ratio = estimate_compression_ratio(large_html)
        
        # Estimate with sample
        sample_ratio = estimate_compression_ratio(large_html, sample_size=1000)
        
        # Both should be reasonable estimates
        self.assertGreater(full_ratio, 0.0)
        self.assertGreater(sample_ratio, 0.0)
    
    def test_is_compressed(self):
        """Test detection of compressed data."""
        compressed = compress_html(self.sample_html)
        
        self.assertTrue(is_compressed(compressed))
        self.assertFalse(is_compressed(self.sample_bytes))
        self.assertFalse(is_compressed(b''))
        self.assertFalse(is_compressed(b'x'))
    
    def test_get_compression_info(self):
        """Test getting compression information."""
        compressed = compress_html(self.sample_html)
        info = get_compression_info(compressed)
        
        self.assertTrue(info['is_valid_gzip'])
        self.assertEqual(info['compressed_size'], len(compressed))
        self.assertEqual(info['original_size'], len(self.sample_bytes))
        self.assertGreater(info['compression_ratio'], 0.0)
        self.assertLess(info['compression_ratio'], 1.0)
    
    def test_get_compression_info_invalid(self):
        """Test getting compression info for invalid data."""
        info = get_compression_info(b'invalid data')
        
        self.assertFalse(info['is_valid_gzip'])
        self.assertIsNone(info['original_size'])
        self.assertIsNone(info['compression_ratio'])
        self.assertIn('error', info)
    
    def test_unicode_content(self):
        """Test compression with Unicode content."""
        unicode_html = """
        <html>
        <body>
            <p>Español: ñáéíóú</p>
            <p>中文内容</p>
            <p>Emoji: 😀 🎉 🌟</p>
        </body>
        </html>
        """
        
        compressed = compress_html(unicode_html)
        decompressed = decompress_html(compressed)
        
        self.assertEqual(unicode_html, decompressed)
    
    def test_empty_content(self):
        """Test compression of empty content."""
        compressed = compress_html('')
        decompressed = decompress_html(compressed)
        
        self.assertEqual('', decompressed)


if __name__ == '__main__':
    unittest.main()
