# Alerting Strategy and Integration Architecture

**Status**: Strategic Alert Architecture Design
**Priority**: P0 - Critical for Business Impact Prevention
**Date**: 2025-09-24
**Dependencies**: Runtime Monitoring System, Startup Validation Framework

## Overview

The Alerting Strategy provides intelligent, context-aware notifications that prevent alert fatigue while ensuring critical business impacts receive immediate attention. This system integrates with multiple channels and provides escalation patterns based on business context, particularly focusing on the £925K Zebra Associates opportunity.

## Strategic Alert Philosophy

### 1. Business-First Alerting
- **Revenue Impact Priority**: Alerts prioritized by potential revenue loss
- **Customer Impact Assessment**: Different alert patterns for customer-facing vs internal issues
- **Opportunity Risk**: Special handling for high-value business opportunities

### 2. Intelligent Alert Management
- **Context-Aware Severity**: Same technical failure gets different alert levels based on business context
- **Escalation Automation**: Automatic escalation based on response time and impact
- **Alert Correlation**: Group related failures to prevent notification storms

### 3. Multi-Channel Integration
- **Channel Selection by Impact**: Critical revenue issues go to immediate channels
- **Stakeholder-Specific Routing**: Business stakeholders get business-focused alerts
- **Integration Redundancy**: Multiple channels for critical alerts

## Alert Classification System

### Alert Levels with Business Context

```python
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

class AlertLevel(Enum):
    EMERGENCY = "emergency"        # P0 - Complete service failure, immediate revenue loss
    CRITICAL = "critical"          # P1 - Major functionality failure, significant revenue impact
    HIGH = "high"                  # P2 - Important functionality degraded, business opportunity risk
    MEDIUM = "medium"              # P3 - Performance issues, customer experience impact
    LOW = "low"                    # P4 - Minor issues, informational
    INFO = "info"                  # P5 - Status updates, successful recoveries

class BusinessContext(Enum):
    REVENUE_CRITICAL = "revenue_critical"      # Direct revenue generation impact
    ZEBRA_OPPORTUNITY = "zebra_opportunity"    # £925K specific opportunity
    CUSTOMER_EXPERIENCE = "customer_experience" # User-facing functionality
    OPERATIONAL = "operational"                # Internal systems, monitoring
    SECURITY = "security"                      # Data protection, compliance
    PERFORMANCE = "performance"                # System performance, scaling

@dataclass
class AlertDefinition:
    """Defines how different types of failures should be alerted"""
    failure_type: str
    alert_level: AlertLevel
    business_context: BusinessContext
    channels: List[str]
    escalation_time_minutes: int
    business_impact_description: str
    recovery_sla_minutes: int
    stakeholder_message_template: str
    technical_message_template: str
    escalation_chain: List[str]

# Alert Configuration Matrix
ALERT_DEFINITIONS = {
    "complete_api_failure": AlertDefinition(
        failure_type="complete_api_failure",
        alert_level=AlertLevel.EMERGENCY,
        business_context=BusinessContext.REVENUE_CRITICAL,
        channels=["pagerduty_critical", "phone_oncall", "slack_emergency", "email_executives"],
        escalation_time_minutes=5,
        business_impact_description="Complete API failure - all revenue generation stopped",
        recovery_sla_minutes=15,
        stakeholder_message_template="🚨 EMERGENCY: MarketEdge API completely unavailable. All customer access blocked. Revenue impact: £925K+ immediate risk. Recovery ETA: {recovery_eta}",
        technical_message_template="CRITICAL API FAILURE: {error_details}. All endpoints unresponsive. Immediate engineering response required.",
        escalation_chain=["oncall_engineer", "engineering_manager", "cto", "ceo"]
    ),

    "auth_system_failure": AlertDefinition(
        failure_type="auth_system_failure",
        alert_level=AlertLevel.EMERGENCY,
        business_context=BusinessContext.REVENUE_CRITICAL,
        channels=["pagerduty_critical", "slack_emergency", "email_immediate"],
        escalation_time_minutes=3,
        business_impact_description="Authentication system failure - no user access possible",
        recovery_sla_minutes=10,
        stakeholder_message_template="🚨 CRITICAL: Authentication system down. All users locked out. Revenue impact: Complete service unavailability. Immediate action in progress.",
        technical_message_template="AUTH SYSTEM FAILURE: {error_details}. All user authentication blocked. Auth0 integration or API router failure suspected.",
        escalation_chain=["oncall_engineer", "engineering_manager", "auth0_support"]
    ),

    "zebra_admin_failure": AlertDefinition(
        failure_type="zebra_admin_failure",
        alert_level=AlertLevel.CRITICAL,
        business_context=BusinessContext.ZEBRA_OPPORTUNITY,
        channels=["slack_zebra_channel", "email_matt_lindop", "slack_alerts", "email_sales_team"],
        escalation_time_minutes=10,
        business_impact_description="Zebra Associates admin access failure - £925K opportunity at risk",
        recovery_sla_minutes=30,
        stakeholder_message_template="🔴 ZEBRA ALERT: Admin panel unavailable for matt.lindop@zebra.associates. £925K cinema intelligence opportunity at immediate risk. Technical team investigating.",
        technical_message_template="ZEBRA ADMIN FAILURE: {error_details}. Admin endpoints or feature flags system may be down. Check /admin/feature-flags endpoint.",
        escalation_chain=["oncall_engineer", "product_manager", "sales_director"]
    ),

    "database_connection_failure": AlertDefinition(
        failure_type="database_connection_failure",
        alert_level=AlertLevel.EMERGENCY,
        business_context=BusinessContext.REVENUE_CRITICAL,
        channels=["pagerduty_critical", "slack_emergency", "email_immediate"],
        escalation_time_minutes=5,
        business_impact_description="Database connectivity failure - complete data access unavailable",
        recovery_sla_minutes=20,
        stakeholder_message_template="🚨 DATABASE CRITICAL: Complete data access failure. All functionality unavailable. Revenue impact: Total service outage. Database team mobilized.",
        technical_message_template="DATABASE FAILURE: {error_details}. PostgreSQL connection failed. Check database server status and connection pool.",
        escalation_chain=["oncall_engineer", "database_admin", "infrastructure_team"]
    ),

    "feature_flag_system_failure": AlertDefinition(
        failure_type="feature_flag_system_failure",
        alert_level=AlertLevel.HIGH,
        business_context=BusinessContext.CUSTOMER_EXPERIENCE,
        channels=["slack_alerts", "email_alerts"],
        escalation_time_minutes=15,
        business_impact_description="Feature flag system failure - business logic control compromised",
        recovery_sla_minutes=45,
        stakeholder_message_template="⚠️ Feature control system degraded. Some business features may not work correctly. Technical team investigating fallback options.",
        technical_message_template="FEATURE FLAGS FAILURE: {error_details}. Feature flag endpoints or database access issues. Using default configurations.",
        escalation_chain=["oncall_engineer", "product_manager"]
    ),

    "tenant_isolation_breach": AlertDefinition(
        failure_type="tenant_isolation_breach",
        alert_level=AlertLevel.EMERGENCY,
        business_context=BusinessContext.SECURITY,
        channels=["pagerduty_security", "slack_security", "email_security_team", "email_legal"],
        escalation_time_minutes=2,
        business_impact_description="Multi-tenant data isolation failure - potential data breach",
        recovery_sla_minutes=5,
        stakeholder_message_template="🚨 SECURITY ALERT: Data isolation systems failure detected. Immediate investigation launched. Customer data protection measures activated.",
        technical_message_template="SECURITY CRITICAL: {error_details}. Row-level security or tenant isolation failure. IMMEDIATE maintenance mode required.",
        escalation_chain=["security_engineer", "engineering_manager", "ciso", "legal_team"]
    ),

    "performance_degradation": AlertDefinition(
        failure_type="performance_degradation",
        alert_level=AlertLevel.MEDIUM,
        business_context=BusinessContext.CUSTOMER_EXPERIENCE,
        channels=["slack_alerts", "email_digest"],
        escalation_time_minutes=30,
        business_impact_description="API performance degradation - customer experience impacted",
        recovery_sla_minutes=60,
        stakeholder_message_template="⚠️ Performance Alert: API response times elevated. Customer experience may be impacted. Performance optimization in progress.",
        technical_message_template="PERFORMANCE DEGRADATION: {error_details}. Response times above threshold. Check server load and database performance.",
        escalation_chain=["oncall_engineer", "performance_team"]
    ),

    "session_storage_failure": AlertDefinition(
        failure_type="session_storage_failure",
        alert_level=AlertLevel.MEDIUM,
        business_context=BusinessContext.CUSTOMER_EXPERIENCE,
        channels=["slack_alerts", "email_alerts"],
        escalation_time_minutes=20,
        business_impact_description="Session storage failure - users experiencing re-authentication",
        recovery_sla_minutes=30,
        stakeholder_message_template="⚠️ Session Alert: Users may need to log in more frequently due to session storage issues. Backup systems active.",
        technical_message_template="REDIS FAILURE: {error_details}. Session storage degraded. Users may experience authentication prompts.",
        escalation_chain=["oncall_engineer", "infrastructure_team"]
    )
}
```

## Alert Channel Integration

### Channel Configuration and Capabilities

```python
class AlertChannel:
    """Base alert channel with delivery capabilities"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.delivery_time_seconds = config.get('delivery_time_seconds', 60)
        self.reliability_score = config.get('reliability_score', 0.95)

    async def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send alert through this channel"""
        raise NotImplementedError

    async def send_recovery(self, recovery_data: Dict[str, Any]) -> bool:
        """Send recovery notification"""
        raise NotImplementedError

class PagerDutyChannel(AlertChannel):
    """PagerDuty integration for critical alerts"""

    async def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        try:
            import httpx

            payload = {
                "routing_key": self.config['routing_key'],
                "event_action": "trigger",
                "dedup_key": f"marketedge_{alert_data['failure_type']}_{alert_data.get('component', 'unknown')}",
                "payload": {
                    "summary": alert_data['stakeholder_message'],
                    "source": "MarketEdge Platform",
                    "severity": alert_data['alert_level'],
                    "component": alert_data.get('component', 'api'),
                    "group": "platform",
                    "class": alert_data['business_context'],
                    "custom_details": {
                        "business_impact": alert_data['business_impact_description'],
                        "recovery_sla_minutes": alert_data['recovery_sla_minutes'],
                        "revenue_at_risk": alert_data.get('revenue_at_risk', 'Unknown'),
                        "technical_details": alert_data['technical_message'],
                        "escalation_chain": alert_data['escalation_chain']
                    }
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload,
                    timeout=30.0
                )
                return response.status_code == 202

        except Exception as e:
            logger.error(f"PagerDuty alert failed: {e}")
            return False

class SlackChannel(AlertChannel):
    """Slack integration for team notifications"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.webhook_url = config['webhook_url']
        self.channel = config.get('channel', '#alerts')

    async def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        try:
            import httpx

            # Create rich Slack message with business context
            color = self._get_alert_color(alert_data['alert_level'])

            message = {
                "channel": self.channel,
                "username": "MarketEdge Monitor",
                "icon_emoji": ":rotating_light:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"{alert_data['alert_level'].upper()}: {alert_data['failure_type'].replace('_', ' ').title()}",
                        "text": alert_data['stakeholder_message'],
                        "fields": [
                            {
                                "title": "Business Impact",
                                "value": alert_data['business_impact_description'],
                                "short": False
                            },
                            {
                                "title": "Recovery SLA",
                                "value": f"{alert_data['recovery_sla_minutes']} minutes",
                                "short": True
                            },
                            {
                                "title": "Component",
                                "value": alert_data.get('component', 'Unknown'),
                                "short": True
                            }
                        ],
                        "footer": "MarketEdge Platform Monitor",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }

            # Add technical details for engineering channels
            if 'engineering' in self.channel or 'alerts' in self.channel:
                message["attachments"][0]["fields"].append({
                    "title": "Technical Details",
                    "value": f"```{alert_data['technical_message']}```",
                    "short": False
                })

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    timeout=10.0
                )
                return response.status_code == 200

        except Exception as e:
            logger.error(f"Slack alert failed for {self.channel}: {e}")
            return False

    def _get_alert_color(self, alert_level: AlertLevel) -> str:
        """Get Slack color based on alert level"""
        colors = {
            AlertLevel.EMERGENCY: "danger",
            AlertLevel.CRITICAL: "danger",
            AlertLevel.HIGH: "warning",
            AlertLevel.MEDIUM: "warning",
            AlertLevel.LOW: "good",
            AlertLevel.INFO: "good"
        }
        return colors.get(alert_level, "warning")

class EmailChannel(AlertChannel):
    """Email integration for stakeholder notifications"""

    async def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert_data['alert_level'].upper()}] MarketEdge Alert: {alert_data['failure_type']}"
            msg['From'] = self.config['from_email']
            msg['To'] = ', '.join(alert_data.get('recipients', self.config['default_recipients']))

            # Create HTML email with business context
            html_content = self._create_html_email(alert_data)
            text_content = self._create_text_email(alert_data)

            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))

            # Send email
            with smtplib.SMTP(self.config['smtp_host'], self.config['smtp_port']) as server:
                if self.config.get('use_tls'):
                    server.starttls()
                if self.config.get('username'):
                    server.login(self.config['username'], self.config['password'])

                server.send_message(msg)
                return True

        except Exception as e:
            logger.error(f"Email alert failed: {e}")
            return False

    def _create_html_email(self, alert_data: Dict[str, Any]) -> str:
        """Create HTML email content with business styling"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
            <div style="background: {'#dc3545' if alert_data['alert_level'] in [AlertLevel.EMERGENCY, AlertLevel.CRITICAL] else '#fd7e14'}; color: white; padding: 15px; border-radius: 5px;">
                <h2 style="margin: 0;">{alert_data['alert_level'].upper()}: MarketEdge Platform Alert</h2>
            </div>

            <div style="margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; background: #f8f9fa;">
                <h3>Business Impact</h3>
                <p>{alert_data['business_impact_description']}</p>
            </div>

            <div style="margin: 20px 0;">
                <h3>Alert Details</h3>
                <p><strong>Component:</strong> {alert_data.get('component', 'Unknown')}</p>
                <p><strong>Time:</strong> {datetime.utcnow().isoformat()}</p>
                <p><strong>Recovery SLA:</strong> {alert_data['recovery_sla_minutes']} minutes</p>
            </div>

            <div style="margin: 20px 0;">
                <h3>Status Message</h3>
                <p>{alert_data['stakeholder_message']}</p>
            </div>

            <div style="margin: 20px 0; padding: 10px; background: #e9ecef; border-radius: 3px;">
                <p><strong>Next Steps:</strong> Engineering team has been notified. Updates will be provided every 15 minutes until resolution.</p>
            </div>
        </body>
        </html>
        """

    def _create_text_email(self, alert_data: Dict[str, Any]) -> str:
        """Create text email content"""
        return f"""
MarketEdge Platform Alert - {alert_data['alert_level'].upper()}

BUSINESS IMPACT:
{alert_data['business_impact_description']}

DETAILS:
- Component: {alert_data.get('component', 'Unknown')}
- Time: {datetime.utcnow().isoformat()}
- Recovery SLA: {alert_data['recovery_sla_minutes']} minutes

STATUS:
{alert_data['stakeholder_message']}

NEXT STEPS:
Engineering team has been notified. Updates will be provided every 15 minutes until resolution.

--
MarketEdge Platform Monitoring System
        """

# Channel Configuration
ALERT_CHANNELS = {
    "pagerduty_critical": PagerDutyChannel("pagerduty_critical", {
        "routing_key": os.getenv("PAGERDUTY_CRITICAL_ROUTING_KEY"),
        "delivery_time_seconds": 30,
        "reliability_score": 0.99
    }),

    "slack_emergency": SlackChannel("slack_emergency", {
        "webhook_url": os.getenv("SLACK_EMERGENCY_WEBHOOK"),
        "channel": "#emergency-alerts",
        "delivery_time_seconds": 15,
        "reliability_score": 0.95
    }),

    "slack_zebra_channel": SlackChannel("slack_zebra_channel", {
        "webhook_url": os.getenv("SLACK_ZEBRA_WEBHOOK"),
        "channel": "#zebra-associates-alerts",
        "delivery_time_seconds": 15,
        "reliability_score": 0.95
    }),

    "email_matt_lindop": EmailChannel("email_matt_lindop", {
        "smtp_host": os.getenv("SMTP_HOST"),
        "smtp_port": int(os.getenv("SMTP_PORT", 587)),
        "use_tls": True,
        "username": os.getenv("SMTP_USERNAME"),
        "password": os.getenv("SMTP_PASSWORD"),
        "from_email": "alerts@marketedge.com",
        "default_recipients": ["matt.lindop@zebra.associates"],
        "delivery_time_seconds": 60,
        "reliability_score": 0.90
    })
}
```

## Alert Manager Implementation

### Core Alert Management System

```python
class AlertManager:
    """Central alert management and orchestration"""

    def __init__(self):
        self.alert_definitions = ALERT_DEFINITIONS
        self.alert_channels = ALERT_CHANNELS
        self.active_alerts = {}  # Track active alerts to prevent duplicates
        self.alert_history = []  # Track alert history for analysis
        self.escalation_tasks = {}  # Track escalation timers

    async def send_monitoring_alert(self, monitoring_target, monitoring_result: MonitoringResult):
        """Send alert based on monitoring result"""

        # Determine alert type based on monitoring target and result
        alert_type = self._determine_alert_type(monitoring_target, monitoring_result)

        if alert_type not in self.alert_definitions:
            logger.error(f"Unknown alert type: {alert_type}")
            return

        alert_def = self.alert_definitions[alert_type]

        # Check if this alert is already active to prevent spam
        alert_key = f"{alert_type}_{monitoring_target.name}"
        if alert_key in self.active_alerts:
            logger.info(f"Alert already active for {alert_key}, skipping duplicate")
            return

        # Create alert data
        alert_data = self._create_alert_data(alert_def, monitoring_target, monitoring_result)

        # Send to configured channels
        success_channels = []
        failed_channels = []

        for channel_name in alert_def.channels:
            if channel_name in self.alert_channels:
                channel = self.alert_channels[channel_name]
                try:
                    success = await channel.send_alert(alert_data)
                    if success:
                        success_channels.append(channel_name)
                    else:
                        failed_channels.append(channel_name)
                except Exception as e:
                    logger.error(f"Alert channel {channel_name} failed: {e}")
                    failed_channels.append(channel_name)

        # Track alert
        self.active_alerts[alert_key] = {
            'alert_type': alert_type,
            'start_time': datetime.utcnow(),
            'alert_data': alert_data,
            'successful_channels': success_channels,
            'failed_channels': failed_channels
        }

        # Start escalation timer
        if alert_def.escalation_time_minutes > 0:
            self.escalation_tasks[alert_key] = asyncio.create_task(
                self._handle_escalation(alert_key, alert_def, alert_data)
            )

        logger.info(f"🚨 Alert sent for {alert_type}: {len(success_channels)} channels successful, {len(failed_channels)} failed")

    async def send_recovery_notification(self, monitoring_target, monitoring_result: MonitoringResult):
        """Send recovery notification"""

        alert_type = self._determine_alert_type(monitoring_target, monitoring_result)
        alert_key = f"{alert_type}_{monitoring_target.name}"

        if alert_key not in self.active_alerts:
            return  # No active alert to clear

        active_alert = self.active_alerts[alert_key]
        alert_def = self.alert_definitions.get(alert_type)

        if not alert_def:
            return

        # Create recovery data
        recovery_data = self._create_recovery_data(alert_def, monitoring_target, monitoring_result, active_alert)

        # Send recovery notifications
        for channel_name in active_alert['successful_channels']:
            if channel_name in self.alert_channels:
                channel = self.alert_channels[channel_name]
                try:
                    await channel.send_recovery(recovery_data)
                except Exception as e:
                    logger.error(f"Recovery notification failed for {channel_name}: {e}")

        # Cancel escalation if active
        if alert_key in self.escalation_tasks:
            self.escalation_tasks[alert_key].cancel()
            del self.escalation_tasks[alert_key]

        # Move to history and clear active alert
        alert_duration = datetime.utcnow() - active_alert['start_time']
        self.alert_history.append({
            **active_alert,
            'end_time': datetime.utcnow(),
            'duration_minutes': alert_duration.total_seconds() / 60,
            'resolution': 'recovered'
        })

        del self.active_alerts[alert_key]

        logger.info(f"✅ Recovery notification sent for {alert_type}")

    def _determine_alert_type(self, monitoring_target, monitoring_result: MonitoringResult) -> str:
        """Determine alert type based on monitoring context"""

        target_name_lower = monitoring_target.name.lower()

        # Map monitoring targets to alert types
        if 'auth' in target_name_lower and 'login' in target_name_lower:
            return "auth_system_failure"
        elif 'zebra' in target_name_lower or 'admin' in target_name_lower:
            return "zebra_admin_failure"
        elif 'database' in target_name_lower:
            return "database_connection_failure"
        elif 'feature' in target_name_lower and 'flag' in target_name_lower:
            return "feature_flag_system_failure"
        elif 'tenant' in target_name_lower and 'isolation' in target_name_lower:
            return "tenant_isolation_breach"
        elif 'response' in target_name_lower and 'time' in target_name_lower:
            return "performance_degradation"
        elif 'redis' in target_name_lower or 'session' in target_name_lower:
            return "session_storage_failure"
        elif 'critical' in target_name_lower and 'endpoint' in target_name_lower:
            return "complete_api_failure"
        else:
            return "performance_degradation"  # Default fallback

    def _create_alert_data(self, alert_def: AlertDefinition, monitoring_target, monitoring_result: MonitoringResult) -> Dict[str, Any]:
        """Create alert data for channels"""

        # Calculate business impact based on monitoring result
        revenue_at_risk = self._calculate_revenue_at_risk(alert_def.business_context, monitoring_result)

        return {
            'failure_type': alert_def.failure_type,
            'alert_level': alert_def.alert_level,
            'business_context': alert_def.business_context,
            'component': monitoring_target.name,
            'business_impact_description': alert_def.business_impact_description,
            'recovery_sla_minutes': alert_def.recovery_sla_minutes,
            'stakeholder_message': alert_def.stakeholder_message_template.format(
                recovery_eta=f"{alert_def.recovery_sla_minutes} minutes",
                error_details=monitoring_result.error_message or "System health check failed"
            ),
            'technical_message': alert_def.technical_message_template.format(
                error_details=monitoring_result.error_message or "Monitoring check failed"
            ),
            'escalation_chain': alert_def.escalation_chain,
            'revenue_at_risk': revenue_at_risk,
            'timestamp': monitoring_result.timestamp,
            'response_time_ms': monitoring_result.response_time_ms
        }

    def _create_recovery_data(self, alert_def: AlertDefinition, monitoring_target, monitoring_result: MonitoringResult, active_alert: Dict) -> Dict[str, Any]:
        """Create recovery notification data"""

        duration_minutes = (datetime.utcnow() - active_alert['start_time']).total_seconds() / 60

        return {
            'failure_type': alert_def.failure_type,
            'component': monitoring_target.name,
            'recovery_time_minutes': duration_minutes,
            'stakeholder_message': f"✅ RECOVERED: {monitoring_target.name} is now operational. Issue resolved in {duration_minutes:.1f} minutes.",
            'technical_message': f"System recovery confirmed. Response time: {monitoring_result.response_time_ms:.1f}ms",
            'met_sla': duration_minutes <= alert_def.recovery_sla_minutes
        }

    def _calculate_revenue_at_risk(self, business_context: BusinessContext, monitoring_result: MonitoringResult) -> str:
        """Calculate revenue at risk based on business context"""

        risk_calculations = {
            BusinessContext.REVENUE_CRITICAL: "£925K+ immediate risk - complete service outage",
            BusinessContext.ZEBRA_OPPORTUNITY: "£925K Zebra Associates opportunity at risk",
            BusinessContext.CUSTOMER_EXPERIENCE: "Customer churn risk - estimated £50K-200K impact",
            BusinessContext.OPERATIONAL: "Operational efficiency impact - estimated £10K-50K",
            BusinessContext.SECURITY: "Compliance and legal risk - potentially unlimited liability",
            BusinessContext.PERFORMANCE: "Customer satisfaction impact - estimated £25K-100K"
        }

        return risk_calculations.get(business_context, "Business impact assessment required")

    async def _handle_escalation(self, alert_key: str, alert_def: AlertDefinition, alert_data: Dict[str, Any]):
        """Handle alert escalation after timeout"""

        try:
            # Wait for escalation time
            await asyncio.sleep(alert_def.escalation_time_minutes * 60)

            # Check if alert is still active
            if alert_key not in self.active_alerts:
                return  # Alert was resolved

            # Send escalation
            escalation_data = {
                **alert_data,
                'escalated': True,
                'escalation_reason': f"No response after {alert_def.escalation_time_minutes} minutes",
                'stakeholder_message': f"🔥 ESCALATED: {alert_data['stakeholder_message']} - No response after {alert_def.escalation_time_minutes} minutes. Escalating to next level."
            }

            # Send to escalation channels (management, executives)
            escalation_channels = ["email_executives", "slack_management", "phone_oncall"]

            for channel_name in escalation_channels:
                if channel_name in self.alert_channels:
                    try:
                        await self.alert_channels[channel_name].send_alert(escalation_data)
                    except Exception as e:
                        logger.error(f"Escalation failed for {channel_name}: {e}")

            logger.error(f"🔥 Alert escalated: {alert_key}")

        except asyncio.CancelledError:
            # Escalation was cancelled due to recovery
            pass

    def get_alert_status(self) -> Dict[str, Any]:
        """Get current alert system status"""

        return {
            'active_alerts': len(self.active_alerts),
            'active_alert_details': {
                key: {
                    'type': alert['alert_type'],
                    'duration_minutes': (datetime.utcnow() - alert['start_time']).total_seconds() / 60,
                    'channels_notified': len(alert['successful_channels'])
                } for key, alert in self.active_alerts.items()
            },
            'total_alerts_today': len([a for a in self.alert_history if a['start_time'].date() == datetime.utcnow().date()]),
            'channel_health': {
                name: {'available': True, 'last_success': None}  # TODO: Track channel health
                for name in self.alert_channels.keys()
            }
        }
```

## Integration with Monitoring System

### Enhanced Monitoring Integration

```python
# Integration in runtime_monitor.py
class RuntimeMonitor:
    def __init__(self):
        # ... existing init ...
        self.alert_manager = AlertManager()

    async def initialize(self):
        """Initialize monitoring with alert manager"""
        await self.alert_manager.initialize()
        # ... rest of initialization ...

    async def _trigger_alert(self, target_name: str, target: MonitoringTarget, result: MonitoringResult):
        """Enhanced alert triggering with business context"""
        await self.alert_manager.send_monitoring_alert(target, result)

    async def _clear_alert(self, target_name: str, target: MonitoringTarget, result: MonitoringResult):
        """Enhanced alert clearing with recovery notifications"""
        await self.alert_manager.send_recovery_notification(target, result)
```

This alerting strategy ensures that the critical business context (especially the £925K Zebra Associates opportunity) is properly communicated to stakeholders with appropriate urgency and escalation patterns.