"""
Utility modules for the scraper core.
"""
from .supabase_client import SupabaseClient, get_supabase_client
from .compression import compress_html, decompress_html

__all__ = ['SupabaseClient', 'get_supabase_client', 'compress_html', 'decompress_html']
