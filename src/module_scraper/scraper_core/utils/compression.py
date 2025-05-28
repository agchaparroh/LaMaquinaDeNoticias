"""
HTML Compression Utility
========================

This module provides utilities for compressing and decompressing HTML content
using gzip compression. This is used to reduce storage size when saving HTML
to Supabase Storage.
"""
import gzip
import logging
from typing import Union, Optional

logger = logging.getLogger(__name__)


def compress_html(
    html_content: Union[str, bytes], 
    compression_level: int = 6,
    encoding: str = 'utf-8'
) -> bytes:
    """
    Compress HTML content using gzip compression.
    
    Args:
        html_content: The HTML content to compress (string or bytes)
        compression_level: Compression level (0-9, where 9 is maximum compression)
        encoding: Text encoding to use if html_content is a string
        
    Returns:
        Compressed content as bytes
        
    Raises:
        ValueError: If compression_level is not between 0 and 9
        UnicodeEncodeError: If encoding fails
    """
    if not 0 <= compression_level <= 9:
        raise ValueError(f"Compression level must be between 0 and 9, got {compression_level}")
    
    try:
        # Convert string to bytes if necessary
        if isinstance(html_content, str):
            html_bytes = html_content.encode(encoding)
        else:
            html_bytes = html_content
        
        # Compress the content
        compressed = gzip.compress(html_bytes, compresslevel=compression_level)
        
        # Log compression statistics
        original_size = len(html_bytes)
        compressed_size = len(compressed)
        compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        logger.debug(
            f"Compressed HTML from {original_size} bytes to {compressed_size} bytes "
            f"({compression_ratio:.1f}% reduction)"
        )
        
        return compressed
        
    except Exception as e:
        logger.error(f"Failed to compress HTML: {str(e)}")
        raise


def decompress_html(
    compressed_content: bytes,
    encoding: str = 'utf-8',
    return_bytes: bool = False
) -> Union[str, bytes]:
    """
    Decompress gzip-compressed HTML content.
    
    Args:
        compressed_content: The compressed content as bytes
        encoding: Text encoding to use for decoding (if return_bytes is False)
        return_bytes: If True, return decompressed content as bytes; otherwise as string
        
    Returns:
        Decompressed content as string or bytes
        
    Raises:
        gzip.BadGzipFile: If the input is not valid gzip data
        UnicodeDecodeError: If decoding fails when return_bytes is False
    """
    try:
        # Decompress the content
        decompressed_bytes = gzip.decompress(compressed_content)
        
        # Return as bytes or string based on preference
        if return_bytes:
            return decompressed_bytes
        else:
            return decompressed_bytes.decode(encoding)
            
    except gzip.BadGzipFile as e:
        logger.error(f"Invalid gzip data: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to decompress HTML: {str(e)}")
        raise


def estimate_compression_ratio(
    html_content: Union[str, bytes],
    sample_size: Optional[int] = None,
    encoding: str = 'utf-8'
) -> float:
    """
    Estimate the compression ratio for HTML content.
    
    This can be useful for deciding whether compression is worthwhile
    or for estimating storage requirements.
    
    Args:
        html_content: The HTML content to analyze
        sample_size: If provided, only use first N bytes for estimation
        encoding: Text encoding to use if html_content is a string
        
    Returns:
        Estimated compression ratio (0.0 to 1.0, where 1.0 means 100% size reduction)
    """
    try:
        # Convert to bytes if necessary
        if isinstance(html_content, str):
            html_bytes = html_content.encode(encoding)
        else:
            html_bytes = html_content
        
        # Use sample if specified
        if sample_size and len(html_bytes) > sample_size:
            sample_bytes = html_bytes[:sample_size]
        else:
            sample_bytes = html_bytes
        
        # Compress the sample
        compressed = gzip.compress(sample_bytes, compresslevel=6)
        
        # Calculate ratio
        original_size = len(sample_bytes)
        compressed_size = len(compressed)
        
        if original_size == 0:
            return 0.0
        
        return 1.0 - (compressed_size / original_size)
        
    except Exception as e:
        logger.error(f"Failed to estimate compression ratio: {str(e)}")
        return 0.0


def is_compressed(data: bytes) -> bool:
    """
    Check if data is gzip-compressed.
    
    Args:
        data: The data to check
        
    Returns:
        True if data appears to be gzip-compressed, False otherwise
    """
    # Gzip magic number is 1f 8b
    return len(data) >= 2 and data[0] == 0x1f and data[1] == 0x8b


def get_compression_info(compressed_data: bytes) -> dict:
    """
    Get information about gzip-compressed data.
    
    Args:
        compressed_data: The compressed data to analyze
        
    Returns:
        Dictionary containing compression information
    """
    try:
        # Decompress to get original size
        decompressed = gzip.decompress(compressed_data)
        
        return {
            'compressed_size': len(compressed_data),
            'original_size': len(decompressed),
            'compression_ratio': 1.0 - (len(compressed_data) / len(decompressed)) if len(decompressed) > 0 else 0.0,
            'is_valid_gzip': True
        }
    except Exception as e:
        return {
            'compressed_size': len(compressed_data),
            'original_size': None,
            'compression_ratio': None,
            'is_valid_gzip': False,
            'error': str(e)
        }
