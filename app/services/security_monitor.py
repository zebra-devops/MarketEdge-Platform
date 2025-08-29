"""
Security Monitoring Service

Provides comprehensive security monitoring, audit logging, and threat detection
for the MarketEdge platform. Monitors authentication patterns, suspicious activities,
and security events across all services.
"""

import asyncio
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import hashlib
import ipaddress

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..models.user import User
from ..models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(str, Enum):
    """Security event types"""
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_FAILURE = "authz_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    TOKEN_ABUSE = "token_abuse"
    SESSION_ANOMALY = "session_anomaly"
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    ACCOUNT_LOCKOUT = "account_lockout"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SECURITY_SCAN = "security_scan"
    MALICIOUS_REQUEST = "malicious_request"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: EventType
    threat_level: ThreatLevel
    timestamp: datetime
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "threat_level": self.threat_level.value,
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "user_id": self.user_id,
            "user_agent": self.user_agent,
            "details": self.details,
            "metadata": self.metadata
        }


@dataclass
class ThreatIntelligence:
    """Threat intelligence data"""
    ip_reputation: Dict[str, str] = field(default_factory=dict)
    known_bad_ips: Set[str] = field(default_factory=set)
    suspicious_patterns: List[str] = field(default_factory=list)
    attack_signatures: Dict[str, str] = field(default_factory=dict)


class SecurityPatternDetector:
    """Detects security patterns and anomalies"""
    
    def __init__(self):
        self.brute_force_threshold = 10  # Failed attempts within time window
        self.brute_force_window = 300  # 5 minutes
        self.rate_limit_threshold = 1000  # Requests per minute
        self.session_anomaly_threshold = 5  # Suspicious session changes
        
        # Pattern tracking
        self._failed_attempts: Dict[str, deque] = defaultdict(deque)
        self._request_patterns: Dict[str, deque] = defaultdict(deque)
        self._session_patterns: Dict[str, List[Dict]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def detect_brute_force(self, identifier: str, timestamp: datetime) -> bool:
        """Detect brute force attacks"""
        with self._lock:
            current_time = timestamp.timestamp()
            
            # Clean old attempts
            while (self._failed_attempts[identifier] and 
                   current_time - self._failed_attempts[identifier][0] > self.brute_force_window):
                self._failed_attempts[identifier].popleft()
            
            # Add current attempt
            self._failed_attempts[identifier].append(current_time)
            
            # Check threshold
            return len(self._failed_attempts[identifier]) >= self.brute_force_threshold
    
    def detect_rate_limit_abuse(self, identifier: str, timestamp: datetime) -> bool:
        """Detect rate limiting abuse patterns"""
        with self._lock:
            current_time = timestamp.timestamp()
            
            # Clean old requests
            while (self._request_patterns[identifier] and 
                   current_time - self._request_patterns[identifier][0] > 60):  # 1 minute window
                self._request_patterns[identifier].popleft()
            
            # Add current request
            self._request_patterns[identifier].append(current_time)
            
            # Check threshold
            return len(self._request_patterns[identifier]) >= self.rate_limit_threshold
    
    def detect_session_anomaly(self, session_id: str, event_data: Dict[str, Any]) -> bool:
        """Detect session anomalies"""
        with self._lock:
            session_events = self._session_patterns[session_id]
            session_events.append({
                "timestamp": time.time(),
                "event": event_data
            })
            
            # Keep only recent events
            cutoff_time = time.time() - 3600  # 1 hour
            session_events[:] = [e for e in session_events if e["timestamp"] > cutoff_time]
            
            # Detect patterns
            if len(session_events) < 2:
                return False
            
            # Check for rapid IP changes
            ip_changes = 0
            last_ip = None
            for event in session_events[-10:]:  # Check last 10 events
                current_ip = event["event"].get("ip_address")
                if last_ip and current_ip and last_ip != current_ip:
                    ip_changes += 1
                last_ip = current_ip
            
            return ip_changes >= self.session_anomaly_threshold
    
    def detect_malicious_patterns(self, request_data: Dict[str, Any]) -> List[str]:
        """Detect malicious request patterns"""
        patterns = []
        
        # Check for common attack patterns
        path = request_data.get("path", "").lower()
        user_agent = request_data.get("user_agent", "").lower()
        
        # SQL injection patterns
        if any(pattern in path for pattern in ["'", "union", "select", "drop", "insert"]):
            patterns.append("sql_injection_attempt")
        
        # XSS patterns
        if any(pattern in path for pattern in ["<script", "javascript:", "onload="]):
            patterns.append("xss_attempt")
        
        # Directory traversal
        if "../" in path or "..%2f" in path:
            patterns.append("directory_traversal")
        
        # Security scanners
        scanner_patterns = ["nmap", "sqlmap", "burp", "owasp", "nikto"]
        if any(pattern in user_agent for pattern in scanner_patterns):
            patterns.append("security_scan")
        
        return patterns


class SecurityMonitor:
    """
    Comprehensive security monitoring service
    
    Features:
    - Real-time threat detection
    - Security event correlation
    - Automated response triggers
    - Audit logging
    - Threat intelligence integration
    """
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.pattern_detector = SecurityPatternDetector()
        self.threat_intelligence = ThreatIntelligence()
        
        # Event storage
        self.security_events: deque = deque(maxlen=max_events)
        self.event_counters: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
        
        # Alerting thresholds
        self.alert_thresholds = {
            ThreatLevel.LOW: 100,
            ThreatLevel.MEDIUM: 50,
            ThreatLevel.HIGH: 10,
            ThreatLevel.CRITICAL: 1
        }
        
        # Background tasks
        self._running = False
        self._background_task = None
        
        logger.info("Security Monitor initialized")
    
    async def start(self):
        """Start background monitoring tasks"""
        self._running = True
        self._background_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Security Monitor started")
    
    async def stop(self):
        """Stop background monitoring tasks"""
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        logger.info("Security Monitor stopped")
    
    async def log_security_event(
        self,
        event_type: EventType,
        threat_level: ThreatLevel,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a security event"""
        event = SecurityEvent(
            event_type=event_type,
            threat_level=threat_level,
            timestamp=datetime.utcnow(),
            source_ip=source_ip,
            user_id=user_id,
            user_agent=user_agent,
            details=details or {},
            metadata=metadata or {}
        )
        
        with self._lock:
            self.security_events.append(event)
            self.event_counters[event_type.value] += 1
        
        # Check for immediate alerts
        await self._check_alert_conditions(event)
        
        # Persist to database
        await self._persist_event(event)
        
        logger.warning(
            f"Security event: {event_type.value}",
            extra={
                "threat_level": threat_level.value,
                "source_ip": source_ip,
                "user_id": user_id,
                "details": details
            }
        )
    
    async def analyze_authentication_failure(
        self,
        source_ip: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):\n        \"\"\"Analyze authentication failure for patterns\"\"\"\n        timestamp = datetime.utcnow()\n        identifier = user_id or source_ip\n        \n        # Check for brute force\n        is_brute_force = self.pattern_detector.detect_brute_force(identifier, timestamp)\n        \n        threat_level = ThreatLevel.HIGH if is_brute_force else ThreatLevel.MEDIUM\n        event_type = EventType.BRUTE_FORCE_ATTACK if is_brute_force else EventType.AUTHENTICATION_FAILURE\n        \n        await self.log_security_event(\n            event_type=event_type,\n            threat_level=threat_level,\n            source_ip=source_ip,\n            user_id=user_id,\n            details=details,\n            metadata={\"brute_force_detected\": is_brute_force}\n        )\n    \n    async def analyze_request_pattern(\n        self,\n        source_ip: str,\n        request_data: Dict[str, Any],\n        user_id: Optional[str] = None\n    ):\n        \"\"\"Analyze request patterns for security threats\"\"\"\n        timestamp = datetime.utcnow()\n        \n        # Check for rate limit abuse\n        is_rate_abuse = self.pattern_detector.detect_rate_limit_abuse(source_ip, timestamp)\n        \n        # Check for malicious patterns\n        malicious_patterns = self.pattern_detector.detect_malicious_patterns(request_data)\n        \n        # Determine threat level\n        threat_level = ThreatLevel.LOW\n        if is_rate_abuse:\n            threat_level = ThreatLevel.MEDIUM\n        if malicious_patterns:\n            threat_level = ThreatLevel.HIGH\n        if \"sql_injection_attempt\" in malicious_patterns:\n            threat_level = ThreatLevel.CRITICAL\n        \n        if is_rate_abuse or malicious_patterns:\n            await self.log_security_event(\n                event_type=EventType.SUSPICIOUS_PATTERN,\n                threat_level=threat_level,\n                source_ip=source_ip,\n                user_id=user_id,\n                details={\n                    \"request_data\": request_data,\n                    \"malicious_patterns\": malicious_patterns,\n                    \"rate_abuse\": is_rate_abuse\n                }\n            )\n    \n    async def analyze_session_activity(\n        self,\n        session_id: str,\n        event_data: Dict[str, Any],\n        user_id: Optional[str] = None\n    ):\n        \"\"\"Analyze session activity for anomalies\"\"\"\n        is_anomaly = self.pattern_detector.detect_session_anomaly(session_id, event_data)\n        \n        if is_anomaly:\n            await self.log_security_event(\n                event_type=EventType.SESSION_ANOMALY,\n                threat_level=ThreatLevel.MEDIUM,\n                source_ip=event_data.get(\"ip_address\"),\n                user_id=user_id,\n                details={\n                    \"session_id\": session_id,\n                    \"event_data\": event_data\n                },\n                metadata={\"anomaly_detected\": True}\n            )\n    \n    def get_security_metrics(self) -> Dict[str, Any]:\n        \"\"\"Get current security metrics\"\"\"\n        with self._lock:\n            total_events = len(self.security_events)\n            \n            # Count events by threat level\n            threat_counts = defaultdict(int)\n            recent_events = []\n            cutoff_time = datetime.utcnow() - timedelta(hours=24)\n            \n            for event in self.security_events:\n                if event.timestamp > cutoff_time:\n                    threat_counts[event.threat_level.value] += 1\n                    recent_events.append(event.to_dict())\n            \n            return {\n                \"total_events\": total_events,\n                \"recent_24h\": len(recent_events),\n                \"threat_level_counts\": dict(threat_counts),\n                \"event_type_counts\": dict(self.event_counters),\n                \"recent_events\": recent_events[-10:]  # Last 10 events\n            }\n    \n    def get_threat_summary(self) -> Dict[str, Any]:\n        \"\"\"Get threat summary for monitoring dashboards\"\"\"\n        metrics = self.get_security_metrics()\n        \n        # Calculate threat score\n        threat_score = (\n            metrics[\"threat_level_counts\"].get(\"critical\", 0) * 10 +\n            metrics[\"threat_level_counts\"].get(\"high\", 0) * 5 +\n            metrics[\"threat_level_counts\"].get(\"medium\", 0) * 2 +\n            metrics[\"threat_level_counts\"].get(\"low\", 0) * 1\n        )\n        \n        # Determine overall threat status\n        if threat_score >= 50:\n            threat_status = \"critical\"\n        elif threat_score >= 20:\n            threat_status = \"high\"\n        elif threat_score >= 10:\n            threat_status = \"medium\"\n        else:\n            threat_status = \"low\"\n        \n        return {\n            \"threat_status\": threat_status,\n            \"threat_score\": threat_score,\n            \"active_threats\": metrics[\"threat_level_counts\"].get(\"high\", 0) + \n                            metrics[\"threat_level_counts\"].get(\"critical\", 0),\n            \"total_events_24h\": metrics[\"recent_24h\"],\n            \"top_threats\": self._get_top_threats()\n        }\n    \n    async def _check_alert_conditions(self, event: SecurityEvent):\n        \"\"\"Check if event triggers alert conditions\"\"\"\n        try:\n            # Check immediate alert thresholds\n            if event.threat_level == ThreatLevel.CRITICAL:\n                await self._trigger_alert(event, \"Critical security event detected\")\n            \n            # Check for pattern-based alerts\n            with self._lock:\n                recent_high_threats = sum(\n                    1 for e in list(self.security_events)[-100:] \n                    if e.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL] and \n                    (datetime.utcnow() - e.timestamp).total_seconds() < 300  # Last 5 minutes\n                )\n            \n            if recent_high_threats >= 5:\n                await self._trigger_alert(event, \"Multiple high-threat events detected\")\n                \n        except Exception as e:\n            logger.error(f\"Error checking alert conditions: {str(e)}\")\n    \n    async def _trigger_alert(self, event: SecurityEvent, message: str):\n        \"\"\"Trigger security alert\"\"\"\n        try:\n            alert_data = {\n                \"timestamp\": datetime.utcnow().isoformat(),\n                \"message\": message,\n                \"event\": event.to_dict(),\n                \"threat_summary\": self.get_threat_summary()\n            }\n            \n            # Log the alert\n            logger.critical(\n                f\"SECURITY ALERT: {message}\",\n                extra=alert_data\n            )\n            \n            # Here you could integrate with external alerting systems:\n            # - Send to security team via email/Slack\n            # - Trigger automated responses\n            # - Update security dashboards\n            # - Send to SIEM systems\n            \n        except Exception as e:\n            logger.error(f\"Error triggering security alert: {str(e)}\")\n    \n    async def _persist_event(self, event: SecurityEvent):\n        \"\"\"Persist security event to database\"\"\"\n        try:\n            async for db in get_db():\n                try:\n                    audit_log = AuditLog(\n                        user_id=event.user_id,\n                        action=\"SECURITY_EVENT\",\n                        resource_type=\"security\",\n                        resource_id=event.event_type.value,\n                        description=f\"{event.event_type.value}: {event.threat_level.value}\",\n                        ip_address=event.source_ip,\n                        user_agent=event.user_agent,\n                        metadata={\n                            \"event_type\": event.event_type.value,\n                            \"threat_level\": event.threat_level.value,\n                            \"details\": event.details,\n                            \"security_metadata\": event.metadata\n                        }\n                    )\n                    \n                    db.add(audit_log)\n                    await db.commit()\n                    break\n                    \n                except Exception as db_error:\n                    logger.error(f\"Database error persisting security event: {str(db_error)}\")\n                    await db.rollback()\n                    break\n                    \n        except Exception as e:\n            logger.error(f\"Error persisting security event: {str(e)}\")\n    \n    async def _monitoring_loop(self):\n        \"\"\"Background monitoring loop\"\"\"\n        while self._running:\n            try:\n                await asyncio.sleep(300)  # Run every 5 minutes\n                \n                # Cleanup old events\n                await self._cleanup_old_events()\n                \n                # Update threat intelligence\n                await self._update_threat_intelligence()\n                \n                # Generate periodic reports\n                await self._generate_periodic_report()\n                \n            except asyncio.CancelledError:\n                break\n            except Exception as e:\n                logger.error(f\"Error in security monitoring loop: {str(e)}\")\n                await asyncio.sleep(60)  # Wait before retrying\n    \n    async def _cleanup_old_events(self):\n        \"\"\"Clean up old security events\"\"\"\n        try:\n            cutoff_time = datetime.utcnow() - timedelta(days=7)  # Keep 7 days\n            \n            with self._lock:\n                # Clean pattern detector data\n                current_time = time.time()\n                \n                # Clean failed attempts older than window\n                for identifier in list(self.pattern_detector._failed_attempts.keys()):\n                    attempts = self.pattern_detector._failed_attempts[identifier]\n                    while attempts and current_time - attempts[0] > self.pattern_detector.brute_force_window:\n                        attempts.popleft()\n                    if not attempts:\n                        del self.pattern_detector._failed_attempts[identifier]\n                \n                # Clean request patterns\n                for identifier in list(self.pattern_detector._request_patterns.keys()):\n                    requests = self.pattern_detector._request_patterns[identifier]\n                    while requests and current_time - requests[0] > 60:\n                        requests.popleft()\n                    if not requests:\n                        del self.pattern_detector._request_patterns[identifier]\n            \n            logger.debug(\"Cleaned up old security monitoring data\")\n            \n        except Exception as e:\n            logger.error(f\"Error cleaning up old events: {str(e)}\")\n    \n    async def _update_threat_intelligence(self):\n        \"\"\"Update threat intelligence data\"\"\"\n        try:\n            # Here you could integrate with external threat intelligence feeds\n            # For now, just log that we're updating\n            logger.debug(\"Updated threat intelligence data\")\n            \n        except Exception as e:\n            logger.error(f\"Error updating threat intelligence: {str(e)}\")\n    \n    async def _generate_periodic_report(self):\n        \"\"\"Generate periodic security reports\"\"\"\n        try:\n            metrics = self.get_security_metrics()\n            threat_summary = self.get_threat_summary()\n            \n            logger.info(\n                \"Security monitoring report\",\n                extra={\n                    \"metrics\": metrics,\n                    \"threat_summary\": threat_summary\n                }\n            )\n            \n        except Exception as e:\n            logger.error(f\"Error generating periodic report: {str(e)}\")\n    \n    def _get_top_threats(self) -> List[Dict[str, Any]]:\n        \"\"\"Get top threats from recent events\"\"\"\n        try:\n            with self._lock:\n                recent_events = [\n                    event for event in self.security_events\n                    if (datetime.utcnow() - event.timestamp).total_seconds() < 3600  # Last hour\n                ]\n                \n                # Group by event type\n                threat_counts = defaultdict(lambda: {\"count\": 0, \"max_threat\": ThreatLevel.LOW})\n                \n                for event in recent_events:\n                    threat_counts[event.event_type.value][\"count\"] += 1\n                    if event.threat_level.value > threat_counts[event.event_type.value][\"max_threat\"].value:\n                        threat_counts[event.event_type.value][\"max_threat\"] = event.threat_level\n                \n                # Sort by threat level and count\n                top_threats = []\n                for event_type, data in threat_counts.items():\n                    top_threats.append({\n                        \"event_type\": event_type,\n                        \"count\": data[\"count\"],\n                        \"max_threat_level\": data[\"max_threat\"].value\n                    })\n                \n                return sorted(top_threats, key=lambda x: (x[\"max_threat_level\"], x[\"count\"]), reverse=True)[:5]\n                \n        except Exception as e:\n            logger.error(f\"Error getting top threats: {str(e)}\")\n            return []\n\n\n# Global instance\nsecurity_monitor: Optional[SecurityMonitor] = None\n\n\ndef get_security_monitor() -> SecurityMonitor:\n    \"\"\"Get the global security monitor instance\"\"\"\n    global security_monitor\n    if security_monitor is None:\n        raise RuntimeError(\"Security monitor not initialized\")\n    return security_monitor\n\n\nasync def initialize_security_monitor() -> SecurityMonitor:\n    \"\"\"Initialize the global security monitor\"\"\"\n    global security_monitor\n    if security_monitor is None:\n        security_monitor = SecurityMonitor()\n        await security_monitor.start()\n        logger.info(\"Global security monitor initialized\")\n    return security_monitor