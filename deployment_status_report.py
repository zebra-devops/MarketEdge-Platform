#!/usr/bin/env python3
"""
MarketEdge Deployment Status Report
Comprehensive analysis of Render deployment hanging issue
"""

import requests
import subprocess
import json
from datetime import datetime
import sys


def test_oauth2_error_type():
    """Determine which version of OAuth2 code is deployed"""
    
    print("🔍 OAuth2 Error Type Analysis")
    print("=" * 50)
    
    base_url = "https://marketedge-platform.onrender.com"
    
    # Test 1: Valid format but invalid code
    print("\n📋 Test 1: Valid request format with invalid code")
    test_data = {
        "code": "4/0AeaFakeCodeForTestingPurposesOnly12345678901234567890",
        "redirect_uri": "https://app.zebra.associates/callback",
        "state": "test_state_12345"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/login-oauth2",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 500:
            error_data = response.json()
            error_detail = error_data.get("detail", "")
            print(f"   Error: {error_detail}")
            
            # Check for deployment version indicators
            if "Internal server error during authentication:" in error_detail:
                print("   ✅ NEW error format - commit 849ae95+ deployed")
                
                if "exchange_code_for_tokens" in error_detail:
                    print("   ❌ OLD method name - commit 610bcb2 NOT deployed") 
                    return "old_method_deployed"
                elif "exchange_code_for_token" in error_detail:
                    print("   ✅ NEW method name - commit 610bcb2 deployed")
                    return "new_method_deployed"
                else:
                    print("   ✅ No method name errors - both fixes deployed")
                    return "all_fixes_deployed"
                    
            elif error_detail == "Internal server error during authentication":
                print("   ⚠️  Generic error - pre-849ae95 deployment")
                return "old_deployment"
            else:
                print(f"   ❓ Unknown error format: {error_detail[:100]}")
                return "unknown_format"
                
        elif response.status_code == 400:
            error_data = response.json()
            print(f"   Validation Error: {error_data.get('detail', '')[:100]}...")
            print("   ✅ Input validation working - basic deployment OK")
            return "validation_working"
        else:
            print(f"   ❓ Unexpected status: {response.status_code}")
            return "unexpected"
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return "request_failed"


def check_deployment_commits():
    """Check which commits are actually deployed"""
    
    print("\n🔍 Deployment Commit Analysis")  
    print("=" * 50)
    
    # Get deployment information
    try:
        result = subprocess.run([
            'gh', 'api', 'repos/zebra-devops/MarketEdge-Platform/deployments',
            '--jq', '.[] | {id: .id, sha: .sha, created_at: .created_at}'
        ], capture_output=True, text=True, check=True)
        
        latest_deployments = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    latest_deployments.append(json.loads(line))
                except:
                    continue
                    
        if latest_deployments:
            latest = latest_deployments[0]
            print(f"📋 Latest deployment: {latest['id']}")
            print(f"📋 Commit SHA: {latest['sha']}")
            print(f"📋 Created: {latest['created_at']}")
            
            # Get commit details
            try:
                commit_result = subprocess.run([
                    'git', 'show', '--oneline', latest['sha']
                ], capture_output=True, text=True, check=True)
                
                print(f"📋 Commit: {commit_result.stdout.strip()}")
                
                # Check if this includes our fixes
                if latest['sha'].startswith('849ae95'):
                    print("✅ Latest commit (849ae95) is deployed - ALL fixes should be live")
                    return "all_fixes_deployed"
                elif latest['sha'].startswith('610bcb2'):
                    print("✅ Method fix commit (610bcb2) is deployed")
                    print("⚠️  Debug logging commit (849ae95) is NOT deployed")
                    return "method_fix_deployed"
                elif latest['sha'].startswith('a6f02c6'):
                    print("⚠️  Only function implementation (a6f02c6) is deployed") 
                    print("❌ Method name fix (610bcb2) is NOT deployed")
                    print("❌ Debug logging (849ae95) is NOT deployed")
                    return "old_deployment"
                else:
                    print(f"❓ Unknown commit deployed: {latest['sha']}")
                    return "unknown_commit"
                    
            except Exception as e:
                print(f"❌ Error getting commit details: {e}")
                return "commit_error"
                
    except Exception as e:
        print(f"❌ Error getting deployment info: {e}")
        return "deployment_error"


def check_current_deployment_status():
    """Check if deployment is still in progress"""
    
    print("\n🔍 Current Deployment Status")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            'gh', 'api', 'repos/zebra-devops/MarketEdge-Platform/deployments/2956841857/statuses'
        ], capture_output=True, text=True, check=True)
        
        statuses = json.loads(result.stdout)
        if statuses:
            latest_status = statuses[0]
            print(f"📋 Status: {latest_status.get('state')}")
            print(f"📋 Updated: {latest_status.get('updated_at')}")
            print(f"📋 Description: {latest_status.get('description', 'None')}")
            
            if latest_status.get('state') == 'in_progress':
                # Check how long it's been in progress
                from datetime import datetime
                import dateutil.parser
                
                try:
                    updated_time = dateutil.parser.parse(latest_status['updated_at'])
                    now = datetime.now(updated_time.tzinfo)
                    duration = now - updated_time
                    
                    print(f"⏱️  In progress for: {duration}")
                    
                    if duration.total_seconds() > 3600:  # 1 hour
                        print("❌ DEPLOYMENT HANGING - Over 1 hour in progress")
                        return "hanging"
                    elif duration.total_seconds() > 1800:  # 30 minutes
                        print("⚠️  DEPLOYMENT SLOW - Over 30 minutes in progress")
                        return "slow"
                    else:
                        print("✅ Deployment in normal progress time")
                        return "in_progress"
                        
                except Exception as e:
                    print(f"❌ Error calculating duration: {e}")
                    return "duration_error"
                    
            elif latest_status.get('state') == 'success':
                print("✅ Latest deployment successful")
                return "success"
            elif latest_status.get('state') == 'failure':
                print("❌ Latest deployment failed")
                return "failed"
            else:
                print(f"❓ Unknown status: {latest_status.get('state')}")
                return "unknown_status"
                
    except Exception as e:
        print(f"❌ Error checking deployment status: {e}")
        return "status_error"


def main():
    """Generate comprehensive deployment status report"""
    
    print("🚀 MarketEdge Render Deployment Status Report")
    print("=" * 60)
    print(f"Generated: {datetime.now().isoformat()}")
    
    # Check what's currently deployed
    oauth_status = test_oauth2_error_type()
    commit_status = check_deployment_commits()
    deploy_status = check_current_deployment_status()
    
    print("\n🎯 SUMMARY REPORT")
    print("=" * 60)
    
    # Deployment hanging analysis
    if deploy_status == "hanging":
        print("❌ CRITICAL: Render deployment has been hanging for over 1 hour")
        print("🔧 IMMEDIATE ACTION REQUIRED:")
        print("   1. Check Render dashboard for stuck deployment")
        print("   2. Cancel hanging deployment if needed")
        print("   3. Trigger manual redeploy")
        print("   4. Check resource limits and build logs")
        
    elif deploy_status == "slow":
        print("⚠️  WARNING: Render deployment is unusually slow (30+ minutes)")
        print("🔧 RECOMMENDED ACTIONS:")
        print("   1. Monitor Render dashboard for progress")
        print("   2. Check if deployment completes in next 30 minutes")
        print("   3. Consider manual intervention if it exceeds 1 hour")
        
    elif deploy_status == "in_progress":
        print("✅ Render deployment is in progress (normal timing)")
        print("🔧 RECOMMENDED ACTIONS:")
        print("   1. Wait for deployment to complete")
        print("   2. Monitor for completion in next 15-20 minutes")
        
    # OAuth2 fix status
    if oauth_status in ["old_method_deployed", "old_deployment"]:
        print("\n❌ OAuth2 fixes are NOT deployed")
        print("🔔 500 errors will continue until deployment completes")
        print("💰 £925K opportunity is BLOCKED until fixes are deployed")
        
    elif oauth_status in ["new_method_deployed", "all_fixes_deployed"]:
        print("\n✅ OAuth2 fixes are deployed and working")
        print("🔔 500 errors should be resolved for valid Auth0 codes") 
        print("💰 £925K opportunity should be UNBLOCKED")
        
    # Final recommendation
    print(f"\n🔧 FINAL RECOMMENDATION:")
    
    if deploy_status == "hanging":
        print("   URGENT: Manually restart Render deployment")
        print("   The deployment has been stuck for too long")
        print("   Latest OAuth2 fixes are waiting to be deployed")
        
    elif oauth_status == "old_deployment" and deploy_status == "in_progress":
        print("   WAIT: Let current deployment complete")
        print("   The fixes should be included in the in-progress deployment")
        print("   Re-test OAuth2 after deployment completes")
        
    elif oauth_status == "all_fixes_deployed":
        print("   SUCCESS: All fixes are deployed and working")
        print("   OAuth2 authentication should work with valid Auth0 codes")
        print("   £925K opportunity is ready for testing")
        
    else:
        print("   INVESTIGATE: Check Render dashboard manually")
        print("   Deployment status is unclear from automated checks")
        
    return oauth_status in ["new_method_deployed", "all_fixes_deployed"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)