# Operational Dashboard Requirements

**Status**: Dashboard Architecture Specification
**Priority**: P1 - Critical for Operational Visibility
**Date**: 2025-09-24
**Dependencies**: Runtime Monitoring System, Alerting Strategy

## Overview

The Operational Dashboard provides comprehensive real-time visibility into system health, business impact, and operational metrics. It serves as the central command center for understanding system state, particularly focusing on business-critical components and revenue-impacting issues like the £925K Zebra Associates opportunity.

## Strategic Dashboard Philosophy

### 1. Business-First Information Architecture
- **Revenue Impact Prioritization**: Most critical business metrics prominently displayed
- **Stakeholder-Specific Views**: Different dashboards for technical teams vs business stakeholders
- **Context-Aware Alerting**: Visual indicators that convey business impact, not just technical status

### 2. Actionable Intelligence
- **Drill-Down Capability**: From business impact to technical root cause
- **Predictive Indicators**: Early warning systems before issues become critical
- **Recovery Tracking**: Progress toward SLA compliance and business objectives

### 3. Multi-Audience Design
- **Executive Summary**: High-level business impact and system health
- **Operations View**: Detailed system metrics and active incidents
- **Engineering View**: Technical debugging information and system internals

## Dashboard Architecture

### Information Hierarchy

```
Level 1: Business Impact Summary
├── Revenue at Risk Counter
├── Critical Business Opportunities Status
├── Customer Impact Assessment
└── Overall System Health Score

Level 2: System Health Overview
├── Critical Services Status
├── Active Incidents & Alerts
├── Performance Metrics
└── Security & Compliance Status

Level 3: Technical Details
├── Infrastructure Metrics
├── Application Performance
├── Database Health
└── Integration Status

Level 4: Historical Analysis
├── Incident Trends
├── Performance History
├── Business Impact Analysis
└── SLA Compliance Tracking
```

## Dashboard Components Specification

### 1. Executive Summary View

```python
class ExecutiveSummaryView:
    """High-level business-focused dashboard for executives"""

    components = {
        "revenue_risk_indicator": {
            "type": "metric_card",
            "title": "Revenue at Risk",
            "description": "Real-time calculation of revenue impact from system issues",
            "data_source": "alert_manager.calculate_total_revenue_at_risk()",
            "update_frequency": "30_seconds",
            "visual_style": {
                "size": "large",
                "color_scheme": "red_amber_green",
                "alert_threshold": "£50K",
                "critical_threshold": "£500K"
            },
            "business_context": "Immediate visibility into financial impact of technical issues",
            "drill_down": "detailed_incident_view"
        },

        "zebra_opportunity_status": {
            "type": "status_indicator",
            "title": "Zebra Associates Access Status",
            "description": "Real-time status of £925K cinema intelligence opportunity",
            "data_source": "monitoring_system.get_zebra_health_status()",
            "update_frequency": "15_seconds",
            "visual_style": {
                "size": "medium",
                "status_icons": {
                    "operational": "✅ OPERATIONAL",
                    "degraded": "⚠️ DEGRADED",
                    "failed": "🚨 FAILED"
                },
                "color_scheme": "status_based"
            },
            "business_context": "Critical visibility into highest-value customer opportunity",
            "drill_down": "zebra_detailed_view"
        },

        "customer_impact_summary": {
            "type": "summary_card",
            "title": "Customer Impact Assessment",
            "description": "Number of affected customers and service degradation",
            "data_source": "monitoring_system.get_customer_impact_summary()",
            "update_frequency": "60_seconds",
            "visual_style": {
                "layout": "horizontal_metrics",
                "metrics": ["affected_customers", "degraded_services", "avg_response_time"]
            },
            "business_context": "Customer experience and satisfaction impact"
        },

        "system_health_score": {
            "type": "gauge",
            "title": "Overall System Health",
            "description": "Composite health score based on all critical systems",
            "data_source": "monitoring_system.calculate_health_score()",
            "update_frequency": "30_seconds",
            "visual_style": {
                "gauge_type": "radial",
                "scale": "0_to_100",
                "color_ranges": [
                    {"min": 90, "max": 100, "color": "green", "label": "Excellent"},
                    {"min": 75, "max": 89, "color": "yellow", "label": "Good"},
                    {"min": 50, "max": 74, "color": "orange", "label": "Degraded"},
                    {"min": 0, "max": 49, "color": "red", "label": "Critical"}
                ]
            },
            "business_context": "Single metric summarizing entire platform health"
        },

        "incident_timeline": {
            "type": "timeline",
            "title": "Recent Incidents",
            "description": "Timeline of incidents and resolutions in last 24 hours",
            "data_source": "alert_manager.get_incident_timeline(hours=24)",
            "update_frequency": "60_seconds",
            "visual_style": {
                "timeline_type": "horizontal",
                "incident_colors": {
                    "resolved": "green",
                    "active": "red",
                    "investigating": "yellow"
                },
                "show_duration": True,
                "show_business_impact": True
            },
            "business_context": "Pattern recognition for incident frequency and impact"
        }
    }
```

### 2. Operations Dashboard View

```python
class OperationsDashboardView:
    """Detailed operational view for technical teams and operations staff"""

    components = {
        "active_alerts_panel": {
            "type": "alert_list",
            "title": "Active Alerts",
            "description": "All currently active alerts with business context",
            "data_source": "alert_manager.get_active_alerts()",
            "update_frequency": "10_seconds",
            "visual_style": {
                "layout": "card_list",
                "sort_by": "business_impact_severity",
                "show_fields": [
                    "alert_level", "component", "duration",
                    "business_impact", "recovery_sla", "escalation_status"
                ],
                "color_coding": "alert_level_based"
            },
            "interactions": {
                "click_to_acknowledge": True,
                "click_to_drill_down": True,
                "bulk_operations": ["acknowledge_all", "escalate_selected"]
            }
        },

        "critical_services_matrix": {
            "type": "service_matrix",
            "title": "Critical Services Health Matrix",
            "description": "Real-time status of all business-critical services",
            "data_source": "monitoring_system.get_critical_services_status()",
            "update_frequency": "15_seconds",
            "visual_style": {
                "layout": "grid",
                "services": [
                    "Authentication System",
                    "Zebra Admin Access",
                    "Database Connectivity",
                    "Feature Flag System",
                    "Multi-Tenant Isolation",
                    "Redis Session Storage",
                    "API Response Times",
                    "Critical Endpoints"
                ],
                "status_indicators": {
                    "healthy": {"color": "green", "icon": "✅"},
                    "degraded": {"color": "orange", "icon": "⚠️"},
                    "failed": {"color": "red", "icon": "🚨"},
                    "unknown": {"color": "gray", "icon": "❓"}
                }
            },
            "drill_down": "service_specific_metrics"
        },

        "performance_metrics_panel": {
            "type": "metrics_grid",
            "title": "Performance Metrics",
            "description": "Key performance indicators for system health",
            "data_source": "monitoring_system.get_performance_metrics()",
            "update_frequency": "30_seconds",
            "visual_style": {
                "layout": "metric_cards_grid",
                "metrics": [
                    {
                        "name": "API Response Time",
                        "unit": "ms",
                        "threshold_good": 500,
                        "threshold_warning": 2000,
                        "threshold_critical": 5000
                    },
                    {
                        "name": "Database Query Time",
                        "unit": "ms",
                        "threshold_good": 100,
                        "threshold_warning": 500,
                        "threshold_critical": 2000
                    },
                    {
                        "name": "Authentication Success Rate",
                        "unit": "%",
                        "threshold_good": 99.5,
                        "threshold_warning": 98.0,
                        "threshold_critical": 95.0
                    },
                    {
                        "name": "Active User Sessions",
                        "unit": "count",
                        "threshold_good": null,
                        "threshold_warning": null,
                        "threshold_critical": null
                    }
                ]
            }
        },

        "incident_management_panel": {
            "type": "incident_management",
            "title": "Incident Management",
            "description": "Active incident tracking and management",
            "data_source": "incident_manager.get_active_incidents()",
            "update_frequency": "30_seconds",
            "visual_style": {
                "layout": "kanban",
                "columns": ["New", "Investigating", "Resolving", "Monitoring"],
                "card_fields": [
                    "incident_id", "severity", "component", "business_impact",
                    "assigned_to", "duration", "next_update_due"
                ]
            },
            "interactions": {
                "drag_drop": True,
                "status_updates": True,
                "comment_system": True,
                "escalation_controls": True
            }
        },

        "zebra_detailed_monitoring": {
            "type": "specialized_panel",
            "title": "Zebra Associates Monitoring",
            "description": "Detailed monitoring specific to £925K opportunity",
            "data_source": "monitoring_system.get_zebra_detailed_metrics()",
            "update_frequency": "10_seconds",
            "visual_style": {
                "layout": "specialized_dashboard",
                "sections": [
                    {
                        "title": "Admin Panel Access",
                        "metrics": ["login_success_rate", "feature_flags_availability", "response_times"]
                    },
                    {
                        "title": "Cinema Intelligence Features",
                        "metrics": ["sic_59140_data_availability", "competitive_analysis_features", "dashboard_performance"]
                    },
                    {
                        "title": "Multi-Tenant Context",
                        "metrics": ["organization_switching", "data_isolation_validation", "permission_system"]
                    }
                ]
            },
            "business_context": "Specialized monitoring for highest-value customer opportunity"
        }
    }
```

### 3. Engineering/Technical View

```python
class EngineeringDashboardView:
    """Deep technical view for engineering teams and system debugging"""

    components = {
        "system_architecture_view": {
            "type": "architecture_diagram",
            "title": "System Architecture Health",
            "description": "Visual representation of system components and their health",
            "data_source": "monitoring_system.get_architecture_health()",
            "update_frequency": "60_seconds",
            "visual_style": {
                "diagram_type": "interactive_nodes",
                "components": [
                    {"name": "FastAPI Backend", "type": "application"},
                    {"name": "Next.js Frontend", "type": "frontend"},
                    {"name": "PostgreSQL Database", "type": "database"},
                    {"name": "Redis Cache", "type": "cache"},
                    {"name": "Auth0", "type": "external_service"},
                    {"name": "API Router", "type": "routing_layer"}
                ],
                "connections": "data_flow_based",
                "health_coloring": True,
                "click_for_details": True
            }
        },

        "import_validation_status": {
            "type": "code_health_panel",
            "title": "Import Validation Status",
            "description": "Real-time status of critical code imports and route registration",
            "data_source": "startup_validator.get_import_status()",
            "update_frequency": "60_seconds",
            "visual_style": {
                "layout": "hierarchical_tree",
                "modules": [
                    "app.api.api_v1.api",
                    "app.api.api_v1.endpoints.auth",
                    "app.api.api_v1.endpoints.admin",
                    "app.api.api_v1.endpoints.user_management",
                    "app.api.api_v1.endpoints.features"
                ],
                "status_indicators": {
                    "imported_successfully": "✅",
                    "import_error": "🚨",
                    "routes_registered": "📝",
                    "no_routes": "❌"
                }
            },
            "business_context": "Prevent the silent API router failure that caused the original issue"
        },

        "database_performance_panel": {
            "type": "database_metrics",
            "title": "Database Performance & Health",
            "description": "Detailed database metrics and query performance",
            "data_source": "monitoring_system.get_database_metrics()",
            "update_frequency": "30_seconds",
            "visual_style": {
                "layout": "tabbed_metrics",
                "tabs": [
                    {
                        "name": "Connection Pool",
                        "metrics": ["active_connections", "idle_connections", "connection_wait_time"]
                    },
                    {
                        "name": "Query Performance",
                        "metrics": ["avg_query_time", "slow_queries", "query_cache_hit_rate"]
                    },
                    {
                        "name": "RLS & Security",
                        "metrics": ["rls_policy_status", "tenant_isolation_tests", "permission_checks"]
                    }
                ]
            }
        },

        "error_tracking_panel": {
            "type": "error_dashboard",
            "title": "Error Tracking & Analysis",
            "description": "Real-time error tracking with business impact analysis",
            "data_source": "error_tracker.get_error_summary()",
            "update_frequency": "30_seconds",
            "visual_style": {
                "layout": "error_stream",
                "grouping": "by_component_and_impact",
                "fields": ["timestamp", "component", "error_type", "business_impact", "frequency"],
                "filtering": ["severity", "component", "time_range"],
                "trend_analysis": True
            }
        },

        "startup_validation_history": {
            "type": "validation_timeline",
            "title": "Startup Validation History",
            "description": "Historical view of startup validation results",
            "data_source": "startup_validator.get_validation_history()",
            "update_frequency": "300_seconds",
            "visual_style": {
                "layout": "timeline",
                "time_range": "last_7_days",
                "events": [
                    "successful_startups",
                    "degraded_startups",
                    "critical_failures",
                    "validation_errors"
                ],
                "trend_indicators": True,
                "failure_pattern_analysis": True
            },
            "business_context": "Track patterns that might predict future silent failures"
        }
    }
```

## Dashboard Data Architecture

### Real-Time Data Pipeline

```python
class DashboardDataManager:
    """Manages data flow and caching for dashboard components"""

    def __init__(self):
        self.data_cache = {}
        self.cache_expiry = {}
        self.update_frequencies = {}
        self.data_sources = {}

    async def initialize_data_sources(self):
        """Initialize connections to all monitoring systems"""
        self.data_sources = {
            "monitoring_system": RuntimeMonitor(),
            "alert_manager": AlertManager(),
            "startup_validator": StartupValidator(),
            "incident_manager": IncidentManager(),
            "error_tracker": ErrorTracker(),
            "business_metrics": BusinessMetricsCalculator()
        }

    async def get_dashboard_data(self, dashboard_type: str, component: str) -> Dict[str, Any]:
        """Get data for specific dashboard component with caching"""

        cache_key = f"{dashboard_type}_{component}"

        # Check if cached data is still valid
        if (cache_key in self.data_cache and
            cache_key in self.cache_expiry and
            datetime.utcnow() < self.cache_expiry[cache_key]):
            return self.data_cache[cache_key]

        # Fetch fresh data
        data = await self._fetch_component_data(dashboard_type, component)

        # Cache the data
        self.data_cache[cache_key] = data
        update_freq = self.update_frequencies.get(f"{dashboard_type}_{component}", 60)
        self.cache_expiry[cache_key] = datetime.utcnow() + timedelta(seconds=update_freq)

        return data

    async def _fetch_component_data(self, dashboard_type: str, component: str) -> Dict[str, Any]:
        """Fetch data for specific component"""

        try:
            if component == "revenue_risk_indicator":
                return await self._get_revenue_risk_data()
            elif component == "zebra_opportunity_status":
                return await self._get_zebra_status_data()
            elif component == "active_alerts_panel":
                return await self._get_active_alerts_data()
            elif component == "critical_services_matrix":
                return await self._get_services_matrix_data()
            elif component == "import_validation_status":
                return await self._get_import_validation_data()
            # ... more component handlers ...
            else:
                return {"error": f"Unknown component: {component}"}

        except Exception as e:
            logger.error(f"Failed to fetch data for {component}: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def _get_revenue_risk_data(self) -> Dict[str, Any]:
        """Calculate total revenue at risk from active alerts"""
        active_alerts = await self.data_sources["alert_manager"].get_active_alerts()

        total_risk = 0
        risk_breakdown = {}

        for alert in active_alerts:
            business_context = alert.get('business_context')
            if business_context == 'zebra_opportunity':
                risk_amount = 925000  # £925K
            elif business_context == 'revenue_critical':
                risk_amount = 925000  # Full platform revenue risk
            elif business_context == 'customer_experience':
                risk_amount = 100000  # Estimated customer churn impact
            else:
                risk_amount = 25000   # Default operational impact

            total_risk += risk_amount
            risk_breakdown[alert['component']] = risk_amount

        return {
            "total_risk_gbp": total_risk,
            "risk_breakdown": risk_breakdown,
            "highest_risk_component": max(risk_breakdown.items(), key=lambda x: x[1])[0] if risk_breakdown else None,
            "alert_count": len(active_alerts),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _get_zebra_status_data(self) -> Dict[str, Any]:
        """Get specific status for Zebra Associates opportunity"""
        zebra_health = await self.data_sources["monitoring_system"].get_zebra_health_status()

        status_mapping = {
            True: "operational",
            False: "failed",
            None: "degraded"
        }

        components_status = {
            "admin_access": zebra_health.get("admin_access_available", False),
            "feature_flags": zebra_health.get("feature_flags_working", False),
            "cinema_data": zebra_health.get("cinema_data_available", False),
            "multi_tenant": zebra_health.get("multi_tenant_working", False)
        }

        overall_status = "operational" if all(components_status.values()) else "degraded"
        if not any(components_status.values()):
            overall_status = "failed"

        return {
            "overall_status": overall_status,
            "components": components_status,
            "revenue_at_risk": "£925,000" if overall_status != "operational" else "£0",
            "last_successful_access": zebra_health.get("last_successful_access"),
            "response_time_ms": zebra_health.get("response_time_ms", 0),
            "timestamp": datetime.utcnow().isoformat()
        }

class BusinessMetricsCalculator:
    """Calculate business-focused metrics from technical data"""

    def __init__(self):
        self.metrics_cache = {}

    async def calculate_customer_impact(self, technical_failures: List[Dict]) -> Dict[str, Any]:
        """Calculate customer impact from technical failures"""

        impact_levels = {
            "auth_failure": {"customers": "all", "severity": "complete_block"},
            "admin_failure": {"customers": "admin_users", "severity": "feature_unavailable"},
            "database_failure": {"customers": "all", "severity": "complete_block"},
            "performance_degradation": {"customers": "all", "severity": "poor_experience"}
        }

        total_affected = 0
        severity_breakdown = {}

        for failure in technical_failures:
            failure_type = failure.get('type', 'unknown')
            if failure_type in impact_levels:
                impact = impact_levels[failure_type]
                if impact['customers'] == 'all':
                    total_affected = "all_users"
                    break
                elif impact['customers'] == 'admin_users':
                    total_affected += 50  # Estimated admin users

        return {
            "total_affected_customers": total_affected,
            "severity_breakdown": severity_breakdown,
            "customer_facing_issues": len([f for f in technical_failures if 'customer' in f.get('impact', '')]),
            "estimated_churn_risk": self._calculate_churn_risk(total_affected),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _calculate_churn_risk(self, affected_customers) -> Dict[str, Any]:
        """Calculate potential customer churn and revenue impact"""

        if affected_customers == "all_users":
            return {
                "churn_percentage_estimate": "10-25%",
                "revenue_risk_gbp": 925000,  # Full Zebra opportunity at risk
                "recovery_time_sensitivity": "high"
            }
        elif isinstance(affected_customers, int) and affected_customers > 0:
            return {
                "churn_percentage_estimate": "5-15%",
                "revenue_risk_gbp": min(100000, affected_customers * 2000),
                "recovery_time_sensitivity": "medium"
            }
        else:
            return {
                "churn_percentage_estimate": "0-5%",
                "revenue_risk_gbp": 10000,
                "recovery_time_sensitivity": "low"
            }
```

## Dashboard Implementation Architecture

### Technology Stack

```python
# Dashboard Technology Requirements

DASHBOARD_TECH_STACK = {
    "frontend": {
        "framework": "React + TypeScript",
        "charting": "Chart.js or D3.js",
        "real_time": "WebSocket connections",
        "state_management": "Redux Toolkit or Zustand",
        "ui_framework": "Material-UI or Ant Design"
    },

    "backend": {
        "api": "FastAPI endpoints",
        "real_time": "WebSocket support",
        "caching": "Redis for dashboard data",
        "data_aggregation": "Background tasks",
        "export": "PDF/CSV generation"
    },

    "deployment": {
        "hosting": "Vercel for frontend",
        "api": "Render backend integration",
        "monitoring": "Built into existing monitoring stack",
        "security": "Same Auth0 integration"
    }
}

# Dashboard Endpoints
@app.get("/api/v1/dashboard/executive-summary")
async def get_executive_summary():
    """Executive dashboard data"""
    pass

@app.get("/api/v1/dashboard/operations")
async def get_operations_dashboard():
    """Operations team dashboard data"""
    pass

@app.get("/api/v1/dashboard/engineering")
async def get_engineering_dashboard():
    """Engineering team dashboard data"""
    pass

@app.websocket("/api/v1/dashboard/realtime")
async def dashboard_websocket():
    """Real-time dashboard updates"""
    pass
```

## Success Metrics

### Dashboard Effectiveness Metrics

- **Mean Time to Detection (MTTD)**: <2 minutes for critical issues
- **Alert Accuracy**: >95% of alerts are actionable
- **Business Impact Awareness**: 100% of incidents have business impact calculated
- **Dashboard Load Time**: <3 seconds for all views
- **Data Freshness**: <30 seconds for critical metrics

### Business Value Metrics

- **Prevented Outages**: Track incidents caught early due to dashboard visibility
- **Faster Resolution**: Measure improvement in MTTR with dashboard usage
- **Stakeholder Satisfaction**: Regular feedback from executive and operations teams
- **Cost Avoidance**: Calculate prevented business impact through early detection

This dashboard architecture provides comprehensive visibility into the health and business impact of the MarketEdge platform, with particular focus on preventing the silent failure modes that could impact the £925K Zebra Associates opportunity.