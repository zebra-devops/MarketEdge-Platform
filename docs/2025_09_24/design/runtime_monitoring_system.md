# Runtime Monitoring System Architecture

**Status**: Technical Architecture Design
**Priority**: P0 - Continuous Protection Against Silent Failures
**Date**: 2025-09-24
**Dependencies**: Startup Validation Framework, Multi-Level Health Checks

## Overview

The Runtime Monitoring System provides continuous validation of critical system components during operation, ensuring that the silent failure modes detected during startup don't develop during runtime. This system monitors the health of API endpoints, business-critical paths, and infrastructure components with appropriate business context.

## Architectural Principles

### 1. Business-First Monitoring
- **Revenue Impact Assessment**: Every failure automatically calculates business impact
- **Customer Impact Tracking**: Real-time assessment of affected user segments
- **SLA Compliance**: Monitor against business service level agreements

### 2. Layered Defense Strategy
- **Critical Path Monitoring**: Continuous validation of revenue-generating endpoints
- **Infrastructure Monitoring**: Database, Redis, external service health
- **Business Logic Monitoring**: Feature flags, multi-tenant isolation, authentication
- **Performance Monitoring**: Response times, error rates, throughput

### 3. Intelligent Alerting
- **Context-Aware Alerts**: Different alert thresholds based on business impact
- **Escalation Patterns**: Automatic escalation based on severity and duration
- **Alert Fatigue Prevention**: Smart grouping and correlation

## Core Architecture

### Monitoring Component Hierarchy

```python
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
import time

class MonitoringLevel(Enum):
    CRITICAL = "critical"        # Revenue-impacting failures
    HIGH = "high"               # Business-impacting failures
    MEDIUM = "medium"           # Performance degradation
    LOW = "low"                 # Informational monitoring

class BusinessImpact(Enum):
    REVENUE_CRITICAL = "revenue_critical"      # £925K+ at risk
    CUSTOMER_CRITICAL = "customer_critical"    # Customer experience impact
    OPERATIONAL = "operational"                # Internal operations impact
    INFORMATIONAL = "informational"            # No immediate impact

@dataclass
class MonitoringTarget:
    name: str
    monitor_function: Callable
    monitoring_level: MonitoringLevel
    business_impact: BusinessImpact
    check_interval_seconds: int
    timeout_seconds: int
    failure_threshold: int  # Consecutive failures before alert
    success_threshold: int  # Consecutive successes to clear alert
    business_context: str
    alert_channels: List[str]
    recovery_actions: List[str]

@dataclass
class MonitoringResult:
    target: str
    success: bool
    response_time_ms: float
    error_message: Optional[str] = None
    business_impact_assessment: Optional[str] = None
    timestamp: datetime = None
    additional_context: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class RuntimeMonitor:
    """Comprehensive runtime monitoring system"""

    def __init__(self):
        self.monitoring_targets = self._initialize_monitoring_targets()
        self.monitoring_state = {}  # Track state for each target
        self.alert_manager = None  # Injected during initialization
        self.business_context_manager = None
        self.running = False

    def _initialize_monitoring_targets(self) -> Dict[str, MonitoringTarget]:
        """Initialize all monitoring targets with business context"""

        return {
            # CRITICAL: Authentication System - Complete Revenue Risk
            "auth_login_endpoint": MonitoringTarget(
                name="Authentication Login Endpoint",
                monitor_function=self._monitor_auth_login,
                monitoring_level=MonitoringLevel.CRITICAL,
                business_impact=BusinessImpact.REVENUE_CRITICAL,
                check_interval_seconds=30,
                timeout_seconds=5,
                failure_threshold=2,  # Alert after 2 failures (1 minute)
                success_threshold=3,  # Require 3 successes to clear
                business_context="Complete authentication failure - all revenue at immediate risk",
                alert_channels=["pagerduty", "slack_emergency", "email_immediate"],
                recovery_actions=["restart_auth_service", "failover_to_backup_auth", "enable_maintenance_mode"]
            ),

            # HIGH: Zebra Associates Admin Access - £925K Opportunity
            "zebra_admin_access": MonitoringTarget(
                name="Zebra Associates Admin Access",
                monitor_function=self._monitor_zebra_admin_access,
                monitoring_level=MonitoringLevel.HIGH,
                business_impact=BusinessImpact.REVENUE_CRITICAL,
                check_interval_seconds=60,
                timeout_seconds=10,
                failure_threshold=2,
                success_threshold=2,
                business_context="£925K Zebra Associates opportunity at risk - admin panel unavailable",
                alert_channels=["slack_zebra_channel", "email_matt_lindop", "slack_alerts"],
                recovery_actions=["restart_admin_service", "check_feature_flags", "validate_auth0_config"]
            ),

            # CRITICAL: Database Connectivity - Complete Data Access
            "database_connectivity": MonitoringTarget(
                name="Database Connectivity",
                monitor_function=self._monitor_database_connectivity,
                monitoring_level=MonitoringLevel.CRITICAL,
                business_impact=BusinessImpact.REVENUE_CRITICAL,
                check_interval_seconds=30,
                timeout_seconds=10,
                failure_threshold=3,  # Database might have brief hiccups
                success_threshold=2,
                business_context="Complete data access failure - all functionality unavailable",
                alert_channels=["pagerduty", "slack_emergency", "email_immediate"],
                recovery_actions=["check_database_server", "restart_connection_pool", "enable_readonly_mode"]
            ),

            # HIGH: Feature Flag System - Business Logic Control
            "feature_flag_system": MonitoringTarget(
                name="Feature Flag System",
                monitor_function=self._monitor_feature_flag_system,
                monitoring_level=MonitoringLevel.HIGH,
                business_impact=BusinessImpact.CUSTOMER_CRITICAL,
                check_interval_seconds=120,
                timeout_seconds=5,
                failure_threshold=2,
                success_threshold=2,
                business_context="Feature flag system failure - business logic control lost",
                alert_channels=["slack_alerts", "email_alerts"],
                recovery_actions=["use_default_flags", "restart_feature_service", "check_database_permissions"]
            ),

            # MEDIUM: Multi-Tenant Isolation - Data Security
            "tenant_isolation": MonitoringTarget(
                name="Multi-Tenant Data Isolation",
                monitor_function=self._monitor_tenant_isolation,
                monitoring_level=MonitoringLevel.HIGH,
                business_impact=BusinessImpact.CUSTOMER_CRITICAL,
                check_interval_seconds=300,  # 5 minutes - expensive check
                timeout_seconds=15,
                failure_threshold=1,  # Zero tolerance for data leakage
                success_threshold=3,
                business_context="Data isolation failure - potential customer data breach",
                alert_channels=["pagerduty", "slack_security", "email_security_team"],
                recovery_actions=["enable_maintenance_mode", "audit_data_access", "restart_with_rls_check"]
            ),

            # MEDIUM: Redis Session Storage - User Experience
            "redis_session_storage": MonitoringTarget(
                name="Redis Session Storage",
                monitor_function=self._monitor_redis_sessions,
                monitoring_level=MonitoringLevel.MEDIUM,
                business_impact=BusinessImpact.CUSTOMER_CRITICAL,
                check_interval_seconds=60,
                timeout_seconds=5,
                failure_threshold=3,
                success_threshold=2,
                business_context="Session storage failure - users forced to re-authenticate",
                alert_channels=["slack_alerts", "email_alerts"],
                recovery_actions=["restart_redis_service", "clear_session_cache", "use_database_sessions"]
            ),

            # HIGH: API Response Times - Customer Experience
            "api_response_times": MonitoringTarget(
                name="API Response Time Performance",
                monitor_function=self._monitor_api_response_times,
                monitoring_level=MonitoringLevel.MEDIUM,
                business_impact=BusinessImpact.CUSTOMER_CRITICAL,
                check_interval_seconds=60,
                timeout_seconds=30,
                failure_threshold=5,  # Allow some variation
                success_threshold=3,
                business_context="API performance degradation - customer experience impacted",
                alert_channels=["slack_alerts", "email_alerts"],
                recovery_actions=["scale_up_instances", "optimize_queries", "enable_caching"]
            ),

            # CRITICAL: Business-Critical Endpoints Availability
            "critical_endpoints_availability": MonitoringTarget(
                name="Critical Business Endpoints",
                monitor_function=self._monitor_critical_endpoints,
                monitoring_level=MonitoringLevel.CRITICAL,
                business_impact=BusinessImpact.REVENUE_CRITICAL,
                check_interval_seconds=45,
                timeout_seconds=10,
                failure_threshold=2,
                success_threshold=2,
                business_context="Critical business endpoints unavailable - revenue generation blocked",
                alert_channels=["pagerduty", "slack_emergency", "email_immediate"],
                recovery_actions=["restart_api_service", "check_route_registration", "validate_imports"]
            )
        }

    async def start_monitoring(self):
        """Start all monitoring tasks"""
        if self.running:
            logger.warning("Runtime monitoring already running")
            return

        self.running = True
        logger.info("🔍 Starting runtime monitoring system...")

        # Initialize monitoring state for all targets
        for target_name in self.monitoring_targets.keys():
            self.monitoring_state[target_name] = {
                'consecutive_failures': 0,
                'consecutive_successes': 0,
                'last_success': None,
                'last_failure': None,
                'alert_active': False,
                'last_check': None,
                'total_checks': 0,
                'success_rate': 1.0
            }

        # Start monitoring tasks for each target
        monitoring_tasks = []
        for target_name, target in self.monitoring_targets.items():
            task = asyncio.create_task(
                self._monitoring_loop(target_name, target),
                name=f"monitor_{target_name}"
            )
            monitoring_tasks.append(task)

        logger.info(f"✅ Started {len(monitoring_tasks)} monitoring tasks")

        # Monitor the monitoring tasks themselves
        asyncio.create_task(self._monitor_monitoring_tasks(monitoring_tasks))

    async def _monitoring_loop(self, target_name: str, target: MonitoringTarget):
        """Individual monitoring loop for a target"""
        logger.info(f"🔍 Starting monitoring loop for {target_name}")

        while self.running:
            try:
                # Perform the monitoring check
                start_time = time.time()
                result = await asyncio.wait_for(
                    target.monitor_function(),
                    timeout=target.timeout_seconds
                )
                result.target = target_name

                # Update monitoring state
                await self._update_monitoring_state(target_name, target, result)

                # Wait for next check
                await asyncio.sleep(target.check_interval_seconds)

            except asyncio.TimeoutError:
                # Handle timeout as a failure
                timeout_result = MonitoringResult(
                    target=target_name,
                    success=False,
                    response_time_ms=target.timeout_seconds * 1000,
                    error_message=f"Monitoring check timed out after {target.timeout_seconds}s",
                    business_impact_assessment=f"Timeout indicates severe performance degradation: {target.business_context}"
                )
                await self._update_monitoring_state(target_name, target, timeout_result)
                await asyncio.sleep(target.check_interval_seconds)

            except Exception as e:
                logger.error(f"Error in monitoring loop for {target_name}: {e}")
                # Create error result
                error_result = MonitoringResult(
                    target=target_name,
                    success=False,
                    response_time_ms=0,
                    error_message=f"Monitoring system error: {str(e)}",
                    business_impact_assessment=f"Monitoring system failure: {target.business_context}"
                )
                await self._update_monitoring_state(target_name, target, error_result)
                await asyncio.sleep(min(target.check_interval_seconds, 60))

    async def _update_monitoring_state(self, target_name: str, target: MonitoringTarget, result: MonitoringResult):
        """Update monitoring state and trigger alerts if needed"""
        state = self.monitoring_state[target_name]
        state['last_check'] = datetime.utcnow()
        state['total_checks'] += 1

        if result.success:
            state['consecutive_failures'] = 0
            state['consecutive_successes'] += 1
            state['last_success'] = result.timestamp

            # Clear alert if we have enough consecutive successes
            if (state['alert_active'] and
                state['consecutive_successes'] >= target.success_threshold):
                await self._clear_alert(target_name, target, result)

        else:
            state['consecutive_successes'] = 0
            state['consecutive_failures'] += 1
            state['last_failure'] = result.timestamp

            # Trigger alert if we have enough consecutive failures
            if (not state['alert_active'] and
                state['consecutive_failures'] >= target.failure_threshold):
                await self._trigger_alert(target_name, target, result)

        # Update success rate (last 100 checks)
        if state['total_checks'] > 0:
            # Simplified success rate calculation
            recent_successes = max(0, state['consecutive_successes'])
            recent_total = min(state['total_checks'], 100)
            state['success_rate'] = recent_successes / recent_total if recent_total > 0 else 0

        # Log result based on importance
        if result.success:
            if state['consecutive_failures'] > 0:
                logger.info(f"✅ {target_name}: Recovered after {state['consecutive_failures']} failures")
        else:
            if target.monitoring_level == MonitoringLevel.CRITICAL:
                logger.error(f"🚨 {target_name}: {result.error_message} (failure #{state['consecutive_failures']})")
            else:
                logger.warning(f"⚠️ {target_name}: {result.error_message} (failure #{state['consecutive_failures']})")

    # Individual Monitoring Functions

    async def _monitor_auth_login(self) -> MonitoringResult:
        """Monitor authentication login endpoint availability"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                start_time = time.time()

                # Test login endpoint with invalid credentials (should return 401, not 500/404)
                response = await client.post(
                    "http://localhost:8000/api/v1/auth/login",
                    json={"email": "health@monitor.test", "password": "invalid"},
                    timeout=5.0
                )

                response_time = (time.time() - start_time) * 1000

                # Success if we get 400/401 (endpoint exists and processes requests)
                # Failure if we get 404/500 (endpoint missing or broken)
                success = response.status_code in [400, 401, 422]  # Expected auth errors

                if success:
                    return MonitoringResult(
                        target="auth_login",
                        success=True,
                        response_time_ms=response_time,
                        business_impact_assessment="Authentication system operational"
                    )
                else:
                    return MonitoringResult(
                        target="auth_login",
                        success=False,
                        response_time_ms=response_time,
                        error_message=f"Unexpected status code: {response.status_code}",
                        business_impact_assessment="Authentication endpoint not responding correctly - all user access blocked"
                    )

        except httpx.ConnectError:
            return MonitoringResult(
                target="auth_login",
                success=False,
                response_time_ms=5000,
                error_message="Cannot connect to API server",
                business_impact_assessment="Complete API server failure - all revenue at risk"
            )
        except Exception as e:
            return MonitoringResult(
                target="auth_login",
                success=False,
                response_time_ms=0,
                error_message=f"Auth monitoring error: {str(e)}",
                business_impact_assessment="Unable to validate authentication system"
            )

    async def _monitor_zebra_admin_access(self) -> MonitoringResult:
        """Monitor Zebra Associates admin access specifically"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                start_time = time.time()

                # Test admin feature flags endpoint (core admin functionality)
                response = await client.get(
                    "http://localhost:8000/api/v1/admin/feature-flags",
                    headers={"Authorization": "Bearer health_check_token"},
                    timeout=10.0
                )

                response_time = (time.time() - start_time) * 1000

                # Success if we get 401/403 (endpoint exists, authentication required)
                # Failure if we get 404/500 (endpoint missing or broken)
                success = response.status_code in [200, 401, 403]

                if success:
                    return MonitoringResult(
                        target="zebra_admin_access",
                        success=True,
                        response_time_ms=response_time,
                        business_impact_assessment="Admin functionality available for £925K opportunity"
                    )
                else:
                    return MonitoringResult(
                        target="zebra_admin_access",
                        success=False,
                        response_time_ms=response_time,
                        error_message=f"Admin endpoint failed with status {response.status_code}",
                        business_impact_assessment="£925K Zebra Associates opportunity at risk - admin panel unavailable"
                    )

        except Exception as e:
            return MonitoringResult(
                target="zebra_admin_access",
                success=False,
                response_time_ms=10000,
                error_message=f"Zebra admin monitoring error: {str(e)}",
                business_impact_assessment="£925K Zebra Associates opportunity at risk - cannot validate admin access"
            )

    async def _monitor_database_connectivity(self) -> MonitoringResult:
        """Monitor database connectivity and basic operations"""
        try:
            from app.core.database import get_async_db

            start_time = time.time()
            async for db in get_async_db():
                # Test basic database operation
                result = await db.execute("SELECT 1 as health_check, NOW() as timestamp")
                await db.commit()
                response_time = (time.time() - start_time) * 1000

                return MonitoringResult(
                    target="database_connectivity",
                    success=True,
                    response_time_ms=response_time,
                    business_impact_assessment="Database fully operational"
                )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 10000
            return MonitoringResult(
                target="database_connectivity",
                success=False,
                response_time_ms=response_time,
                error_message=f"Database connectivity error: {str(e)}",
                business_impact_assessment="Complete data access failure - all functionality unavailable"
            )

    async def _monitor_feature_flag_system(self) -> MonitoringResult:
        """Monitor feature flag system functionality"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                start_time = time.time()

                # Test feature flags endpoint
                response = await client.get(
                    "http://localhost:8000/api/v1/features",
                    timeout=5.0
                )

                response_time = (time.time() - start_time) * 1000
                success = response.status_code in [200, 401, 403]

                if success:
                    return MonitoringResult(
                        target="feature_flag_system",
                        success=True,
                        response_time_ms=response_time,
                        business_impact_assessment="Feature flag system operational"
                    )
                else:
                    return MonitoringResult(
                        target="feature_flag_system",
                        success=False,
                        response_time_ms=response_time,
                        error_message=f"Feature flags endpoint returned {response.status_code}",
                        business_impact_assessment="Feature flag system failure - business logic control compromised"
                    )

        except Exception as e:
            return MonitoringResult(
                target="feature_flag_system",
                success=False,
                response_time_ms=5000,
                error_message=f"Feature flag monitoring error: {str(e)}",
                business_impact_assessment="Cannot validate feature flag system"
            )

    async def _monitor_tenant_isolation(self) -> MonitoringResult:
        """Monitor multi-tenant data isolation"""
        try:
            # This is a more expensive check, so we do it less frequently
            from app.core.database import get_async_db

            start_time = time.time()
            async for db in get_async_db():
                # Check that RLS is enabled
                rls_check = await db.execute("SHOW row_security")
                result = await db.fetchone()

                response_time = (time.time() - start_time) * 1000

                if result and result[0] == 'on':
                    return MonitoringResult(
                        target="tenant_isolation",
                        success=True,
                        response_time_ms=response_time,
                        business_impact_assessment="Multi-tenant isolation secure"
                    )
                else:
                    return MonitoringResult(
                        target="tenant_isolation",
                        success=False,
                        response_time_ms=response_time,
                        error_message="Row Level Security not enabled",
                        business_impact_assessment="CRITICAL: Data isolation failure - potential customer data breach"
                    )

        except Exception as e:
            return MonitoringResult(
                target="tenant_isolation",
                success=False,
                response_time_ms=15000,
                error_message=f"Tenant isolation check error: {str(e)}",
                business_impact_assessment="Cannot validate data isolation - potential security risk"
            )

    async def _monitor_redis_sessions(self) -> MonitoringResult:
        """Monitor Redis session storage"""
        try:
            from app.core.redis_manager import redis_manager

            start_time = time.time()
            await redis_manager.health_check()
            response_time = (time.time() - start_time) * 1000

            return MonitoringResult(
                target="redis_session_storage",
                success=True,
                response_time_ms=response_time,
                business_impact_assessment="Session storage operational"
            )

        except Exception as e:
            return MonitoringResult(
                target="redis_session_storage",
                success=False,
                response_time_ms=5000,
                error_message=f"Redis session error: {str(e)}",
                business_impact_assessment="Session storage failure - users may experience re-authentication"
            )

    async def _monitor_api_response_times(self) -> MonitoringResult:
        """Monitor API response time performance"""
        try:
            import httpx

            # Test multiple endpoints and calculate average response time
            endpoints_to_test = [
                "/health",
                "/api/v1/auth/login",  # Expect 422/401
                "/api/v1/users",       # Expect 401/403
            ]

            total_time = 0
            successful_tests = 0

            async with httpx.AsyncClient() as client:
                for endpoint in endpoints_to_test:
                    try:
                        start_time = time.time()
                        await client.get(f"http://localhost:8000{endpoint}", timeout=30.0)
                        endpoint_time = (time.time() - start_time) * 1000
                        total_time += endpoint_time
                        successful_tests += 1
                    except Exception:
                        continue

            if successful_tests > 0:
                avg_response_time = total_time / successful_tests
                # Consider slow if average response time > 5 seconds
                success = avg_response_time < 5000

                return MonitoringResult(
                    target="api_response_times",
                    success=success,
                    response_time_ms=avg_response_time,
                    business_impact_assessment="API performance acceptable" if success else "API performance degraded - customer experience impacted",
                    additional_context={"endpoints_tested": successful_tests, "avg_response_time": avg_response_time}
                )
            else:
                return MonitoringResult(
                    target="api_response_times",
                    success=False,
                    response_time_ms=30000,
                    error_message="No endpoints responding",
                    business_impact_assessment="Complete API failure - all endpoints unresponsive"
                )

        except Exception as e:
            return MonitoringResult(
                target="api_response_times",
                success=False,
                response_time_ms=0,
                error_message=f"Response time monitoring error: {str(e)}",
                business_impact_assessment="Cannot validate API performance"
            )

    async def _monitor_critical_endpoints(self) -> MonitoringResult:
        """Monitor availability of critical business endpoints"""
        try:
            import httpx

            # Critical endpoints that must be available
            critical_endpoints = [
                ("/api/v1/auth/login", [400, 401, 422]),
                ("/api/v1/users", [401, 403, 200]),
                ("/api/v1/admin/feature-flags", [401, 403, 200]),
                ("/api/v1/organisations", [401, 403, 200])
            ]

            failed_endpoints = []
            total_response_time = 0

            async with httpx.AsyncClient() as client:
                for endpoint, expected_codes in critical_endpoints:
                    try:
                        start_time = time.time()
                        response = await client.get(f"http://localhost:8000{endpoint}", timeout=10.0)
                        endpoint_time = (time.time() - start_time) * 1000
                        total_response_time += endpoint_time

                        if response.status_code not in expected_codes:
                            failed_endpoints.append(f"{endpoint} (got {response.status_code})")

                    except Exception as e:
                        failed_endpoints.append(f"{endpoint} (error: {str(e)})")

            success = len(failed_endpoints) == 0

            if success:
                return MonitoringResult(
                    target="critical_endpoints_availability",
                    success=True,
                    response_time_ms=total_response_time,
                    business_impact_assessment="All critical endpoints operational"
                )
            else:
                return MonitoringResult(
                    target="critical_endpoints_availability",
                    success=False,
                    response_time_ms=total_response_time,
                    error_message=f"Failed endpoints: {', '.join(failed_endpoints)}",
                    business_impact_assessment="Critical business endpoints unavailable - revenue generation blocked"
                )

        except Exception as e:
            return MonitoringResult(
                target="critical_endpoints_availability",
                success=False,
                response_time_ms=0,
                error_message=f"Critical endpoint monitoring error: {str(e)}",
                business_impact_assessment="Cannot validate critical endpoint availability"
            )

    async def _trigger_alert(self, target_name: str, target: MonitoringTarget, result: MonitoringResult):
        """Trigger alert for monitoring failure"""
        self.monitoring_state[target_name]['alert_active'] = True

        logger.error(f"🚨 ALERT TRIGGERED: {target_name}")

        # Send to alert manager if available
        if self.alert_manager:
            await self.alert_manager.send_monitoring_alert(target, result)

    async def _clear_alert(self, target_name: str, target: MonitoringTarget, result: MonitoringResult):
        """Clear alert for monitoring recovery"""
        self.monitoring_state[target_name]['alert_active'] = False

        logger.info(f"✅ ALERT CLEARED: {target_name}")

        # Send recovery notification
        if self.alert_manager:
            await self.alert_manager.send_recovery_notification(target, result)

    async def stop_monitoring(self):
        """Stop all monitoring tasks"""
        self.running = False
        logger.info("🔍 Stopping runtime monitoring system...")

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status for health checks"""
        return {
            "monitoring_active": self.running,
            "total_targets": len(self.monitoring_targets),
            "targets_status": {
                name: {
                    "last_check": state.get('last_check'),
                    "success_rate": state.get('success_rate', 0),
                    "alert_active": state.get('alert_active', False),
                    "consecutive_failures": state.get('consecutive_failures', 0)
                } for name, state in self.monitoring_state.items()
            },
            "business_impact_summary": self._calculate_business_impact_summary()
        }

    def _calculate_business_impact_summary(self) -> str:
        """Calculate overall business impact from monitoring state"""
        active_critical_alerts = 0
        active_high_alerts = 0

        for target_name, state in self.monitoring_state.items():
            if state.get('alert_active', False):
                target = self.monitoring_targets[target_name]
                if target.monitoring_level == MonitoringLevel.CRITICAL:
                    active_critical_alerts += 1
                elif target.monitoring_level == MonitoringLevel.HIGH:
                    active_high_alerts += 1

        if active_critical_alerts > 0:
            return f"CRITICAL: {active_critical_alerts} critical systems failing - immediate revenue impact"
        elif active_high_alerts > 0:
            return f"HIGH: {active_high_alerts} high-impact systems degraded - £925K opportunity at risk"
        else:
            return "OPERATIONAL: All critical systems healthy"

    async def _monitor_monitoring_tasks(self, tasks: List[asyncio.Task]):
        """Monitor the monitoring tasks themselves"""
        while self.running:
            try:
                # Check if any monitoring tasks have failed
                failed_tasks = [task for task in tasks if task.done() and not task.cancelled()]

                if failed_tasks:
                    logger.error(f"🚨 MONITORING SYSTEM FAILURE: {len(failed_tasks)} monitoring tasks failed")
                    for task in failed_tasks:
                        logger.error(f"   Failed task: {task.get_name()} - {task.exception()}")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error monitoring monitoring tasks: {e}")
                await asyncio.sleep(60)
```

## Integration with Main Application

### FastAPI Integration Pattern

```python
# app/main.py integration
from app.monitoring.runtime_monitor import RuntimeMonitor

@app.on_event("startup")
async def startup_with_runtime_monitoring():
    """Enhanced startup with runtime monitoring"""

    # ... existing startup logic ...

    # Initialize and start runtime monitoring
    runtime_monitor = RuntimeMonitor()
    app.state.runtime_monitor = runtime_monitor

    # Start monitoring in background
    await runtime_monitor.start_monitoring()

    logger.info("✅ Runtime monitoring system active")

@app.on_event("shutdown")
async def shutdown_with_monitoring():
    """Enhanced shutdown with monitoring cleanup"""

    if hasattr(app.state, 'runtime_monitor'):
        await app.state.runtime_monitor.stop_monitoring()

    logger.info("Runtime monitoring system stopped")

# Runtime monitoring status endpoint
@app.get("/health/runtime-monitoring")
async def runtime_monitoring_health():
    """Expose runtime monitoring status"""

    if hasattr(app.state, 'runtime_monitor'):
        return app.state.runtime_monitor.get_monitoring_status()
    else:
        return {
            "monitoring_active": False,
            "error": "Runtime monitoring not initialized"
        }
```

This runtime monitoring system provides continuous protection against the silent failure modes while maintaining business context and appropriate alerting thresholds for the multi-tenant platform.