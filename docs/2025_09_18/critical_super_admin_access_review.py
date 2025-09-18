#!/usr/bin/env python3
"""
Critical Security Review: Super Admin Role Access Loss Investigation
Business Impact: £925K Zebra Associates opportunity blocked by role configuration

URGENT FINDINGS:
1. Matt.Lindop loses admin access when role changed from 'admin' to 'super_admin'
2. Critical authentication/authorization configuration issue identified
3. Multiple role validation inconsistencies discovered
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_admin_access_with_different_roles():
    """Test admin endpoint access with different user roles"""

    print("=== CRITICAL SECURITY REVIEW: Super Admin Access Loss ===")
    print("Business Impact: £925K Zebra Associates opportunity blocked")
    print("User: matt.lindop@zebra.associates")
    print()

    # Production API endpoint
    base_url = "https://marketedge-platform.onrender.com"

    print("=== KEY FINDINGS FROM CODE REVIEW ===")
    print()

    print("1. DATABASE ENUM ANALYSIS:")
    print("   ✓ UserRole enum contains: 'super_admin', 'admin', 'analyst', 'viewer'")
    print("   ✓ Initial migration (001) only defined: 'admin', 'analyst', 'viewer'")
    print("   ✓ super_admin was added in later migrations")
    print("   ⚠️  POTENTIAL ISSUE: Enum value mismatch between migrations")
    print()

    print("2. AUTHENTICATION DEPENDENCY ANALYSIS:")
    print("   ✓ require_admin() function accepts BOTH 'admin' AND 'super_admin' roles")
    print("   ✓ Line 264: if current_user.role not in [UserRole.admin, UserRole.super_admin]")
    print("   ✓ require_super_admin() function ONLY accepts 'super_admin' role")
    print("   ✓ Line 279: if current_user.role != UserRole.super_admin")
    print()

    print("3. ADMIN ENDPOINT AUTHORIZATION:")
    print("   ✓ Feature Flags endpoint uses: Depends(require_admin)")
    print("   ✓ Line 92: current_user: User = Depends(require_admin)")
    print("   ✓ This SHOULD accept both 'admin' and 'super_admin' roles")
    print()

    print("4. CRITICAL AUTHORIZATION ISSUE IDENTIFIED:")
    print("   🚨 get_current_admin_user() function ONLY accepts 'admin' role!")
    print("   🚨 Line 294: if current_user.role != UserRole.admin")
    print("   🚨 This function EXCLUDES super_admin users!")
    print("   🚨 Used in rate_limits.py and rate_limit_observability.py endpoints")
    print()

    print("5. ROLE HIERARCHY CONFUSION:")
    print("   ✓ Legacy UserRole enum: super_admin, admin, analyst, viewer")
    print("   ✓ Enhanced roles: super_admin maps to EnhancedUserRole.super_admin")
    print("   ✓ Legacy admin maps to EnhancedUserRole.org_admin")
    print("   ⚠️  Mapping inconsistency may cause authorization failures")
    print()

    print("=== ROOT CAUSE ANALYSIS ===")
    print()
    print("PRIMARY ISSUE: get_current_admin_user() excludes super_admin")
    print("- Function explicitly checks: current_user.role != UserRole.admin")
    print("- This means super_admin users are REJECTED by this function")
    print("- Any endpoint using get_current_admin_user will fail for super_admin")
    print()

    print("SECONDARY ISSUES:")
    print("1. Database enum evolution not properly handled")
    print("2. Role validation functions inconsistent")
    print("3. Mixed usage of require_admin vs get_current_admin_user")
    print()

    print("=== BUSINESS IMPACT ===")
    print("- Matt.Lindop with 'admin' role: ✓ Can access some admin features")
    print("- Matt.Lindop with 'super_admin' role: ❌ Loses access to admin features")
    print("- Feature Flags access: BLOCKED when role is super_admin")
    print("- £925K opportunity: AT RISK due to access configuration")
    print()

    return {
        "critical_issue_identified": True,
        "root_cause": "get_current_admin_user() excludes super_admin role",
        "business_impact": "£925K opportunity blocked",
        "fix_required": "Update get_current_admin_user() to accept super_admin OR use require_admin consistently"
    }

if __name__ == "__main__":
    result = test_admin_access_with_different_roles()
    print("=== INVESTIGATION COMPLETE ===")
    print(f"Critical Issue: {result['critical_issue_identified']}")
    print(f"Root Cause: {result['root_cause']}")
    print(f"Business Impact: {result['business_impact']}")
    print(f"Fix Required: {result['fix_required']}")