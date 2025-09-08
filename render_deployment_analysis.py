#!/usr/bin/env python3
"""
Comprehensive Render Deployment Analysis for MarketEdge Platform
Analyzes deployment status, commit timing, and OAuth2 functionality
"""

import requests
import subprocess
import json
from datetime import datetime, timezone
import sys


def get_git_commits():
    """Get recent git commits with timestamps"""
    try:
        result = subprocess.run([
            'git', 'log', '--pretty=format:%H|%ai|%s', '-10'
        ], capture_output=True, text=True, check=True)
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                hash_part, timestamp, message = line.split('|', 2)
                commits.append({
                    'hash': hash_part[:7],
                    'full_hash': hash_part,
                    'timestamp': timestamp,
                    'message': message
                })
        return commits
    except Exception as e:
        print(f"Error getting git commits: {e}")
        return []


def get_deployment_status():
    """Get deployment status from GitHub API"""
    try:
        # Get recent deployments
        result = subprocess.run([
            'gh', 'api', 'repos/zebra-devops/MarketEdge-Platform/deployments',
            '--jq', '.[] | {id: .id, ref: .ref, sha: .sha, task: .task, environment: .environment, created_at: .created_at}'
        ], capture_output=True, text=True, check=True)
        
        deployments = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    deployments.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                    
        return deployments[:5]  # Get latest 5
    except Exception as e:
        print(f"Error getting deployment status: {e}")
        return []


def get_deployment_details(deployment_id):
    """Get detailed status of a specific deployment"""
    try:
        result = subprocess.run([
            'gh', 'api', f'repos/zebra-devops/MarketEdge-Platform/deployments/{deployment_id}/statuses',
            '--jq', '.[] | {state: .state, description: .description, created_at: .created_at, updated_at: .updated_at}'
        ], capture_output=True, text=True, check=True)
        
        statuses = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    statuses.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                    
        return statuses
    except Exception as e:
        print(f"Error getting deployment details: {e}")
        return []


def test_oauth2_deployment():
    """Test OAuth2 functionality to determine if latest fixes are deployed"""
    print("🔍 Testing OAuth2 Endpoint Deployment Status")
    print("=" * 60)
    
    base_url = "https://marketedge-platform.onrender.com"
    
    # Test with a realistic-looking but invalid OAuth2 code
    test_payload = {
        "code": "4/0AeanS0bGoogleStyleCodeThatShouldTriggerAuth0Call12345",
        "redirect_uri": "https://app.zebra.associates/callback",
        "state": "deployment_test_state_12345"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/login-oauth2",
            json=test_payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "MarketEdge-DeploymentTest/1.0"
            },
            timeout=30
        )
        
        print(f"📊 Response Code: {response.status_code}")
        
        if response.status_code == 500:
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", "")
                
                print(f"📊 Error Detail: {error_detail[:100]}...")
                
                # Check for specific deployment markers
                if "Internal server error during authentication:" in error_detail:
                    print("✅ NEW error format detected - latest commits likely deployed")
                    
                    if "exchange_code_for_tokens" in error_detail:
                        print("❌ OLD method name detected - OAuth2 fix NOT deployed")
                        return "fix_not_deployed"
                    elif "AttributeError" in error_detail and "has no attribute" in error_detail:
                        print("❌ Method name error detected - OAuth2 fix NOT deployed")
                        return "fix_not_deployed"
                    else:
                        print("✅ No method name errors - OAuth2 fix appears deployed")
                        return "fix_deployed"
                        
                elif "Internal server error during authentication" == error_detail:
                    print("⚠️  Generic error format - deployment status unclear")
                    return "status_unclear"
                else:
                    print("⚠️  Unexpected error format")
                    return "status_unclear"
                    
            except json.JSONDecodeError:
                print("❌ Could not parse error response")
                return "parse_error"
                
        else:
            print(f"⚠️  Unexpected response code: {response.status_code}")
            return "unexpected_response"
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - possible deployment/server issues")
        return "timeout"
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return "request_error"


def analyze_deployment_timeline():
    """Analyze the deployment timeline vs commit timeline"""
    print("\n📅 Deployment Timeline Analysis")
    print("=" * 60)
    
    # Get commits and deployments
    commits = get_git_commits()
    deployments = get_deployment_status()
    
    if not commits:
        print("❌ Could not retrieve git commits")
        return
        
    if not deployments:
        print("❌ Could not retrieve deployment information")
        return
    
    print("\n📝 Recent Commits:")
    for i, commit in enumerate(commits[:5]):
        marker = "🔥" if i < 2 else "📝"
        print(f"  {marker} {commit['hash']} - {commit['timestamp']}")
        print(f"     {commit['message']}")
    
    print(f"\n🚀 Recent Deployments:")
    for i, deployment in enumerate(deployments[:3]):
        status_info = get_deployment_details(deployment['id'])
        latest_status = status_info[0] if status_info else {"state": "unknown"}
        
        marker = "🔥" if i == 0 else "🚀"
        print(f"  {marker} Deploy {deployment['id']} - {deployment['created_at']}")
        print(f"     Status: {latest_status.get('state', 'unknown')}")
        
        if deployment.get('sha'):
            print(f"     SHA: {deployment['sha'][:7]}")
    
    # Analysis
    latest_commit = commits[0]
    latest_deployment = deployments[0]
    
    print(f"\n🔍 Analysis:")
    print(f"  Latest Commit: {latest_commit['hash']} at {latest_commit['timestamp']}")
    print(f"  Latest Deploy: {latest_deployment['id']} at {latest_deployment['created_at']}")
    
    # Parse timestamps for comparison
    try:
        from dateutil import parser
        
        commit_time = parser.parse(latest_commit['timestamp'])
        deploy_time = parser.parse(latest_deployment['created_at'])
        
        time_diff = commit_time - deploy_time
        
        if time_diff.total_seconds() > 0:
            print(f"  ⚠️  Latest commit is {time_diff} NEWER than latest deployment")
            print(f"  🔔 Deployment may be lagging behind commits")
            return "deployment_lagging"
        else:
            print(f"  ✅ Latest deployment is recent (within commit timeline)")
            return "deployment_current"
            
    except Exception as e:
        print(f"  ❌ Could not parse timestamps for comparison: {e}")
        return "timestamp_error"


def main():
    """Main analysis function"""
    print("🚀 MarketEdge Render Deployment Analysis")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # 1. Test current production health
    print("🏥 Health Check")
    try:
        response = requests.get("https://marketedge-platform.onrender.com/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Status: {health.get('status')}")
            print(f"✅ Mode: {health.get('mode')}")
            print(f"✅ CORS: {health.get('cors_configured')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # 2. Analyze deployment timeline
    timeline_status = analyze_deployment_timeline()
    
    # 3. Test OAuth2 deployment
    oauth_status = test_oauth2_deployment()
    
    # 4. Final assessment
    print(f"\n🎯 Final Assessment")
    print("=" * 60)
    
    if timeline_status == "deployment_lagging":
        print("❌ DEPLOYMENT ISSUE: Latest commits not yet deployed")
        print("🔔 Render deployment appears to be hanging or slow")
        print("💡 Recommendation: Check Render dashboard for stuck deployments")
    elif oauth_status == "fix_not_deployed":
        print("❌ OAUTH2 ISSUE: Method name fix not deployed")
        print("🔔 OAuth2 500 errors will continue until deployment completes")
        print("💡 Recommendation: Wait for deployment or restart Render service")
    elif oauth_status == "fix_deployed":
        print("✅ SUCCESS: OAuth2 fixes appear to be deployed")
        print("✅ 500 errors should be resolved for valid authentication")
        print("💡 Remaining 500 errors likely due to Auth0 validation")
    else:
        print("⚠️  UNCLEAR: Deployment status cannot be determined")
        print("🔔 Manual investigation of Render logs recommended")
        print("💡 Recommendation: Check Render dashboard directly")
    
    return oauth_status == "fix_deployed"


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)