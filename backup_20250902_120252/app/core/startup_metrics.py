"""
Startup Performance Monitoring for Lazy Initialization Architecture
Tracks and reports on system startup performance and service availability
"""

import time
import logging
import psutil
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import asyncio
import threading

logger = logging.getLogger(__name__)


@dataclass
class StartupMetric:
    """Individual startup metric data"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System resource metrics at startup"""
    cpu_percent: float
    memory_usage_mb: float
    memory_percent: float
    disk_usage_percent: float
    process_memory_mb: float
    open_connections: int
    thread_count: int


class StartupPerformanceMonitor:
    """
    Monitors and tracks startup performance for the lazy initialization architecture
    Provides detailed metrics and reporting for optimization
    """
    
    def __init__(self):
        self._metrics: Dict[str, StartupMetric] = {}
        self._system_metrics: List[SystemMetrics] = []
        self._startup_start_time = time.time()
        self._cold_start_threshold = 5.0  # seconds
        self._monitoring_active = True
        self._lock = threading.Lock()
        
        # Environment detection
        self._is_render = bool(os.getenv("RENDER"))
        self._is_production = os.getenv("ENVIRONMENT", "").lower() == "production"
        
        logger.info("Startup performance monitoring initialized")
        
    def start_metric(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Start tracking a metric"""
        with self._lock:
            if name in self._metrics:
                logger.warning(f"Metric '{name}' already started, overwriting")
                
            self._metrics[name] = StartupMetric(
                name=name,
                start_time=time.time(),
                metadata=metadata or {}
            )
            
        logger.debug(f"Started tracking metric: {name}")
        
    def end_metric(self, name: str, success: bool = True, error_message: Optional[str] = None):
        """End tracking a metric"""
        with self._lock:
            if name not in self._metrics:
                logger.error(f"Metric '{name}' not found to end")
                return
                
            metric = self._metrics[name]
            metric.end_time = time.time()
            metric.duration = metric.end_time - metric.start_time
            metric.success = success
            metric.error_message = error_message
            
        logger.debug(f"Ended tracking metric: {name} (duration: {metric.duration:.3f}s, success: {success})")
        
    def record_system_metrics(self):
        """Record current system resource metrics"""
        try:
            process = psutil.Process()
            
            # Get memory info
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            # Get disk usage
            disk_usage = psutil.disk_usage('/')
            
            # Get CPU usage (averaged over short period)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Count open connections
            try:
                connections = len(process.connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
                
            system_metric = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_usage_mb=system_memory.used / (1024 * 1024),
                memory_percent=system_memory.percent,
                disk_usage_percent=disk_usage.percent,
                process_memory_mb=memory_info.rss / (1024 * 1024),
                open_connections=connections,
                thread_count=process.num_threads()
            )
            
            with self._lock:
                self._system_metrics.append(system_metric)
                # Keep only last 10 measurements
                if len(self._system_metrics) > 10:
                    self._system_metrics = self._system_metrics[-10:]
                    
            logger.debug(f"Recorded system metrics: CPU {cpu_percent}%, Memory {memory_info.rss / (1024 * 1024):.1f}MB")
            
        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}")
            
    async def periodic_monitoring(self, interval: int = 30):
        """Run periodic system monitoring"""
        while self._monitoring_active:
            try:
                self.record_system_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in periodic monitoring: {e}")
                await asyncio.sleep(interval)
                
    def stop_monitoring(self):
        """Stop periodic monitoring"""
        self._monitoring_active = False
        logger.info("Startup performance monitoring stopped")
        
    def get_startup_summary(self) -> Dict[str, Any]:
        """Get comprehensive startup performance summary"""
        current_time = time.time()
        total_startup_time = current_time - self._startup_start_time
        
        # Analyze metrics
        successful_metrics = [m for m in self._metrics.values() if m.success and m.duration is not None]
        failed_metrics = [m for m in self._metrics.values() if not m.success]
        
        # Calculate performance statistics
        if successful_metrics:
            total_init_time = sum(m.duration for m in successful_metrics)
            avg_init_time = total_init_time / len(successful_metrics)
            max_init_time = max(m.duration for m in successful_metrics)
            min_init_time = min(m.duration for m in successful_metrics)
        else:
            total_init_time = avg_init_time = max_init_time = min_init_time = 0
            
        # Get latest system metrics
        latest_system_metrics = self._system_metrics[-1] if self._system_metrics else None
        
        return {
            "startup_performance": {
                "total_startup_time": round(total_startup_time, 3),
                "cold_start_threshold": self._cold_start_threshold,
                "cold_start_success": total_startup_time < self._cold_start_threshold,
                "performance_grade": self._calculate_performance_grade(total_startup_time),
                "startup_timestamp": self._startup_start_time,
                "current_timestamp": current_time
            },
            "initialization_metrics": {
                "total_metrics": len(self._metrics),
                "successful_initializations": len(successful_metrics),
                "failed_initializations": len(failed_metrics),
                "total_init_time": round(total_init_time, 3),
                "average_init_time": round(avg_init_time, 3) if successful_metrics else 0,
                "max_init_time": round(max_init_time, 3) if successful_metrics else 0,
                "min_init_time": round(min_init_time, 3) if successful_metrics else 0
            },
            "detailed_metrics": {
                metric.name: {
                    "duration": round(metric.duration, 3) if metric.duration else None,
                    "success": metric.success,
                    "error": metric.error_message,
                    "metadata": metric.metadata
                }
                for metric in self._metrics.values()
            },
            "system_metrics": {
                "current": {
                    "cpu_percent": latest_system_metrics.cpu_percent if latest_system_metrics else None,
                    "memory_usage_mb": round(latest_system_metrics.memory_usage_mb, 1) if latest_system_metrics else None,
                    "memory_percent": round(latest_system_metrics.memory_percent, 1) if latest_system_metrics else None,
                    "disk_usage_percent": round(latest_system_metrics.disk_usage_percent, 1) if latest_system_metrics else None,
                    "process_memory_mb": round(latest_system_metrics.process_memory_mb, 1) if latest_system_metrics else None,
                    "open_connections": latest_system_metrics.open_connections if latest_system_metrics else None,
                    "thread_count": latest_system_metrics.thread_count if latest_system_metrics else None
                },
                "history_count": len(self._system_metrics)
            },
            "environment": {
                "is_render": self._is_render,
                "is_production": self._is_production,
                "process_id": os.getpid(),
                "python_version": os.sys.version.split()[0],
                "platform": os.sys.platform
            },
            "optimization_recommendations": self._get_optimization_recommendations(total_startup_time)
        }
        
    def _calculate_performance_grade(self, startup_time: float) -> str:
        """Calculate performance grade based on startup time"""
        if startup_time < 2.0:
            return "A+ (Excellent)"
        elif startup_time < 3.0:
            return "A (Very Good)"
        elif startup_time < 5.0:
            return "B (Good)"
        elif startup_time < 8.0:
            return "C (Fair)"
        elif startup_time < 12.0:
            return "D (Poor)"
        else:
            return "F (Critical)"
            
    def _get_optimization_recommendations(self, startup_time: float) -> List[str]:
        """Get optimization recommendations based on performance metrics"""
        recommendations = []
        
        if startup_time > self._cold_start_threshold:
            recommendations.append(f"Cold start time ({startup_time:.3f}s) exceeds target ({self._cold_start_threshold}s)")
            
        # Analyze failed metrics
        failed_metrics = [m for m in self._metrics.values() if not m.success]
        if failed_metrics:
            recommendations.append(f"{len(failed_metrics)} service(s) failed to initialize")
            
        # Analyze slow metrics  
        slow_metrics = [m for m in self._metrics.values() if m.duration and m.duration > 2.0]
        if slow_metrics:
            slowest = max(slow_metrics, key=lambda m: m.duration)
            recommendations.append(f"Slowest service: {slowest.name} ({slowest.duration:.3f}s)")
            
        # System resource recommendations
        if self._system_metrics:
            latest = self._system_metrics[-1]
            
            if latest.memory_percent > 80:
                recommendations.append(f"High memory usage: {latest.memory_percent:.1f}%")
                
            if latest.cpu_percent > 80:
                recommendations.append(f"High CPU usage: {latest.cpu_percent:.1f}%")
                
            if latest.disk_usage_percent > 90:
                recommendations.append(f"High disk usage: {latest.disk_usage_percent:.1f}%")
                
        if not recommendations:
            recommendations.append("Performance is optimal")
            
        return recommendations
        
    def get_render_specific_metrics(self) -> Dict[str, Any]:
        """Get Render.com specific performance metrics"""
        if not self._is_render:
            return {"render_deployment": False}
            
        return {
            "render_deployment": True,
            "startup_within_timeout": time.time() - self._startup_start_time < 300,  # 5 minute Render timeout
            "memory_optimized": self._system_metrics[-1].process_memory_mb < 512 if self._system_metrics else False,  # Render memory limits
            "cold_start_optimized": time.time() - self._startup_start_time < self._cold_start_threshold,
            "render_health_ready": True  # Application is responding
        }


# Global startup performance monitor
startup_monitor = StartupPerformanceMonitor()


# Decorator for automatic metric tracking
def track_startup_metric(name: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator to automatically track startup metrics"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                startup_monitor.start_metric(name, metadata)
                try:
                    result = await func(*args, **kwargs)
                    startup_monitor.end_metric(name, success=True)
                    return result
                except Exception as e:
                    startup_monitor.end_metric(name, success=False, error_message=str(e))
                    raise
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                startup_monitor.start_metric(name, metadata)
                try:
                    result = func(*args, **kwargs)
                    startup_monitor.end_metric(name, success=True)
                    return result
                except Exception as e:
                    startup_monitor.end_metric(name, success=False, error_message=str(e))
                    raise
            return sync_wrapper
    return decorator