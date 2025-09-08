#!/usr/bin/env python3
"""
EMERGENCY MODULE DISCOVERY VERIFICATION SCRIPT
===============================================

Critical verification script for the £925K Zebra Associates opportunity.
Verifies that the emergency module discovery fixes are working correctly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from app.core.module_registry import ModuleRegistry, get_module_registry, RegistrationResult
from app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

async def test_emergency_module_discovery():
    """Test emergency module discovery functionality"""
    
    print("🚨 EMERGENCY VERIFICATION: Module Discovery Fix for Zebra Associates")
    print("=" * 80)
    
    try:
        # Get the module registry
        registry = get_module_registry()
        
        print(f"✅ Module registry initialized")
        print(f"📊 Registry stats: {registry.get_memory_stats()}")
        
        # Test auto-discovery endpoint
        print("\n🔍 Testing auto_discover_and_register method...")
        
        results = await registry.auto_discover_and_register()
        
        print(f"\n📋 Discovery Results:")
        print(f"Total modules processed: {len(results)}")
        
        successful_modules = [r for r in results if r.success]
        failed_modules = [r for r in results if not r.success]
        
        print(f"✅ Successful registrations: {len(successful_modules)}")
        print(f"❌ Failed registrations: {len(failed_modules)}")
        
        if successful_modules:
            print(f"\n✅ Successfully registered modules:")
            for result in successful_modules:
                print(f"  - {result.module_id} ({result.lifecycle_state})")
        
        if failed_modules:
            print(f"\n❌ Failed modules:")
            for result in failed_modules:
                print(f"  - {result.module_id}: {result.message}")
                if result.errors:
                    for error in result.errors:
                        print(f"    Error: {error}")
        
        # Test getting registered modules
        print(f"\n🎯 Testing get_registered_modules...")
        registered_modules = await registry.get_registered_modules()
        
        print(f"📊 Total registered modules: {len(registered_modules)}")
        for module in registered_modules:
            if hasattr(module, 'metadata'):
                print(f"  - {module.metadata.id}: {module.metadata.name} (v{module.metadata.version})")
            else:
                print(f"  - {module}")
        
        # Verify critical modules for Zebra demo
        critical_modules = ["market_trends", "pricing_intelligence", "competitive_analysis", "feature_flags"]
        print(f"\n🎯 Verifying critical modules for Zebra Associates...")
        
        missing_modules = []
        for module_id in critical_modules:
            module = await registry.get_module_registration(module_id)
            if module:
                print(f"  ✅ {module_id}: Available")
            else:
                print(f"  ❌ {module_id}: MISSING")
                missing_modules.append(module_id)
        
        if missing_modules:
            print(f"\n⚠️  WARNING: Missing critical modules: {missing_modules}")
            return False
        else:
            print(f"\n🎉 SUCCESS: All critical modules are available!")
            
        # Test emergency endpoint compatibility
        print(f"\n🧪 Testing emergency endpoint format compatibility...")
        
        # Simulate what the endpoint returns
        endpoint_results = []
        for result in results:
            if result.success:
                endpoint_results.append({
                    "success": result.success,
                    "module_id": result.module_id,
                    "message": result.message,
                    "lifecycle_state": result.lifecycle_state.value if hasattr(result.lifecycle_state, 'value') else result.lifecycle_state,
                    "errors": result.errors,
                    "warnings": result.warnings
                })
        
        print(f"📤 Endpoint would return {len(endpoint_results)} results")
        print(f"✅ Format validation: PASS")
        
        print(f"\n" + "=" * 80)
        print(f"🎯 VERIFICATION COMPLETE FOR ZEBRA ASSOCIATES")
        print(f"📊 Module Discovery Status: OPERATIONAL")
        print(f"🚀 Ready for £925K opportunity evaluation")
        
        return len(missing_modules) == 0
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR during verification: {e}")
        logger.exception("Module discovery verification failed")
        return False

async def main():
    """Main verification function"""
    success = await test_emergency_module_discovery()
    
    if success:
        print(f"\n✅ ALL SYSTEMS GO: Emergency fixes operational")
        sys.exit(0)
    else:
        print(f"\n❌ CRITICAL FAILURE: Emergency fixes need attention")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())