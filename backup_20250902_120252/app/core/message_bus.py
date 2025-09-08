"""
US-104: Inter-Module Communication - Message Bus

This module provides a centralized message bus for inter-module communication,
supporting both synchronous (request-response) and asynchronous (pub-sub) patterns
with comprehensive error handling, retry mechanisms, and performance monitoring.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import threading
import weakref
from collections import defaultdict, OrderedDict
import hashlib

from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import traceback

from ..models.modules import ModuleUsageLog
from ..core.database import get_db
from ..services.audit_service import AuditService
from ..core.module_registry import get_module_registry

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages supported by the message bus"""
    REQUEST = "request"           # Synchronous request-response
    RESPONSE = "response"         # Response to a request
    EVENT = "event"              # Asynchronous event notification
    COMMAND = "command"          # Command to execute an action
    BROADCAST = "broadcast"      # Broadcast to all subscribers
    MULTICAST = "multicast"      # Send to multiple specific recipients


class MessageStatus(Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    DEAD_LETTER = "dead_letter"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class MessageMetadata:
    """Metadata for message tracking and routing"""
    message_id: str
    correlation_id: Optional[str] = None
    sender_module: str = ""
    recipient_module: Optional[str] = None
    topic: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: MessagePriority = MessagePriority.NORMAL
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        data['priority'] = self.priority.value
        data['tags'] = list(self.tags)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageMetadata':
        """Create from dictionary"""
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'expires_at' in data and data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        if 'priority' in data:
            data['priority'] = MessagePriority(data['priority'])
        if 'tags' in data:
            data['tags'] = set(data['tags'])
        return cls(**data)


@dataclass
class Message:
    """Core message structure for inter-module communication"""
    message_type: MessageType
    payload: Dict[str, Any]
    metadata: MessageMetadata
    status: MessageStatus = MessageStatus.PENDING
    error_message: Optional[str] = None
    processing_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            "message_type": self.message_type.value,
            "payload": self.payload,
            "metadata": self.metadata.to_dict(),
            "status": self.status.value,
            "error_message": self.error_message,
            "processing_time_ms": self.processing_time_ms
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            message_type=MessageType(data["message_type"]),
            payload=data["payload"],
            metadata=MessageMetadata.from_dict(data["metadata"]),
            status=MessageStatus(data["status"]),
            error_message=data.get("error_message"),
            processing_time_ms=data.get("processing_time_ms")
        )
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        if not self.metadata.expires_at:
            return False
        return datetime.utcnow() > self.metadata.expires_at


class MessageHandler(ABC):
    """Abstract base class for message handlers"""
    
    @abstractmethod
    async def handle_message(self, message: Message) -> Any:
        """Handle incoming message"""
        pass
    
    @abstractmethod
    def get_supported_message_types(self) -> List[MessageType]:
        """Get supported message types"""
        pass
    
    @abstractmethod
    def get_topics(self) -> List[str]:
        """Get topics this handler subscribes to"""
        pass


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5      # Failures before opening
    success_threshold: int = 3      # Successes to close from half-open
    timeout_seconds: int = 60       # Time to stay open
    reset_timeout_seconds: int = 30  # Time before trying half-open


class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.next_attempt_time = None
        self._lock = threading.RLock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if not await self._can_execute():
            raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _can_execute(self) -> bool:
        """Check if execution is allowed"""
        with self._lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True
            elif self.state == CircuitBreakerState.OPEN:
                if self.next_attempt_time and datetime.utcnow() > self.next_attempt_time:
                    self.state = CircuitBreakerState.HALF_OPEN
                    return True
                return False
            elif self.state == CircuitBreakerState.HALF_OPEN:
                return True
        return False
    
    async def _on_success(self):
        """Handle successful execution"""
        with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            else:
                self.failure_count = 0
    
    async def _on_failure(self):
        """Handle failed execution"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self.next_attempt_time = datetime.utcnow() + timedelta(
                    seconds=self.config.timeout_seconds
                )


class MessageStorage:
    """Persistent storage for messages with Redis and database support"""
    
    def __init__(
        self, 
        redis_client: Optional[aioredis.Redis] = None,
        max_memory_messages: int = 10000
    ):
        self.redis = redis_client
        self.max_memory_messages = max_memory_messages
        
        # In-memory storage for when Redis is unavailable
        self.memory_storage: OrderedDict[str, Message] = OrderedDict()
        self._storage_lock = threading.RLock()
    
    async def store_message(self, message: Message, ttl_seconds: int = 3600):
        """Store message with TTL"""
        try:
            message_data = json.dumps(message.to_dict())
            
            # Try Redis first
            if self.redis:
                await self.redis.setex(
                    f"message:{message.metadata.message_id}",
                    ttl_seconds,
                    message_data
                )
            else:
                # Fallback to memory with size limits
                with self._storage_lock:
                    if len(self.memory_storage) >= self.max_memory_messages:
                        # Remove oldest message
                        self.memory_storage.popitem(last=False)
                    
                    self.memory_storage[message.metadata.message_id] = message
                    # Move to end for LRU
                    self.memory_storage.move_to_end(message.metadata.message_id)
                    
        except Exception as e:
            logger.error(f"Failed to store message {message.metadata.message_id}: {str(e)}")
    
    async def retrieve_message(self, message_id: str) -> Optional[Message]:
        """Retrieve message by ID"""
        try:
            # Try Redis first
            if self.redis:
                message_data = await self.redis.get(f"message:{message_id}")
                if message_data:
                    data = json.loads(message_data)
                    return Message.from_dict(data)
            
            # Fallback to memory
            with self._storage_lock:
                return self.memory_storage.get(message_id)
                    
        except Exception as e:
            logger.error(f"Failed to retrieve message {message_id}: {str(e)}")
        
        return None
    
    async def delete_message(self, message_id: str):
        """Delete message from storage"""
        try:
            if self.redis:
                await self.redis.delete(f"message:{message_id}")
            
            with self._storage_lock:
                if message_id in self.memory_storage:
                    del self.memory_storage[message_id]
                    
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {str(e)}")


class DeadLetterQueue:
    """Handle failed messages that cannot be processed"""
    
    def __init__(self, storage: MessageStorage, audit_service: Optional[AuditService] = None):
        self.storage = storage
        self.audit_service = audit_service
        self.dead_messages: Dict[str, Message] = {}
        self._dlq_lock = threading.RLock()
    
    async def add_message(self, message: Message, reason: str):
        """Add message to dead letter queue"""
        try:
            message.status = MessageStatus.DEAD_LETTER
            message.error_message = f"Dead letter: {reason}"
            
            with self._dlq_lock:
                self.dead_messages[message.metadata.message_id] = message
            
            # Store persistently
            await self.storage.store_message(message, ttl_seconds=86400)  # 24 hours
            
            # Audit log
            if self.audit_service:
                await self.audit_service.log_action(
                    user_id="system",
                    action="MESSAGE_DEAD_LETTER",
                    resource_type="message",
                    resource_id=message.metadata.message_id,
                    description=f"Message moved to dead letter queue: {reason}",
                    metadata={
                        "sender_module": message.metadata.sender_module,
                        "recipient_module": message.metadata.recipient_module,
                        "message_type": message.message_type.value,
                        "reason": reason
                    }
                )
            
            logger.warning(f"Message {message.metadata.message_id} moved to dead letter queue: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to add message to dead letter queue: {str(e)}")
    
    async def get_dead_messages(self, limit: int = 100) -> List[Message]:
        """Get messages from dead letter queue"""
        with self._dlq_lock:
            messages = list(self.dead_messages.values())
            return messages[:limit]
    
    async def reprocess_message(self, message_id: str) -> Optional[Message]:
        """Remove message from DLQ for reprocessing"""
        with self._dlq_lock:
            message = self.dead_messages.pop(message_id, None)
            if message:
                message.status = MessageStatus.PENDING
                message.error_message = None
                message.metadata.retry_count = 0
            return message


class MessageBusMetrics:
    """Metrics collection for message bus performance"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._metrics_lock = threading.RLock()
        
        # Aggregated metrics
        self.total_messages_sent = 0
        self.total_messages_processed = 0
        self.total_failures = 0
        self.total_timeouts = 0
        
        # Performance tracking
        self.processing_times: List[float] = []
        self.max_processing_times = 1000  # Keep last 1000 measurements
    
    def record_message_sent(self, message: Message):
        """Record message sent metric"""
        with self._metrics_lock:
            self.total_messages_sent += 1
            self._add_metric("messages_sent", {
                "timestamp": datetime.utcnow().isoformat(),
                "message_id": message.metadata.message_id,
                "message_type": message.message_type.value,
                "sender_module": message.metadata.sender_module,
                "recipient_module": message.metadata.recipient_module,
                "priority": message.metadata.priority.value
            })
    
    def record_message_processed(self, message: Message, processing_time_ms: float):
        """Record message processed metric"""
        with self._metrics_lock:
            self.total_messages_processed += 1
            
            # Track processing times
            self.processing_times.append(processing_time_ms)
            if len(self.processing_times) > self.max_processing_times:
                self.processing_times.pop(0)
            
            self._add_metric("messages_processed", {
                "timestamp": datetime.utcnow().isoformat(),
                "message_id": message.metadata.message_id,
                "processing_time_ms": processing_time_ms,
                "status": message.status.value
            })
    
    def record_failure(self, message: Message, error: str):
        """Record message failure metric"""
        with self._metrics_lock:
            self.total_failures += 1
            self._add_metric("message_failures", {
                "timestamp": datetime.utcnow().isoformat(),
                "message_id": message.metadata.message_id,
                "error": error,
                "retry_count": message.metadata.retry_count
            })
    
    def record_timeout(self, message: Message):
        """Record message timeout metric"""
        with self._metrics_lock:
            self.total_timeouts += 1
            self._add_metric("message_timeouts", {
                "timestamp": datetime.utcnow().isoformat(),
                "message_id": message.metadata.message_id
            })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        with self._metrics_lock:
            avg_processing_time = (
                sum(self.processing_times) / len(self.processing_times)
                if self.processing_times else 0
            )
            
            return {
                "total_messages_sent": self.total_messages_sent,
                "total_messages_processed": self.total_messages_processed,
                "total_failures": self.total_failures,
                "total_timeouts": self.total_timeouts,
                "success_rate": (
                    self.total_messages_processed / self.total_messages_sent
                    if self.total_messages_sent > 0 else 1.0
                ),
                "failure_rate": (
                    self.total_failures / self.total_messages_sent
                    if self.total_messages_sent > 0 else 0.0
                ),
                "average_processing_time_ms": avg_processing_time,
                "metrics_collected": sum(len(metrics) for metrics in self.metrics.values())
            }
    
    def _add_metric(self, metric_type: str, data: Dict[str, Any]):
        """Add metric with memory bounds"""
        metrics_list = self.metrics[metric_type]
        metrics_list.append(data)
        
        # Enforce memory limits
        if len(metrics_list) > self.max_metrics // len(self.metrics or {"default": 1}):
            metrics_list.pop(0)


class InterModuleMessageBus:
    """
    US-104: Centralized message bus for inter-module communication
    
    Provides:
    - Request-response and pub-sub communication patterns
    - Message routing and filtering
    - Circuit breaker and retry mechanisms
    - Dead letter queue handling
    - Performance monitoring and metrics
    - Event-driven architecture support
    """
    
    def __init__(
        self,
        redis_client: Optional[aioredis.Redis] = None,
        audit_service: Optional[AuditService] = None,
        max_concurrent_messages: int = 1000
    ):
        self.redis = redis_client
        self.audit_service = audit_service
        self.max_concurrent_messages = max_concurrent_messages
        
        # Core components
        self.storage = MessageStorage(redis_client)
        self.dead_letter_queue = DeadLetterQueue(self.storage, audit_service)
        self.metrics = MessageBusMetrics()
        
        # Message handling
        self.message_handlers: Dict[str, List[MessageHandler]] = defaultdict(list)
        self.topic_subscribers: Dict[str, List[MessageHandler]] = defaultdict(list)
        self.pending_responses: Dict[str, asyncio.Future] = {}
        
        # Circuit breakers per module
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Processing queues with priority
        self.message_queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in MessagePriority
        }
        
        # Background tasks
        self.executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="message-bus")
        self.background_tasks: List[asyncio.Task] = []
        self.processing_semaphore = asyncio.Semaphore(max_concurrent_messages)
        
        # Locks for thread safety
        self._handlers_lock = threading.RLock()
        self._responses_lock = threading.RLock()
        
        logger.info(f"Inter-module message bus initialized with max concurrent messages: {max_concurrent_messages}")
    
    async def start(self):
        """Start message bus processing"""
        try:
            # Start message processing tasks for each priority
            for priority in MessagePriority:
                task = asyncio.create_task(
                    self._process_messages_by_priority(priority)
                )
                self.background_tasks.append(task)
            
            # Start cleanup task
            cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
            self.background_tasks.append(cleanup_task)
            
            # Start metrics rotation task
            metrics_task = asyncio.create_task(self._rotate_metrics())
            self.background_tasks.append(metrics_task)
            
            logger.info("Message bus background tasks started")
            
        except Exception as e:
            logger.error(f"Failed to start message bus: {str(e)}")
            raise
    
    async def stop(self):
        """Stop message bus processing"""
        try:
            # Cancel all background tasks
            for task in self.background_tasks:
                task.cancel()
            
            if self.background_tasks:
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            # Shutdown executor
            self.executor.shutdown(wait=True, timeout=30)
            
            logger.info("Message bus stopped")
            
        except Exception as e:
            logger.error(f"Error stopping message bus: {str(e)}")
    
    def register_handler(self, handler: MessageHandler, module_id: str):
        """Register a message handler for a module"""
        with self._handlers_lock:
            # Register for message types
            for message_type in handler.get_supported_message_types():
                key = f"{module_id}:{message_type.value}"
                self.message_handlers[key].append(handler)
            
            # Register for topics
            for topic in handler.get_topics():
                self.topic_subscribers[topic].append(handler)
            
            # Create circuit breaker for module if not exists
            if module_id not in self.circuit_breakers:
                self.circuit_breakers[module_id] = CircuitBreaker(
                    CircuitBreakerConfig()
                )
        
        logger.info(f"Registered message handler for module {module_id}")
    
    def unregister_handler(self, handler: MessageHandler, module_id: str):
        """Unregister a message handler"""
        with self._handlers_lock:
            # Remove from message types
            for message_type in handler.get_supported_message_types():
                key = f"{module_id}:{message_type.value}"
                if handler in self.message_handlers[key]:
                    self.message_handlers[key].remove(handler)
            
            # Remove from topics
            for topic in handler.get_topics():
                if handler in self.topic_subscribers[topic]:
                    self.topic_subscribers[topic].remove(handler)
        
        logger.info(f"Unregistered message handler for module {module_id}")
    
    async def send_request(
        self,
        sender_module: str,
        recipient_module: str,
        payload: Dict[str, Any],
        timeout_seconds: int = 30,
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None
    ) -> Any:
        """
        Send synchronous request and wait for response
        
        Args:
            sender_module: Module sending the request
            recipient_module: Module to receive the request
            payload: Request data
            timeout_seconds: Request timeout
            priority: Message priority
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            Response data from recipient module
        """
        try:
            # Create request message
            message_id = str(uuid.uuid4())
            correlation_id = correlation_id or str(uuid.uuid4())
            
            metadata = MessageMetadata(
                message_id=message_id,
                correlation_id=correlation_id,
                sender_module=sender_module,
                recipient_module=recipient_module,
                expires_at=datetime.utcnow() + timedelta(seconds=timeout_seconds),
                priority=priority
            )
            
            message = Message(
                message_type=MessageType.REQUEST,
                payload=payload,
                metadata=metadata
            )
            
            # Create future for response
            response_future = asyncio.Future()
            with self._responses_lock:
                self.pending_responses[correlation_id] = response_future
            
            # Send message
            await self._queue_message(message)
            self.metrics.record_message_sent(message)
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(response_future, timeout=timeout_seconds)
                return response
            except asyncio.TimeoutError:
                self.metrics.record_timeout(message)
                raise Exception(f"Request to {recipient_module} timed out after {timeout_seconds}s")
            
        except Exception as e:
            logger.error(f"Failed to send request to {recipient_module}: {str(e)}")
            raise
        finally:
            # Clean up pending response
            with self._responses_lock:
                self.pending_responses.pop(correlation_id, None)
    
    async def send_response(
        self,
        sender_module: str,
        correlation_id: str,
        payload: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Send response to a request"""
        try:
            message_id = str(uuid.uuid4())
            metadata = MessageMetadata(
                message_id=message_id,
                correlation_id=correlation_id,
                sender_module=sender_module
            )
            
            response_payload = {
                "success": success,
                "data": payload,
                "error": error_message
            }
            
            message = Message(
                message_type=MessageType.RESPONSE,
                payload=response_payload,
                metadata=metadata,
                status=MessageStatus.COMPLETED if success else MessageStatus.FAILED,
                error_message=error_message
            )
            
            # Find and resolve pending response
            with self._responses_lock:
                if correlation_id in self.pending_responses:
                    future = self.pending_responses[correlation_id]
                    if not future.done():
                        if success:
                            future.set_result(payload)
                        else:
                            future.set_exception(Exception(error_message or "Request failed"))
                    
                    del self.pending_responses[correlation_id]
            
            self.metrics.record_message_sent(message)
            
        except Exception as e:
            logger.error(f"Failed to send response for correlation {correlation_id}: {str(e)}")
    
    async def publish_event(
        self,
        sender_module: str,
        topic: str,
        payload: Dict[str, Any],
        tags: Optional[Set[str]] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ):
        """Publish event to topic subscribers"""
        try:
            message_id = str(uuid.uuid4())
            metadata = MessageMetadata(
                message_id=message_id,
                sender_module=sender_module,
                topic=topic,
                tags=tags or set(),
                priority=priority
            )
            
            message = Message(
                message_type=MessageType.EVENT,
                payload=payload,
                metadata=metadata
            )
            
            await self._queue_message(message)
            self.metrics.record_message_sent(message)
            
            logger.debug(f"Published event to topic {topic} from {sender_module}")
            
        except Exception as e:
            logger.error(f"Failed to publish event to topic {topic}: {str(e)}")
    
    async def send_command(
        self,
        sender_module: str,
        recipient_module: str,
        command: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ):
        """Send command to specific module"""
        try:
            message_id = str(uuid.uuid4())
            metadata = MessageMetadata(
                message_id=message_id,
                sender_module=sender_module,
                recipient_module=recipient_module,
                priority=priority
            )
            
            command_payload = {
                "command": command,
                "data": payload
            }
            
            message = Message(
                message_type=MessageType.COMMAND,
                payload=command_payload,
                metadata=metadata
            )
            
            await self._queue_message(message)
            self.metrics.record_message_sent(message)
            
        except Exception as e:
            logger.error(f"Failed to send command {command} to {recipient_module}: {str(e)}")
    
    async def broadcast_message(
        self,
        sender_module: str,
        payload: Dict[str, Any],
        exclude_modules: Optional[Set[str]] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ):
        """Broadcast message to all registered modules"""
        try:
            message_id = str(uuid.uuid4())
            metadata = MessageMetadata(
                message_id=message_id,
                sender_module=sender_module,
                priority=priority,
                tags={"broadcast"}
            )
            
            message = Message(
                message_type=MessageType.BROADCAST,
                payload=payload,
                metadata=metadata
            )
            
            # Add exclusion filter if provided
            if exclude_modules:
                message.metadata.tags.add("exclude_modules")
                message.payload["_exclude_modules"] = list(exclude_modules)
            
            await self._queue_message(message)
            self.metrics.record_message_sent(message)
            
        except Exception as e:
            logger.error(f"Failed to broadcast message from {sender_module}: {str(e)}")
    
    # Private processing methods
    
    async def _queue_message(self, message: Message):
        """Queue message for processing based on priority"""
        try:
            priority_queue = self.message_queues[message.metadata.priority]
            await priority_queue.put(message)
            
            # Store message for persistence
            await self.storage.store_message(message)
            
        except Exception as e:
            logger.error(f"Failed to queue message {message.metadata.message_id}: {str(e)}")
            await self.dead_letter_queue.add_message(message, f"Queue error: {str(e)}")
    
    async def _process_messages_by_priority(self, priority: MessagePriority):
        """Process messages for a specific priority queue"""
        queue = self.message_queues[priority]
        
        while True:
            try:
                # Get message from queue
                message = await queue.get()
                
                # Check if message expired
                if message.is_expired():
                    logger.warning(f"Message {message.metadata.message_id} expired before processing")
                    self.metrics.record_timeout(message)
                    continue
                
                # Process message with semaphore protection
                async with self.processing_semaphore:
                    await self._process_message(message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message processing loop for priority {priority.name}: {str(e)}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _process_message(self, message: Message):
        """Process individual message"""
        start_time = time.time()
        
        try:
            message.status = MessageStatus.PROCESSING
            
            # Handle different message types
            if message.message_type == MessageType.REQUEST:
                await self._handle_request(message)
            elif message.message_type == MessageType.EVENT:
                await self._handle_event(message)
            elif message.message_type == MessageType.COMMAND:
                await self._handle_command(message)
            elif message.message_type == MessageType.BROADCAST:
                await self._handle_broadcast(message)
            
            message.status = MessageStatus.COMPLETED
            processing_time = (time.time() - start_time) * 1000
            message.processing_time_ms = processing_time
            
            self.metrics.record_message_processed(message, processing_time)
            
        except Exception as e:
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            processing_time = (time.time() - start_time) * 1000
            
            self.metrics.record_failure(message, str(e))
            
            # Handle retry logic
            if message.metadata.retry_count < message.metadata.max_retries:
                message.metadata.retry_count += 1
                message.status = MessageStatus.PENDING
                
                # Exponential backoff
                delay = min(2 ** message.metadata.retry_count, 60)  # Max 60 seconds
                await asyncio.sleep(delay)
                
                logger.info(f"Retrying message {message.metadata.message_id} (attempt {message.metadata.retry_count})")
                await self._queue_message(message)
            else:
                # Move to dead letter queue
                await self.dead_letter_queue.add_message(message, f"Max retries exceeded: {str(e)}")
            
            logger.error(f"Failed to process message {message.metadata.message_id}: {str(e)}")
        
        finally:
            # Clean up message from storage if completed
            if message.status in [MessageStatus.COMPLETED, MessageStatus.DEAD_LETTER]:
                await self.storage.delete_message(message.metadata.message_id)
    
    async def _handle_request(self, message: Message):
        """Handle request message"""
        recipient = message.metadata.recipient_module
        if not recipient:
            raise ValueError("Request message must have recipient module")
        
        # Find handlers for the recipient module
        key = f"{recipient}:{MessageType.REQUEST.value}"
        handlers = self.message_handlers.get(key, [])
        
        if not handlers:
            raise ValueError(f"No handlers found for module {recipient}")
        
        # Use circuit breaker for the recipient module
        circuit_breaker = self.circuit_breakers.get(recipient)
        if not circuit_breaker:
            raise ValueError(f"No circuit breaker found for module {recipient}")
        
        # Process request with first available handler
        handler = handlers[0]  # For now, use first handler
        
        try:
            result = await circuit_breaker.call(handler.handle_message, message)
            
            # Send response back
            await self.send_response(
                sender_module=recipient,
                correlation_id=message.metadata.correlation_id,
                payload=result,
                success=True
            )
            
        except Exception as e:
            # Send error response
            await self.send_response(
                sender_module=recipient,
                correlation_id=message.metadata.correlation_id,
                payload={},
                success=False,
                error_message=str(e)
            )
            raise
    
    async def _handle_event(self, message: Message):
        """Handle event message"""
        topic = message.metadata.topic
        if not topic:
            raise ValueError("Event message must have topic")
        
        # Find all subscribers for the topic
        subscribers = self.topic_subscribers.get(topic, [])
        
        if not subscribers:
            logger.debug(f"No subscribers for topic {topic}")
            return
        
        # Send event to all subscribers concurrently
        tasks = []
        for handler in subscribers:
            task = asyncio.create_task(self._handle_event_for_subscriber(handler, message))
            tasks.append(task)
        
        # Wait for all handlers to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any handler failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Event handler {i} failed for topic {topic}: {str(result)}")
    
    async def _handle_event_for_subscriber(self, handler: MessageHandler, message: Message):
        """Handle event for individual subscriber"""
        try:
            await handler.handle_message(message)
        except Exception as e:
            logger.error(f"Event handler failed: {str(e)}")
            # Don't re-raise to avoid affecting other handlers
    
    async def _handle_command(self, message: Message):
        """Handle command message"""
        recipient = message.metadata.recipient_module
        if not recipient:
            raise ValueError("Command message must have recipient module")
        
        # Similar to request handling but no response expected
        key = f"{recipient}:{MessageType.COMMAND.value}"
        handlers = self.message_handlers.get(key, [])
        
        if not handlers:
            raise ValueError(f"No command handlers found for module {recipient}")
        
        circuit_breaker = self.circuit_breakers.get(recipient)
        if not circuit_breaker:
            raise ValueError(f"No circuit breaker found for module {recipient}")
        
        handler = handlers[0]
        await circuit_breaker.call(handler.handle_message, message)
    
    async def _handle_broadcast(self, message: Message):
        """Handle broadcast message"""
        exclude_modules = set(message.payload.get("_exclude_modules", []))
        
        # Find all registered modules except excluded ones
        all_handlers = []
        for key, handlers in self.message_handlers.items():
            module_id = key.split(":")[0]
            if module_id not in exclude_modules and module_id != message.metadata.sender_module:
                all_handlers.extend(handlers)
        
        # Send broadcast to all handlers concurrently
        tasks = []
        for handler in all_handlers:
            task = asyncio.create_task(self._handle_broadcast_for_handler(handler, message))
            tasks.append(task)
        
        # Wait for all handlers
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _handle_broadcast_for_handler(self, handler: MessageHandler, message: Message):
        """Handle broadcast for individual handler"""
        try:
            await handler.handle_message(message)
        except Exception as e:
            logger.error(f"Broadcast handler failed: {str(e)}")
    
    async def _cleanup_expired_messages(self):
        """Background task to clean up expired messages"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up expired pending responses
                with self._responses_lock:
                    expired_correlations = []
                    for correlation_id, future in self.pending_responses.items():
                        if future.done():
                            expired_correlations.append(correlation_id)
                    
                    for correlation_id in expired_correlations:
                        del self.pending_responses[correlation_id]
                
                logger.debug(f"Cleaned up {len(expired_correlations)} expired response futures")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
    
    async def _rotate_metrics(self):
        """Background task to rotate metrics"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Reset metrics to prevent memory growth
                with self.metrics._metrics_lock:
                    # Keep only recent metrics
                    for metric_type in list(self.metrics.metrics.keys()):
                        metrics_list = self.metrics.metrics[metric_type]
                        if len(metrics_list) > 1000:
                            # Keep last 1000 entries
                            self.metrics.metrics[metric_type] = metrics_list[-1000:]
                
                logger.debug("Rotated message bus metrics")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics rotation: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current message bus metrics"""
        return {
            **self.metrics.get_performance_summary(),
            "active_handlers": len(self.message_handlers),
            "topic_subscribers": {topic: len(handlers) for topic, handlers in self.topic_subscribers.items()},
            "pending_responses": len(self.pending_responses),
            "circuit_breakers": {
                module: breaker.state.value 
                for module, breaker in self.circuit_breakers.items()
            },
            "queue_sizes": {
                priority.name: queue.qsize() 
                for priority, queue in self.message_queues.items()
            },
            "dead_letter_queue_size": len(self.dead_letter_queue.dead_messages)
        }


# Global instance
message_bus: Optional[InterModuleMessageBus] = None


def get_message_bus() -> InterModuleMessageBus:
    """Get the global message bus instance"""
    global message_bus
    if message_bus is None:
        raise RuntimeError("Message bus not initialized")
    return message_bus


async def initialize_message_bus(
    redis_client: Optional[aioredis.Redis] = None,
    audit_service: Optional[AuditService] = None,
    max_concurrent_messages: int = 1000
) -> InterModuleMessageBus:
    """Initialize the global message bus"""
    global message_bus
    if message_bus is None:
        message_bus = InterModuleMessageBus(
            redis_client=redis_client,
            audit_service=audit_service,
            max_concurrent_messages=max_concurrent_messages
        )
        await message_bus.start()
        logger.info(f"Global message bus initialized with {max_concurrent_messages} max concurrent messages")
    return message_bus


def message_handler(*message_types: MessageType, topics: Optional[List[str]] = None):
    """Decorator to mark methods as message handlers"""
    def decorator(func: Callable):
        func._message_types = list(message_types)
        func._topics = topics or []
        return func
    return decorator