#!/usr/bin/env python3
"""
SIMPLE EMERGENCY TEST - Module Discovery Fix Verification
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

async def test_auto_discover():
    """Simple test of auto_discover_and_register method"""
    try:
        from app.core.module_registry import get_module_registry
        
        print("🚨 EMERGENCY TEST: Module Discovery for £925K Zebra Associates")
        print("=" * 60)
        
        # Get registry
        registry = get_module_registry()
        print("✅ Module registry obtained")
        
        # Test auto discovery method exists
        if hasattr(registry, 'auto_discover_and_register'):
            print("✅ auto_discover_and_register method exists")
            
            # Test method execution
            results = await registry.auto_discover_and_register()
            print(f"✅ Method executed successfully")
            print(f"📊 Results: {len(results)} modules processed")
            
            # Check results format
            for result in results[:3]:  # Show first 3
                print(f"  - {result.module_id}: {result.success} ({result.message})")
            
            # Check registered modules
            registered = list(registry.registered_modules.keys())
            print(f"📋 Registered modules: {registered}")
            
            critical_modules = ["market_trends", "pricing_intelligence", "competitive_analysis"]
            missing = [m for m in critical_modules if m not in registered]
            
            if not missing:
                print("🎉 SUCCESS: All critical modules available!")
                return True
            else:
                print(f"⚠️  Missing: {missing}")
                return False
                
        else:
            print("❌ auto_discover_and_register method missing!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_auto_discover())
    if success:
        print("\n🎯 EMERGENCY FIX: OPERATIONAL")
    else:
        print("\n❌ EMERGENCY FIX: NEEDS ATTENTION")
    sys.exit(0 if success else 1)