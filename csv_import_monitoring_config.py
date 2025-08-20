#!/usr/bin/env python3
"""
CSV Import Monitoring Configuration
Sets up monitoring, alerts, and dashboards for the CSV import feature
"""

import json
from typing import Dict, List, Any
from datetime import datetime, timedelta

class CSVImportMonitoringConfig:
    """Configuration for monitoring CSV import functionality"""
    
    # Alert thresholds
    ALERT_THRESHOLDS = {
        "import_failure_rate": 0.10,  # 10% failure rate
        "processing_time_per_user": 30,  # 30 seconds per user
        "rate_limit_violations": 20,  # 20 violations per hour
        "background_task_failures": 5,  # 5 task failures per hour
        "file_upload_errors": 0.15,  # 15% upload error rate
    }
    
    # Key metrics to track
    METRICS = {
        "csv_imports_total": {
            "type": "counter",
            "description": "Total number of CSV import attempts",
            "labels": ["organization_id", "status", "user_id"]
        },
        "csv_import_duration_seconds": {
            "type": "histogram",
            "description": "Time taken to process CSV imports",
            "labels": ["organization_id", "file_size_category"],
            "buckets": [1, 5, 10, 30, 60, 300, 900]  # seconds
        },
        "csv_import_users_processed": {
            "type": "histogram", 
            "description": "Number of users processed per import",
            "labels": ["organization_id", "status"],
            "buckets": [1, 10, 50, 100, 500, 1000, 5000]
        },
        "csv_upload_errors_total": {
            "type": "counter",
            "description": "File upload errors by type",
            "labels": ["error_type", "organization_id"]
        },
        "csv_rate_limit_violations_total": {
            "type": "counter",
            "description": "Rate limit violations for CSV imports",
            "labels": ["user_id", "limit_type"]
        },
        "csv_background_task_failures_total": {
            "type": "counter", 
            "description": "Background task processing failures",
            "labels": ["error_type", "organization_id"]
        }
    }
    
    @staticmethod
    def get_prometheus_config() -> Dict[str, Any]:
        """Generate Prometheus monitoring configuration"""
        return {
            "rule_groups": [
                {
                    "name": "csv_import_alerts",
                    "rules": [
                        {
                            "alert": "CSVImportHighFailureRate",
                            "expr": f"rate(csv_imports_total{{status='failed'}}[5m]) / rate(csv_imports_total[5m]) > {CSVImportMonitoringConfig.ALERT_THRESHOLDS['import_failure_rate']}",
                            "for": "5m",
                            "labels": {
                                "severity": "critical",
                                "service": "csv_import"
                            },
                            "annotations": {
                                "summary": "High CSV import failure rate detected",
                                "description": "CSV import failure rate is above {{ $value }}% for 5 minutes"
                            }
                        },
                        {
                            "alert": "CSVImportSlowProcessing", 
                            "expr": f"avg(csv_import_duration_seconds / csv_import_users_processed) > {CSVImportMonitoringConfig.ALERT_THRESHOLDS['processing_time_per_user']}",
                            "for": "10m",
                            "labels": {
                                "severity": "warning",
                                "service": "csv_import"
                            },
                            "annotations": {
                                "summary": "CSV import processing is slow",
                                "description": "Average processing time per user is {{ $value }} seconds"
                            }
                        },
                        {
                            "alert": "CSVRateLimitViolations",
                            "expr": f"rate(csv_rate_limit_violations_total[1h]) > {CSVImportMonitoringConfig.ALERT_THRESHOLDS['rate_limit_violations']}",
                            "for": "5m", 
                            "labels": {
                                "severity": "warning",
                                "service": "csv_import"
                            },
                            "annotations": {
                                "summary": "High rate of CSV import rate limit violations",
                                "description": "Rate limit violations occurring at {{ $value }} per hour"
                            }
                        },
                        {
                            "alert": "CSVBackgroundTaskFailures",
                            "expr": f"rate(csv_background_task_failures_total[1h]) > {CSVImportMonitoringConfig.ALERT_THRESHOLDS['background_task_failures']}",
                            "for": "10m",
                            "labels": {
                                "severity": "critical", 
                                "service": "csv_import"
                            },
                            "annotations": {
                                "summary": "CSV background task failures detected",
                                "description": "Background task failures at {{ $value }} per hour"
                            }
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def get_grafana_dashboard() -> Dict[str, Any]:
        """Generate Grafana dashboard configuration for CSV imports"""
        return {
            "dashboard": {
                "id": None,
                "title": "CSV Import Monitoring Dashboard",
                "description": "Monitor CSV user import functionality and performance",
                "tags": ["csv", "import", "users", "admin"],
                "timezone": "UTC",
                "refresh": "30s",
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "panels": [
                    {
                        "id": 1,
                        "title": "Import Success Rate",
                        "type": "singlestat",
                        "targets": [
                            {
                                "expr": "rate(csv_imports_total{status='completed'}[5m]) / rate(csv_imports_total[5m]) * 100",
                                "legendFormat": "Success Rate %"
                            }
                        ],
                        "thresholds": "80,95",
                        "colorBackground": True,
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Active Imports",
                        "type": "singlestat",
                        "targets": [
                            {
                                "expr": "sum(csv_imports_total{status='processing'})",
                                "legendFormat": "Processing"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Import Volume Over Time",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(csv_imports_total[5m])",
                                "legendFormat": "Imports per second"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                    },
                    {
                        "id": 4,
                        "title": "Processing Time Distribution",
                        "type": "heatmap",
                        "targets": [
                            {
                                "expr": "csv_import_duration_seconds_bucket",
                                "legendFormat": "Processing Time"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
                    },
                    {
                        "id": 5,
                        "title": "Error Breakdown",
                        "type": "piechart",
                        "targets": [
                            {
                                "expr": "sum by (error_type) (csv_upload_errors_total)",
                                "legendFormat": "{{error_type}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
                    },
                    {
                        "id": 6,
                        "title": "Rate Limit Violations",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(csv_rate_limit_violations_total[5m])",
                                "legendFormat": "{{user_id}} - {{limit_type}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 24}
                    }
                ]
            }
        }
    
    @staticmethod
    def get_logging_config() -> Dict[str, Any]:
        """Get structured logging configuration for CSV imports"""
        return {
            "loggers": {
                "csv_import": {
                    "level": "INFO",
                    "handlers": ["console", "file"],
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "structured_logs": {
                "csv_import_started": {
                    "level": "INFO",
                    "fields": [
                        "timestamp", "user_id", "organization_id", 
                        "filename", "file_size", "total_rows", "batch_id"
                    ]
                },
                "csv_import_completed": {
                    "level": "INFO", 
                    "fields": [
                        "timestamp", "batch_id", "total_rows", "successful_rows",
                        "failed_rows", "processing_time", "status"
                    ]
                },
                "csv_import_error": {
                    "level": "ERROR",
                    "fields": [
                        "timestamp", "batch_id", "error_type", "error_message",
                        "user_id", "organization_id", "row_number"
                    ]
                },
                "csv_rate_limit_hit": {
                    "level": "WARNING",
                    "fields": [
                        "timestamp", "user_id", "limit_type", "current_count",
                        "limit_value", "retry_after"
                    ]
                }
            }
        }
    
    @staticmethod  
    def get_health_checks() -> List[Dict[str, Any]]:
        """Define health checks for CSV import functionality"""
        return [
            {
                "name": "csv_import_endpoint_health",
                "endpoint": "/api/v1/organizations/health-check/users/import/template",
                "method": "GET",
                "expected_status": [200, 403],  # 403 is OK if not authenticated
                "timeout": 10,
                "interval": 60
            },
            {
                "name": "csv_redis_connection",
                "check_type": "redis_ping",
                "description": "Verify Redis connectivity for rate limiting",
                "interval": 30
            },
            {
                "name": "csv_database_tables",
                "check_type": "database_query",
                "query": "SELECT COUNT(*) FROM import_batches WHERE created_at > NOW() - INTERVAL '1 hour'",
                "description": "Verify import tables are accessible",
                "interval": 300
            },
            {
                "name": "csv_background_tasks",
                "check_type": "custom",
                "description": "Check background task processing health",
                "script": "check_background_task_queue.py",
                "interval": 120
            }
        ]

def generate_monitoring_files():
    """Generate all monitoring configuration files"""
    config = CSVImportMonitoringConfig()
    
    # Generate Prometheus rules
    with open('csv_import_prometheus_rules.yml', 'w') as f:
        json.dump(config.get_prometheus_config(), f, indent=2)
    
    # Generate Grafana dashboard
    with open('csv_import_grafana_dashboard.json', 'w') as f:
        json.dump(config.get_grafana_dashboard(), f, indent=2)
    
    # Generate logging config
    with open('csv_import_logging.json', 'w') as f:
        json.dump(config.get_logging_config(), f, indent=2)
    
    # Generate health checks
    with open('csv_import_health_checks.json', 'w') as f:
        json.dump({"health_checks": config.get_health_checks()}, f, indent=2)
    
    print("✅ Generated monitoring configuration files:")
    print("   - csv_import_prometheus_rules.yml")
    print("   - csv_import_grafana_dashboard.json") 
    print("   - csv_import_logging.json")
    print("   - csv_import_health_checks.json")

if __name__ == "__main__":
    generate_monitoring_files()