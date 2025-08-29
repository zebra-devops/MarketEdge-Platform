"""
US-104: Event-Driven Workflow System and Event Sourcing

This module provides comprehensive event-driven architecture with workflow
orchestration, event sourcing, and event replay capabilities for inter-module
communication.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable, Union, Tuple, AsyncGenerator
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
from functools import wraps
import threading
import weakref
from collections import defaultdict, OrderedDict, deque
import hashlib
import pickle
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload
from redis import asyncio as aioredis

from ..models.modules import ModuleUsageLog
from ..core.database import get_db
from ..core.message_bus import (
    get_message_bus, 
    MessageHandler, 
    Message, 
    MessageType, 
    MessagePriority,
    MessageMetadata
)
from ..services.audit_service import AuditService

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events in the system"""
    DOMAIN_EVENT = "domain_event"         # Business domain events
    SYSTEM_EVENT = "system_event"         # System-level events
    WORKFLOW_EVENT = "workflow_event"     # Workflow orchestration events
    INTEGRATION_EVENT = "integration_event"  # External integration events
    NOTIFICATION_EVENT = "notification_event"  # User notification events
    AUDIT_EVENT = "audit_event"           # Security and audit events
    ERROR_EVENT = "error_event"           # Error and exception events


class EventStatus(Enum):
    """Status of event processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    REPLAYING = "replaying"
    ARCHIVED = "archived"


class WorkflowStatus(Enum):
    """Status of workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class EventMetadata:
    """Metadata for events"""
    event_id: str
    event_type: EventType
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    version: int = 1
    
    # Causation and correlation
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    # Source information
    source_module: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Timing
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Processing
    priority: MessagePriority = MessagePriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    
    # Categorization
    tags: Set[str] = field(default_factory=set)
    category: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['priority'] = self.priority.value
        data['occurred_at'] = self.occurred_at.isoformat()
        data['scheduled_for'] = self.scheduled_for.isoformat() if self.scheduled_for else None
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        data['tags'] = list(self.tags)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventMetadata':
        """Create from dictionary"""
        if 'event_type' in data:
            data['event_type'] = EventType(data['event_type'])
        if 'priority' in data:
            data['priority'] = MessagePriority(data['priority'])
        if 'occurred_at' in data:
            data['occurred_at'] = datetime.fromisoformat(data['occurred_at'])
        if 'scheduled_for' in data and data['scheduled_for']:
            data['scheduled_for'] = datetime.fromisoformat(data['scheduled_for'])
        if 'expires_at' in data and data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        if 'tags' in data:
            data['tags'] = set(data['tags'])
        return cls(**data)


@dataclass
class DomainEvent:
    """Domain event with payload and metadata"""
    name: str
    payload: Dict[str, Any]
    metadata: EventMetadata
    status: EventStatus = EventStatus.PENDING
    
    # Processing information
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    processing_duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'payload': self.payload,
            'metadata': self.metadata.to_dict(),
            'status': self.status.value,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processed_by': self.processed_by,
            'processing_duration_ms': self.processing_duration_ms,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DomainEvent':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            payload=data['payload'],
            metadata=EventMetadata.from_dict(data['metadata']),
            status=EventStatus(data['status']),
            processed_at=datetime.fromisoformat(data['processed_at']) if data.get('processed_at') else None,
            processed_by=data.get('processed_by'),
            processing_duration_ms=data.get('processing_duration_ms'),
            error_message=data.get('error_message')
        )


@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    step_id: str
    name: str
    handler: str  # Module and function to handle this step
    input_mapping: Dict[str, str] = field(default_factory=dict)
    output_mapping: Dict[str, str] = field(default_factory=dict)
    
    # Execution configuration
    timeout_seconds: int = 300
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    
    # Conditional execution
    condition: Optional[str] = None  # Expression to evaluate
    depends_on: List[str] = field(default_factory=list)  # Step dependencies
    
    # Compensation (for rollback)
    compensation_handler: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class WorkflowDefinition:
    """Definition of an event-driven workflow"""
    workflow_id: str
    name: str
    description: str
    version: str
    
    # Workflow configuration
    trigger_events: List[str]  # Events that trigger this workflow
    steps: List[WorkflowStep]
    
    # Execution settings
    parallel_execution: bool = False
    timeout_seconds: int = 3600
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['steps'] = [step.to_dict() for step in self.steps]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowDefinition':
        """Create from dictionary"""
        data = data.copy()
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'steps' in data:
            data['steps'] = [WorkflowStep.from_dict(step) for step in data['steps']]
        return cls(**data)


@dataclass
class WorkflowExecution:
    """Runtime execution of a workflow"""
    execution_id: str
    workflow_id: str
    trigger_event_id: str
    
    # State
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_index: int = 0
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    
    # Runtime data
    context: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    # Error handling
    error_message: Optional[str] = None
    compensation_executed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowExecution':
        """Create from dictionary"""
        data = data.copy()
        data['status'] = WorkflowStatus(data['status'])
        if 'started_at' in data and data['started_at']:
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if 'completed_at' in data and data['completed_at']:
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


class EventStore:
    """Event store for event sourcing with Redis and database persistence"""
    
    def __init__(
        self, 
        redis_client: Optional[aioredis.Redis] = None,
        max_memory_events: int = 10000
    ):
        self.redis = redis_client
        self.max_memory_events = max_memory_events
        
        # In-memory storage for when Redis is unavailable
        self.memory_store: OrderedDict[str, DomainEvent] = OrderedDict()
        self.aggregate_streams: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Event indexing for fast retrieval
        self.event_index: Dict[str, Set[str]] = defaultdict(set)  # category -> event_ids
        self.aggregate_index: Dict[str, List[str]] = defaultdict(list)  # aggregate_id -> event_ids
        
        self._store_lock = threading.RLock()
    
    async def append_event(self, event: DomainEvent) -> bool:
        """Append event to the event store"""
        try:
            with self._store_lock:
                # Store in memory
                if len(self.memory_store) >= self.max_memory_events:
                    # Remove oldest event
                    oldest_id, _ = self.memory_store.popitem(last=False)
                    self._remove_from_indexes(oldest_id)
                
                self.memory_store[event.metadata.event_id] = event
                self.memory_store.move_to_end(event.metadata.event_id)
                
                # Update indexes
                self._update_indexes(event)
                
                # Store in aggregate stream
                if event.metadata.aggregate_id:
                    self.aggregate_streams[event.metadata.aggregate_id].append(event.metadata.event_id)
            
            # Persist to Redis if available
            if self.redis:
                await self._persist_to_redis(event)
            
            # Persist to database for long-term storage
            await self._persist_to_database(event)
            
            logger.debug(f"Appended event {event.metadata.event_id} to event store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to append event {event.metadata.event_id}: {str(e)}")
            return False
    
    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        category: Optional[str] = None,
        from_version: int = 0,
        limit: int = 100
    ) -> List[DomainEvent]:
        """Retrieve events from the store"""
        try:
            events = []
            
            with self._store_lock:
                if aggregate_id:
                    # Get events for specific aggregate
                    event_ids = self.aggregate_index.get(aggregate_id, [])
                    for event_id in event_ids:
                        if event_id in self.memory_store:
                            event = self.memory_store[event_id]
                            if event.metadata.version >= from_version:
                                events.append(event)
                else:
                    # Get all events matching criteria
                    for event in self.memory_store.values():
                        if event_type and event.metadata.event_type != event_type:
                            continue
                        if category and event.metadata.category != category:
                            continue
                        if event.metadata.version >= from_version:
                            events.append(event)
            
            # Sort by version and limit
            events.sort(key=lambda e: e.metadata.version)
            return events[:limit]
            
        except Exception as e:
            logger.error(f"Failed to retrieve events: {str(e)}")
            return []
    
    async def get_event_stream(
        self, 
        aggregate_id: str, 
        from_version: int = 0
    ) -> AsyncGenerator[DomainEvent, None]:
        """Get event stream for aggregate"""
        try:
            event_ids = self.aggregate_index.get(aggregate_id, [])
            for event_id in event_ids:
                if event_id in self.memory_store:
                    event = self.memory_store[event_id]
                    if event.metadata.version >= from_version:
                        yield event
        except Exception as e:
            logger.error(f"Failed to get event stream for {aggregate_id}: {str(e)}")
    
    async def replay_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
        to_version: Optional[int] = None,
        event_handler: Optional[Callable[[DomainEvent], None]] = None
    ) -> List[DomainEvent]:
        """Replay events for an aggregate"""
        try:
            events = []
            async for event in self.get_event_stream(aggregate_id, from_version):
                if to_version and event.metadata.version > to_version:
                    break
                
                events.append(event)
                
                if event_handler:
                    try:
                        await event_handler(event)
                    except Exception as e:
                        logger.error(f"Event handler failed during replay: {str(e)}")
            
            logger.info(f"Replayed {len(events)} events for aggregate {aggregate_id}")
            return events
            
        except Exception as e:
            logger.error(f"Failed to replay events for {aggregate_id}: {str(e)}")
            return []
    
    async def create_snapshot(self, aggregate_id: str, snapshot_data: Dict[str, Any]) -> bool:
        """Create snapshot of aggregate state"""
        try:
            snapshot_key = f"snapshot:{aggregate_id}"
            snapshot = {
                'aggregate_id': aggregate_id,
                'data': snapshot_data,
                'version': len(self.aggregate_index.get(aggregate_id, [])),
                'created_at': datetime.utcnow().isoformat()
            }
            
            if self.redis:
                await self.redis.set(snapshot_key, json.dumps(snapshot))
            
            logger.debug(f"Created snapshot for aggregate {aggregate_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create snapshot for {aggregate_id}: {str(e)}")
            return False
    
    async def get_snapshot(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """Get snapshot of aggregate state"""
        try:
            snapshot_key = f"snapshot:{aggregate_id}"
            
            if self.redis:
                snapshot_data = await self.redis.get(snapshot_key)
                if snapshot_data:
                    return json.loads(snapshot_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get snapshot for {aggregate_id}: {str(e)}")
            return None
    
    # Private helper methods
    
    def _update_indexes(self, event: DomainEvent):
        """Update event indexes"""
        event_id = event.metadata.event_id
        
        # Category index
        if event.metadata.category:
            self.event_index[event.metadata.category].add(event_id)
        
        # Aggregate index
        if event.metadata.aggregate_id:
            self.aggregate_index[event.metadata.aggregate_id].append(event_id)
        
        # Tag index
        for tag in event.metadata.tags:
            self.event_index[f"tag:{tag}"].add(event_id)
    
    def _remove_from_indexes(self, event_id: str):
        """Remove event from indexes"""
        # Remove from all indexes
        for index_key, event_set in self.event_index.items():
            event_set.discard(event_id)
        
        # Remove from aggregate indexes
        for aggregate_id, event_list in self.aggregate_index.items():
            if event_id in event_list:
                event_list.remove(event_id)
    
    async def _persist_to_redis(self, event: DomainEvent):
        """Persist event to Redis"""
        try:
            event_key = f"event:{event.metadata.event_id}"
            event_data = json.dumps(event.to_dict())
            
            # Store event with TTL
            await self.redis.setex(event_key, 86400, event_data)  # 24 hours
            
            # Add to stream for aggregate
            if event.metadata.aggregate_id:
                stream_key = f"stream:{event.metadata.aggregate_id}"
                await self.redis.xadd(
                    stream_key,
                    {
                        'event_id': event.metadata.event_id,
                        'event_data': event_data
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to persist event to Redis: {str(e)}")
    
    async def _persist_to_database(self, event: DomainEvent):
        """Persist event to database for long-term storage"""
        try:
            # Store in module usage log table for now
            # In production, you'd have a dedicated events table
            async for db_session in get_db():
                try:
                    usage_log = ModuleUsageLog(
                        module_id=event.metadata.source_module or "event_system",
                        organisation_id=event.metadata.aggregate_id or "system",
                        user_id=event.metadata.user_id or "system",
                        action=f"EVENT:{event.name}",
                        context=event.payload,
                        success=event.status == EventStatus.PROCESSED
                    )
                    
                    db_session.add(usage_log)
                    await db_session.commit()
                    break
                    
                except Exception as e:
                    logger.error(f"Database error persisting event: {str(e)}")
                    await db_session.rollback()
                    break
                    
        except Exception as e:
            logger.error(f"Failed to persist event to database: {str(e)}")


class EventBus:
    """Event bus for publishing and subscribing to domain events"""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        
        # Event subscriptions
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.pattern_subscribers: List[Tuple[str, Callable]] = []
        
        # Processing queues
        self.event_queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in MessagePriority
        }
        
        # Background processing
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="event-bus")
        self.background_tasks: List[asyncio.Task] = []
        self.processing_semaphore = asyncio.Semaphore(100)
        
        self._subscribers_lock = threading.RLock()
    
    async def start(self):
        """Start event processing"""
        try:
            # Start event processing tasks for each priority
            for priority in MessagePriority:
                task = asyncio.create_task(
                    self._process_events_by_priority(priority)
                )
                self.background_tasks.append(task)
            
            logger.info("Event bus started")
            
        except Exception as e:
            logger.error(f"Failed to start event bus: {str(e)}")
            raise
    
    async def stop(self):
        """Stop event processing"""
        try:
            # Cancel all background tasks
            for task in self.background_tasks:
                task.cancel()
            
            if self.background_tasks:
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            # Shutdown executor
            self.executor.shutdown(wait=True, timeout=30)
            
            logger.info("Event bus stopped")
            
        except Exception as e:
            logger.error(f"Error stopping event bus: {str(e)}")
    
    def subscribe(self, event_name: str, handler: Callable[[DomainEvent], None]):
        """Subscribe to specific event"""
        with self._subscribers_lock:
            self.subscribers[event_name].append(handler)
        logger.debug(f"Subscribed to event: {event_name}")
    
    def subscribe_pattern(self, pattern: str, handler: Callable[[DomainEvent], None]):
        """Subscribe to events matching pattern"""
        with self._subscribers_lock:
            self.pattern_subscribers.append((pattern, handler))
        logger.debug(f"Subscribed to pattern: {pattern}")
    
    def unsubscribe(self, event_name: str, handler: Callable[[DomainEvent], None]):
        """Unsubscribe from event"""
        with self._subscribers_lock:
            if handler in self.subscribers[event_name]:
                self.subscribers[event_name].remove(handler)
        logger.debug(f"Unsubscribed from event: {event_name}")
    
    async def publish(self, event: DomainEvent) -> bool:
        """Publish event to subscribers"""
        try:
            # Store event first
            stored = await self.event_store.append_event(event)
            if not stored:
                logger.error(f"Failed to store event {event.metadata.event_id}")
                return False
            
            # Queue for processing
            priority = event.metadata.priority
            await self.event_queues[priority].put(event)
            
            logger.debug(f"Published event: {event.name} ({event.metadata.event_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.name}: {str(e)}")
            return False
    
    async def _process_events_by_priority(self, priority: MessagePriority):
        """Process events for specific priority queue"""
        queue = self.event_queues[priority]
        
        while True:
            try:
                # Get event from queue
                event = await queue.get()
                
                # Process with semaphore protection
                async with self.processing_semaphore:
                    await self._process_event(event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processing loop for priority {priority.name}: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_event(self, event: DomainEvent):
        """Process individual event"""
        start_time = time.time()
        
        try:
            event.status = EventStatus.PROCESSING
            
            # Find subscribers
            handlers = []
            
            with self._subscribers_lock:
                # Exact match subscribers
                handlers.extend(self.subscribers.get(event.name, []))
                
                # Pattern match subscribers
                import re
                for pattern, handler in self.pattern_subscribers:
                    if re.match(pattern, event.name):
                        handlers.append(handler)
            
            if not handlers:
                logger.debug(f"No handlers found for event {event.name}")
                event.status = EventStatus.PROCESSED
                return
            
            # Execute handlers concurrently
            tasks = []
            for handler in handlers:
                task = asyncio.create_task(self._execute_handler(handler, event))
                tasks.append(task)
            
            # Wait for all handlers
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for failures
            failures = [r for r in results if isinstance(r, Exception)]
            if failures:
                event.status = EventStatus.FAILED
                event.error_message = f"Handler failures: {[str(f) for f in failures[:3]]}"
                logger.error(f"Event {event.name} processing failed: {failures}")
            else:
                event.status = EventStatus.PROCESSED
                logger.debug(f"Event {event.name} processed successfully")
            
        except Exception as e:
            event.status = EventStatus.FAILED
            event.error_message = str(e)
            logger.error(f"Event {event.name} processing failed: {str(e)}")
        
        finally:
            # Update processing metadata
            event.processed_at = datetime.utcnow()
            event.processing_duration_ms = (time.time() - start_time) * 1000
    
    async def _execute_handler(self, handler: Callable, event: DomainEvent):
        """Execute individual event handler"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                # Run sync handler in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, handler, event)
        except Exception as e:
            logger.error(f"Event handler failed: {str(e)}")
            raise


class WorkflowEngine:
    """Workflow orchestration engine for event-driven workflows"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
        # Workflow storage
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
        # Event subscriptions for workflow triggers
        self.trigger_mappings: Dict[str, List[str]] = defaultdict(list)  # event -> workflow_ids
        
        # Execution queues
        self.execution_queue = asyncio.Queue()
        self.step_queue = asyncio.Queue()
        
        # Background processing
        self.background_tasks: List[asyncio.Task] = []
        
        self._workflows_lock = threading.RLock()
        
        # Subscribe to workflow events
        self.event_bus.subscribe_pattern(r".*", self._on_event_received)
    
    async def start(self):
        """Start workflow engine"""
        try:
            # Start workflow execution processor
            exec_task = asyncio.create_task(self._process_workflow_executions())
            self.background_tasks.append(exec_task)
            
            # Start step execution processor
            step_task = asyncio.create_task(self._process_workflow_steps())
            self.background_tasks.append(step_task)
            
            logger.info("Workflow engine started")
            
        except Exception as e:
            logger.error(f"Failed to start workflow engine: {str(e)}")
            raise
    
    async def stop(self):
        """Stop workflow engine"""
        try:
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
            
            if self.background_tasks:
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            logger.info("Workflow engine stopped")
            
        except Exception as e:
            logger.error(f"Error stopping workflow engine: {str(e)}")
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register workflow definition"""
        with self._workflows_lock:
            self.workflow_definitions[workflow.workflow_id] = workflow
            
            # Update trigger mappings
            for event_name in workflow.trigger_events:
                self.trigger_mappings[event_name].append(workflow.workflow_id)
        
        logger.info(f"Registered workflow: {workflow.name}")
    
    def unregister_workflow(self, workflow_id: str):
        """Unregister workflow definition"""
        with self._workflows_lock:
            workflow = self.workflow_definitions.pop(workflow_id, None)
            if workflow:
                # Clean up trigger mappings
                for event_name in workflow.trigger_events:
                    if workflow_id in self.trigger_mappings[event_name]:
                        self.trigger_mappings[event_name].remove(workflow_id)
        
        logger.info(f"Unregistered workflow: {workflow_id}")
    
    async def start_workflow(
        self, 
        workflow_id: str, 
        trigger_event: DomainEvent,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start workflow execution"""
        try:
            workflow = self.workflow_definitions.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            if not workflow.is_active:
                raise ValueError(f"Workflow {workflow_id} is not active")
            
            # Create execution
            execution_id = str(uuid.uuid4())
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                trigger_event_id=trigger_event.metadata.event_id,
                context=context or {},
                started_at=datetime.utcnow()
            )
            
            # Add trigger event data to context
            execution.context['trigger_event'] = trigger_event.payload
            execution.context['trigger_metadata'] = trigger_event.metadata.to_dict()
            
            # Store execution
            self.active_executions[execution_id] = execution
            
            # Queue for processing
            await self.execution_queue.put(execution_id)
            
            logger.info(f"Started workflow execution {execution_id} for workflow {workflow_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to start workflow {workflow_id}: {str(e)}")
            raise
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        execution = self.active_executions.get(execution_id)
        if execution:
            return execution.to_dict()
        return None
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel workflow execution"""
        try:
            execution = self.active_executions.get(execution_id)
            if execution:
                execution.status = WorkflowStatus.CANCELLED
                execution.completed_at = datetime.utcnow()
                
                if execution.started_at:
                    duration = execution.completed_at - execution.started_at
                    execution.duration_ms = duration.total_seconds() * 1000
                
                logger.info(f"Cancelled workflow execution {execution_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow {execution_id}: {str(e)}")
            return False
    
    async def _on_event_received(self, event: DomainEvent):
        """Handle incoming events for workflow triggers"""
        try:
            # Find workflows triggered by this event
            triggered_workflows = self.trigger_mappings.get(event.name, [])
            
            for workflow_id in triggered_workflows:
                try:
                    await self.start_workflow(workflow_id, event)
                except Exception as e:
                    logger.error(f"Failed to start workflow {workflow_id} from event {event.name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error handling event for workflow triggers: {str(e)}")
    
    async def _process_workflow_executions(self):
        """Process workflow executions"""
        while True:
            try:
                execution_id = await self.execution_queue.get()
                execution = self.active_executions.get(execution_id)
                
                if not execution:
                    continue
                
                if execution.status == WorkflowStatus.CANCELLED:
                    continue
                
                # Start workflow execution
                execution.status = WorkflowStatus.RUNNING
                
                # Queue first step for execution
                await self.step_queue.put((execution_id, 0))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing workflow executions: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_workflow_steps(self):
        """Process individual workflow steps"""
        while True:
            try:
                execution_id, step_index = await self.step_queue.get()
                execution = self.active_executions.get(execution_id)
                
                if not execution or execution.status != WorkflowStatus.RUNNING:
                    continue
                
                workflow = self.workflow_definitions.get(execution.workflow_id)
                if not workflow:
                    execution.status = WorkflowStatus.FAILED
                    execution.error_message = "Workflow definition not found"
                    continue
                
                if step_index >= len(workflow.steps):
                    # Workflow completed
                    execution.status = WorkflowStatus.COMPLETED
                    execution.completed_at = datetime.utcnow()
                    
                    if execution.started_at:
                        duration = execution.completed_at - execution.started_at
                        execution.duration_ms = duration.total_seconds() * 1000
                    
                    logger.info(f"Workflow execution {execution_id} completed")
                    continue
                
                # Execute current step
                step = workflow.steps[step_index]
                execution.current_step_index = step_index
                
                try:
                    await self._execute_workflow_step(execution, step)
                    
                    # Mark step as completed
                    execution.completed_steps.append(step.step_id)
                    
                    # Queue next step
                    await self.step_queue.put((execution_id, step_index + 1))
                    
                except Exception as e:
                    logger.error(f"Step {step.name} failed in execution {execution_id}: {str(e)}")
                    
                    execution.failed_steps.append(step.step_id)
                    execution.status = WorkflowStatus.FAILED
                    execution.error_message = str(e)
                    execution.completed_at = datetime.utcnow()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing workflow steps: {str(e)}")
                await asyncio.sleep(1)
    
    async def _execute_workflow_step(self, execution: WorkflowExecution, step: WorkflowStep):
        """Execute individual workflow step"""
        try:
            # Check dependencies
            for dep_step_id in step.depends_on:
                if dep_step_id not in execution.completed_steps:
                    raise Exception(f"Step {step.name} depends on incomplete step {dep_step_id}")
            
            # Evaluate condition if present
            if step.condition:
                if not self._evaluate_condition(step.condition, execution.context):
                    logger.info(f"Step {step.name} skipped due to condition: {step.condition}")
                    return
            
            # Prepare step input
            step_input = self._map_step_input(step, execution.context)
            
            # Execute step handler
            # This would call the actual module function
            # For now, simulate step execution
            step_result = await self._call_step_handler(step.handler, step_input)
            
            # Map step output to context
            if step.output_mapping:
                for context_key, result_key in step.output_mapping.items():
                    if result_key in step_result:
                        execution.context[context_key] = step_result[result_key]
            
            # Store step result
            execution.step_results[step.step_id] = step_result
            
            logger.debug(f"Step {step.name} executed successfully in execution {execution.execution_id}")
            
        except Exception as e:
            logger.error(f"Step {step.name} execution failed: {str(e)}")
            raise
    
    def _map_step_input(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Map context data to step input"""
        step_input = {}
        
        for input_key, context_key in step.input_mapping.items():
            if context_key in context:
                step_input[input_key] = context[context_key]
        
        return step_input
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate step condition (simplified implementation)"""
        try:
            # This would use a proper expression evaluator in production
            # For now, just check for simple existence conditions
            if condition.startswith("exists(") and condition.endswith(")"):
                key = condition[7:-1]  # Remove "exists(" and ")"
                return key in context
            
            return True  # Default to true for unknown conditions
            
        except Exception:
            return False
    
    async def _call_step_handler(self, handler: str, step_input: Dict[str, Any]) -> Dict[str, Any]:
        """Call step handler (mock implementation)"""
        try:
            # This would resolve and call the actual module function
            # For now, return mock result
            await asyncio.sleep(0.1)  # Simulate processing
            
            return {
                'success': True,
                'result': f'Executed {handler}',
                'input_received': step_input
            }
            
        except Exception as e:
            logger.error(f"Step handler {handler} failed: {str(e)}")
            raise


class EventDrivenSystem:
    """
    US-104: Complete event-driven system with workflows and event sourcing
    
    Integrates event store, event bus, and workflow engine for comprehensive
    event-driven architecture supporting inter-module communication.
    """
    
    def __init__(
        self,
        redis_client: Optional[aioredis.Redis] = None,
        audit_service: Optional[AuditService] = None
    ):
        self.audit_service = audit_service
        
        # Core components
        self.event_store = EventStore(redis_client)
        self.event_bus = EventBus(self.event_store)
        self.workflow_engine = WorkflowEngine(self.event_bus)
        
        # System metrics
        self.metrics = {
            'events_published': 0,
            'events_processed': 0,
            'workflows_started': 0,
            'workflows_completed': 0,
            'workflows_failed': 0
        }
        
        logger.info("Event-driven system initialized")
    
    async def start(self):
        """Start the event-driven system"""
        try:
            await self.event_bus.start()
            await self.workflow_engine.start()
            
            logger.info("Event-driven system started")
            
        except Exception as e:
            logger.error(f"Failed to start event-driven system: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the event-driven system"""
        try:
            await self.workflow_engine.stop()
            await self.event_bus.stop()
            
            logger.info("Event-driven system stopped")
            
        except Exception as e:
            logger.error(f"Error stopping event-driven system: {str(e)}")
    
    async def publish_event(
        self,
        event_name: str,
        payload: Dict[str, Any],
        source_module: str,
        aggregate_id: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        tags: Optional[Set[str]] = None
    ) -> str:
        """Publish domain event"""
        try:
            # Create event metadata
            metadata = EventMetadata(
                event_id=str(uuid.uuid4()),
                event_type=EventType.DOMAIN_EVENT,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                source_module=source_module,
                user_id=user_id,
                correlation_id=correlation_id,
                priority=priority,
                tags=tags or set()
            )
            
            # Create domain event
            event = DomainEvent(
                name=event_name,
                payload=payload,
                metadata=metadata
            )
            
            # Publish event
            success = await self.event_bus.publish(event)
            if success:
                self.metrics['events_published'] += 1
                
                # Audit log
                if self.audit_service:
                    await self.audit_service.log_action(
                        user_id=user_id or "system",
                        action="EVENT_PUBLISHED",
                        resource_type="domain_event",
                        resource_id=event.metadata.event_id,
                        description=f"Published event {event_name}",
                        metadata={
                            'event_name': event_name,
                            'source_module': source_module,
                            'aggregate_id': aggregate_id
                        }
                    )
            
            return event.metadata.event_id
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_name}: {str(e)}")
            raise
    
    def subscribe_to_event(self, event_name: str, handler: Callable[[DomainEvent], None]):
        """Subscribe to domain event"""
        self.event_bus.subscribe(event_name, handler)
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register workflow definition"""
        self.workflow_engine.register_workflow(workflow)
    
    async def start_workflow(
        self, 
        workflow_id: str, 
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Manually start workflow"""
        try:
            # Create a manual trigger event
            trigger_event = DomainEvent(
                name="workflow.manual_trigger",
                payload=context or {},
                metadata=EventMetadata(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.WORKFLOW_EVENT,
                    source_module="workflow_engine",
                    user_id=user_id
                )
            )
            
            execution_id = await self.workflow_engine.start_workflow(
                workflow_id, trigger_event, context
            )
            
            self.metrics['workflows_started'] += 1
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to start workflow {workflow_id}: {str(e)}")
            raise
    
    async def get_event_history(
        self,
        aggregate_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[DomainEvent]:
        """Get event history"""
        return await self.event_store.get_events(
            aggregate_id=aggregate_id,
            event_type=event_type,
            limit=limit
        )
    
    async def replay_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
        event_handler: Optional[Callable[[DomainEvent], None]] = None
    ) -> List[DomainEvent]:
        """Replay events for aggregate"""
        return await self.event_store.replay_events(
            aggregate_id, from_version, event_handler
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return {
            **self.metrics,
            'active_workflows': len(self.workflow_engine.active_executions),
            'workflow_definitions': len(self.workflow_engine.workflow_definitions),
            'event_subscribers': sum(len(subs) for subs in self.event_bus.subscribers.values()),
            'pattern_subscribers': len(self.event_bus.pattern_subscribers)
        }


# Global instance
event_system: Optional[EventDrivenSystem] = None


def get_event_system() -> EventDrivenSystem:
    """Get the global event-driven system instance"""
    global event_system
    if event_system is None:
        raise RuntimeError("Event-driven system not initialized")
    return event_system


async def initialize_event_system(
    redis_client: Optional[aioredis.Redis] = None,
    audit_service: Optional[AuditService] = None
) -> EventDrivenSystem:
    """Initialize the global event-driven system"""
    global event_system
    if event_system is None:
        event_system = EventDrivenSystem(
            redis_client=redis_client,
            audit_service=audit_service
        )
        await event_system.start()
        logger.info("Global event-driven system initialized")
    return event_system