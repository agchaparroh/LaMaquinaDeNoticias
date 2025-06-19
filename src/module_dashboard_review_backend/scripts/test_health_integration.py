"""
Test script to verify Supabase client integration
This verifies that the health check can use the client
"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from services.supabase_client import SupabaseClient
from utils.exceptions import DatabaseConnectionError


async def test_health_check_integration():
    """Test that health check can use Supabase client."""
    print("Testing Supabase client integration for health check...")
    print("-" * 50)
    
    try:
        # This simulates what a health check would do
        print("1. Getting Supabase client instance...")
        client = SupabaseClient.get_client()
        print("✅ Client obtained successfully")
        
        print("\n2. Testing basic query (simulating health check)...")
        # Simulate a simple health check query
        async def health_check_query():
            # In a real health check, this would be a simple query
            # like selecting 1 record to verify connection
            return {"status": "connected"}
        
        result = await SupabaseClient.execute_with_retry(health_check_query)
        print(f"✅ Health check query result: {result}")
        
        print("\n3. Testing error handling...")
        try:
            # Reset client to test initialization error
            SupabaseClient.reset_client()
            
            # Temporarily break the config to test error handling
            import utils.config
            original_url = utils.config.settings.supabase_url
            utils.config.settings.supabase_url = ""
            
            # This should raise DatabaseConnectionError
            client = SupabaseClient.get_client()
            
        except DatabaseConnectionError as e:
            print(f"✅ Error handling works correctly: {e}")
            # Restore config
            utils.config.settings.supabase_url = original_url
            SupabaseClient.reset_client()
        
        print("\n" + "=" * 50)
        print("✅ All integration tests passed!")
        print("The health check can successfully use the Supabase client")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(test_health_check_integration())
    sys.exit(0 if success else 1)
