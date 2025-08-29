"""
US-104: Module Communication Integration Layer

This module integrates the message bus, discovery service, and event system
with the existing module registry and authentication context systems to provide
a complete inter-module communication solution.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import threading
from functools import wraps

from redis import asyncio as aioredis

from ..models.user import User
from ..models.modules import ModuleType, ModuleStatus
from ..core.module_registry import (
    get_module_registry,
    ModuleRegistry,
    ModuleMetadata,
    ModuleRegistration
)
from ..core.auth_context import (
    get_auth_context_manager,
    AuthenticationContextManager,
    AuthenticationContext
)
from ..core.message_bus import (
    get_message_bus,
    initialize_message_bus,
    InterModuleMessageBus,
    MessageHandler,
    Message,
    MessageType,
    MessagePriority
)
from ..core.module_discovery import (
    get_discovery_service,
    initialize_discovery_service,
    ModuleDiscoveryService,
    ModuleCapability,
    CapabilityType,
    DiscoveryQuery
)
from ..core.event_system import (
    get_event_system,
    initialize_event_system,
    EventDrivenSystem,
    DomainEvent,
    WorkflowDefinition,
    EventType
)
from ..services.audit_service import AuditService

logger = logging.getLogger(__name__)


class CommunicationProtocol(Enum):
    """Communication protocols supported"""
    REQUEST_RESPONSE = "request_response"
    PUBLISH_SUBSCRIBE = "publish_subscribe"
    EVENT_DRIVEN = "event_driven"
    WORKFLOW = "workflow"
    BROADCAST = "broadcast"


class SecurityLevel(Enum):
    """Security levels for inter-module communication"""
    NONE = "none"                    # No security
    BASIC = "basic"                  # Basic authentication
    AUTHENTICATED = "authenticated"  # User authentication required
    AUTHORIZED = "authorized"        # Permission-based authorization
    ENCRYPTED = "encrypted"          # End-to-end encryption


@dataclass
class CommunicationContext:
    """Context for inter-module communication"""
    
    # Source and target
    source_module: str
    target_module: Optional[str] = None
    
    # Authentication
    auth_context: Optional[AuthenticationContext] = None
    user: Optional[User] = None
    
    # Security
    security_level: SecurityLevel = SecurityLevel.AUTHENTICATED
    required_permissions: List[str] = field(default_factory=list)
    
    # Protocol
    protocol: CommunicationProtocol = CommunicationProtocol.REQUEST_RESPONSE
    
    # Metadata
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timeout_seconds: int = 30
    priority: MessagePriority = MessagePriority.NORMAL
    
    # Tracing
    trace_enabled: bool = True
    parent_trace_id: Optional[str] = None


class ModuleCommunicationHandler(MessageHandler):
    """Base handler for module communication with integrated security and context"""
    
    def __init__(
        self,
        module_id: str,
        supported_protocols: List[CommunicationProtocol],
        security_level: SecurityLevel = SecurityLevel.AUTHENTICATED
    ):
        self.module_id = module_id
        self.supported_protocols = supported_protocols
        self.security_level = security_level
        self.auth_context_manager = get_auth_context_manager()
        
        # Handler registry
        self.request_handlers: Dict[str, Callable] = {}
        self.event_handlers: Dict[str, Callable] = {}
        self.command_handlers: Dict[str, Callable] = {}
    
    def get_supported_message_types(self) -> List[MessageType]:
        """Get supported message types based on protocols"""
        message_types = []
        
        if CommunicationProtocol.REQUEST_RESPONSE in self.supported_protocols:
            message_types.extend([MessageType.REQUEST, MessageType.RESPONSE])
        
        if CommunicationProtocol.PUBLISH_SUBSCRIBE in self.supported_protocols:
            message_types.append(MessageType.EVENT)
        
        if CommunicationProtocol.BROADCAST in self.supported_protocols:
            message_types.append(MessageType.BROADCAST)
        
        if CommunicationProtocol.WORKFLOW in self.supported_protocols:
            message_types.append(MessageType.COMMAND)
        
        return message_types
    
    def get_topics(self) -> List[str]:
        """Get topics this handler subscribes to"""
        return [
            f"module.{self.module_id}",
            f"module.{self.module_id}.*",
            "broadcast.*",
            "system.*"
        ]
    
    async def handle_message(self, message: Message) -> Any:
        """Handle incoming message with security and context validation"""
        try:
            # Create communication context
            comm_context = await self._create_communication_context(message)
            
            # Validate security
            await self._validate_security(comm_context, message)
            
            # Route message based on type
            if message.message_type == MessageType.REQUEST:
                return await self._handle_request(message, comm_context)
            elif message.message_type == MessageType.EVENT:
                return await self._handle_event(message, comm_context)
            elif message.message_type == MessageType.COMMAND:
                return await self._handle_command(message, comm_context)
            elif message.message_type == MessageType.BROADCAST:
                return await self._handle_broadcast(message, comm_context)
            else:
                raise ValueError(f"Unsupported message type: {message.message_type}")
                
        except Exception as e:
            logger.error(f"Message handling failed in module {self.module_id}: {str(e)}")
            raise
    
    def register_request_handler(self, action: str, handler: Callable):
        """Register handler for request actions"""
        self.request_handlers[action] = handler
    
    def register_event_handler(self, event_name: str, handler: Callable):
        """Register handler for events"""
        self.event_handlers[event_name] = handler
    
    def register_command_handler(self, command: str, handler: Callable):
        """Register handler for commands"""
        self.command_handlers[command] = handler
    
    async def _create_communication_context(self, message: Message) -> CommunicationContext:
        """Create communication context from message"""
        context = CommunicationContext(
            source_module=message.metadata.sender_module,
            target_module=message.metadata.recipient_module,
            correlation_id=message.metadata.correlation_id or str(uuid.uuid4()),
            priority=message.metadata.priority
        )
        
        # Extract auth context if available
        if hasattr(message, 'auth_context_id'):
            auth_context = await self.auth_context_manager.get_context(
                session_id=message.auth_context_id
            )
            if auth_context:
                context.auth_context = auth_context
                context.user = auth_context.user
        
        return context
    
    async def _validate_security(self, context: CommunicationContext, message: Message):
        """Validate security requirements"""
        if self.security_level == SecurityLevel.NONE:
            return
        
        if self.security_level in [SecurityLevel.AUTHENTICATED, SecurityLevel.AUTHORIZED, SecurityLevel.ENCRYPTED]:
            if not context.auth_context:
                raise PermissionError("Authentication context required")
            
            # Validate context is still valid
            is_valid = await self.auth_context_manager.validate_context(
                context.auth_context,
                self.module_id
            )
            if not is_valid:
                raise PermissionError("Invalid or expired authentication context")
        
        if self.security_level == SecurityLevel.AUTHORIZED:
            # Check module-specific permissions
            if not context.auth_context.permissions.intersection(set(context.required_permissions)):
                raise PermissionError("Insufficient permissions for inter-module communication")
    
    async def _handle_request(self, message: Message, context: CommunicationContext) -> Any:
        """Handle request message"""
        action = message.payload.get('action')
        if not action:
            raise ValueError("Request message must specify action")
        
        handler = self.request_handlers.get(action)
        if not handler:
            raise ValueError(f"No handler registered for action: {action}")
        
        # Execute handler with context
        if asyncio.iscoroutinefunction(handler):
            return await handler(message.payload.get('data', {}), context)
        else:
            return handler(message.payload.get('data', {}), context)
    
    async def _handle_event(self, message: Message, context: CommunicationContext) -> Any:
        """Handle event message"""
        event_name = message.payload.get('event_name') or message.metadata.topic
        if not event_name:
            raise ValueError("Event message must specify event name or topic")
        
        handler = self.event_handlers.get(event_name)
        if handler:
            if asyncio.iscoroutinefunction(handler):
                await handler(message.payload, context)
            else:
                handler(message.payload, context)
    
    async def _handle_command(self, message: Message, context: CommunicationContext) -> Any:
        """Handle command message"""
        command = message.payload.get('command')
        if not command:
            raise ValueError("Command message must specify command")
        
        handler = self.command_handlers.get(command)
        if not handler:
            raise ValueError(f"No handler registered for command: {command}")
        
        if asyncio.iscoroutinefunction(handler):
            return await handler(message.payload.get('data', {}), context)
        else:
            return handler(message.payload.get('data', {}), context)
    
    async def _handle_broadcast(self, message: Message, context: CommunicationContext) -> Any:
        """Handle broadcast message"""
        # Process broadcast for all registered handlers
        for handler in list(self.event_handlers.values()):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message.payload, context)
                else:
                    handler(message.payload, context)
            except Exception as e:
                logger.error(f"Broadcast handler failed: {str(e)}")


class InterModuleCommunicationService:
    """
    US-104: Complete inter-module communication service
    
    Provides unified interface for all module communication patterns with
    integrated security, discovery, and monitoring.
    """
    
    def __init__(
        self,
        redis_client: Optional[aioredis.Redis] = None,
        audit_service: Optional[AuditService] = None
    ):
        self.redis_client = redis_client
        self.audit_service = audit_service
        
        # Core components (will be initialized in start())
        self.message_bus: Optional[InterModuleMessageBus] = None
        self.discovery_service: Optional[ModuleDiscoveryService] = None
        self.event_system: Optional[EventDrivenSystem] = None
        self.auth_context_manager: Optional[AuthenticationContextManager] = None
        self.module_registry: Optional[ModuleRegistry] = None
        
        # Communication handlers by module
        self.module_handlers: Dict[str, ModuleCommunicationHandler] = {}
        
        # Security policies
        self.security_policies: Dict[str, Dict[str, Any]] = {}
        
        # Communication metrics
        self.metrics = {
            'messages_sent': 0,
            'messages_received': 0,
            'events_published': 0,
            'workflows_triggered': 0,
            'security_violations': 0,
            'communication_errors': 0
        }
        
        self._handlers_lock = threading.RLock()
        
        logger.info("Inter-module communication service initialized")
    
    async def start(self):
        """Start the communication service"""
        try:
            # Initialize core components
            self.message_bus = await initialize_message_bus(
                self.redis_client, 
                self.audit_service
            )
            
            self.discovery_service = await initialize_discovery_service(
                self.audit_service
            )
            
            self.event_system = await initialize_event_system(
                self.redis_client,
                self.audit_service
            )
            
            # Get existing components
            self.auth_context_manager = get_auth_context_manager()
            self.module_registry = get_module_registry()
            
            # Register system event handlers
            self.event_system.subscribe_to_event(
                "module.registered", 
                self._on_module_registered
            )
            
            self.event_system.subscribe_to_event(
                "module.deregistered", 
                self._on_module_deregistered
            )
            
            logger.info("Inter-module communication service started")
            
        except Exception as e:
            logger.error(f"Failed to start communication service: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the communication service"""
        try:
            if self.event_system:
                await self.event_system.stop()
            
            if self.message_bus:
                await self.message_bus.stop()
            
            logger.info("Inter-module communication service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping communication service: {str(e)}")
    
    def register_module_handler(
        self, 
        module_id: str, 
        handler: ModuleCommunicationHandler
    ):
        """Register communication handler for a module"""
        with self._handlers_lock:
            self.module_handlers[module_id] = handler
            
            # Register with message bus
            if self.message_bus:
                self.message_bus.register_handler(handler, module_id)
        
        logger.info(f"Registered communication handler for module {module_id}")
    
    def unregister_module_handler(self, module_id: str):
        """Unregister communication handler for a module"""
        with self._handlers_lock:
            handler = self.module_handlers.pop(module_id, None)
            
            if handler and self.message_bus:
                self.message_bus.unregister_handler(handler, module_id)
        
        logger.info(f"Unregistered communication handler for module {module_id}")
    
    async def send_request(
        self,
        source_module: str,
        target_module: str,
        action: str,
        data: Dict[str, Any],
        auth_context: Optional[AuthenticationContext] = None,
        timeout_seconds: int = 30,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Any:
        """
        Send request to another module
        
        Args:
            source_module: Module sending the request
            target_module: Module to receive the request
            action: Action to perform
            data: Request data
            auth_context: Authentication context
            timeout_seconds: Request timeout
            priority: Message priority
            
        Returns:
            Response from target module
        """
        try:
            # Validate modules are registered and accessible
            await self._validate_module_communication(
                source_module, target_module, auth_context
            )
            
            # Prepare request payload
            payload = {
                'action': action,
                'data': data
            }
            
            # Add auth context if provided
            correlation_id = str(uuid.uuid4())
            if auth_context:
                payload['auth_context_id'] = auth_context.session_id
                
                # Update auth context with module access
                auth_context.update_access(target_module)
                await self.auth_context_manager.cache.set_context(auth_context)
            
            # Send request via message bus
            response = await self.message_bus.send_request(
                sender_module=source_module,
                recipient_module=target_module,
                payload=payload,
                timeout_seconds=timeout_seconds,
                priority=priority,
                correlation_id=correlation_id
            )
            
            self.metrics['messages_sent'] += 1
            
            # Audit log
            if self.audit_service:
                await self.audit_service.log_action(
                    user_id=auth_context.user_id if auth_context else "system",
                    action="MODULE_REQUEST",
                    resource_type="inter_module_communication",
                    resource_id=correlation_id,
                    description=f"Request from {source_module} to {target_module}: {action}",
                    metadata={
                        'source_module': source_module,
                        'target_module': target_module,
                        'action': action,
                        'success': True
                    }
                )
            
            return response
            
        except Exception as e:
            self.metrics['communication_errors'] += 1
            logger.error(f"Request from {source_module} to {target_module} failed: {str(e)}")
            
            # Audit log failure
            if self.audit_service:
                await self.audit_service.log_action(
                    user_id=auth_context.user_id if auth_context else "system",
                    action="MODULE_REQUEST_FAILED",
                    resource_type="inter_module_communication",
                    resource_id=str(uuid.uuid4()),
                    description=f"Failed request from {source_module} to {target_module}: {action}",
                    metadata={
                        'source_module': source_module,
                        'target_module': target_module,
                        'action': action,
                        'error': str(e)
                    }
                )
            
            raise
    
    async def publish_event(
        self,
        source_module: str,
        event_name: str,
        data: Dict[str, Any],
        auth_context: Optional[AuthenticationContext] = None,
        aggregate_id: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """
        Publish event for other modules to consume
        
        Args:
            source_module: Module publishing the event
            event_name: Name of the event
            data: Event data
            auth_context: Authentication context
            aggregate_id: Optional aggregate ID for event sourcing
            tags: Optional tags for event categorization
            priority: Message priority
            
        Returns:
            Event ID
        """
        try:
            event_id = await self.event_system.publish_event(
                event_name=event_name,
                payload=data,
                source_module=source_module,
                aggregate_id=aggregate_id,
                user_id=auth_context.user_id if auth_context else None,
                priority=priority,
                tags=tags
            )
            
            self.metrics['events_published'] += 1
            
            return event_id
            
        except Exception as e:
            self.metrics['communication_errors'] += 1
            logger.error(f"Event publication from {source_module} failed: {str(e)}")
            raise
    
    async def subscribe_to_event(
        self,
        module_id: str,
        event_name: str,
        handler: Callable[[DomainEvent, CommunicationContext], None]
    ):
        """Subscribe module to specific event"""
        def wrapped_handler(domain_event: DomainEvent):
            # Create communication context
            context = CommunicationContext(
                source_module=domain_event.metadata.source_module,
                target_module=module_id,
                correlation_id=domain_event.metadata.correlation_id
            )
            
            # Call original handler
            return handler(domain_event, context)
        
        self.event_system.subscribe_to_event(event_name, wrapped_handler)
        
        logger.info(f"Module {module_id} subscribed to event {event_name}")
    
    async def discover_modules(
        self,
        query: DiscoveryQuery,
        auth_context: Optional[AuthenticationContext] = None
    ) -> List[Dict[str, Any]]:
        """Discover available modules and capabilities"""
        try:
            # Apply security filtering based on auth context
            if auth_context:
                # Filter based on user's module access
                if query.exclude_modules is None:
                    query.exclude_modules = set()
                
                # Add modules user doesn't have access to
                user_accessible_modules = set(auth_context.module_access.keys())
                all_modules = await self.module_registry.get_registered_modules()
                
                for module in all_modules:
                    if module.metadata.id not in user_accessible_modules:
                        query.exclude_modules.add(module.metadata.id)
            
            # Perform discovery
            result = await self.discovery_service.discover_modules(query)
            return result.modules
            
        except Exception as e:
            logger.error(f"Module discovery failed: {str(e)}")
            raise
    
    async def negotiate_capability(
        self,
        consumer_module: str,
        provider_module: str,
        capability_requirements: Dict[str, Any],
        auth_context: Optional[AuthenticationContext] = None
    ) -> Dict[str, Any]:
        """Negotiate capability usage between modules"""
        try:
            # Validate module communication is allowed
            await self._validate_module_communication(
                consumer_module, provider_module, auth_context
            )
            
            # Perform capability negotiation
            result = await self.discovery_service.negotiate_capability(
                consumer_module=consumer_module,
                provider_module=provider_module,
                capability_requirements=capability_requirements
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Capability negotiation failed: {str(e)}")
            raise
    
    async def start_workflow(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
        auth_context: Optional[AuthenticationContext] = None
    ) -> str:
        """Start workflow execution"""
        try:
            execution_id = await self.event_system.start_workflow(
                workflow_id=workflow_id,
                context=context,
                user_id=auth_context.user_id if auth_context else None
            )
            
            self.metrics['workflows_triggered'] += 1
            
            return execution_id
            
        except Exception as e:
            self.metrics['communication_errors'] += 1
            logger.error(f"Workflow start failed: {str(e)}")
            raise
    
    def set_security_policy(
        self, 
        module_id: str, 
        policy: Dict[str, Any]
    ):
        """Set security policy for module communication"""
        self.security_policies[module_id] = policy
        logger.info(f"Set security policy for module {module_id}")
    
    def get_communication_metrics(self) -> Dict[str, Any]:
        """Get communication metrics"""
        base_metrics = self.metrics.copy()
        
        # Add component-specific metrics
        if self.message_bus:
            base_metrics.update(self.message_bus.get_metrics())
        
        if self.discovery_service:
            base_metrics.update(self.discovery_service.get_discovery_metrics())
        
        if self.event_system:
            base_metrics.update(self.event_system.get_metrics())
        
        return base_metrics
    
    # Private helper methods
    
    async def _validate_module_communication(
        self,
        source_module: str,
        target_module: str,
        auth_context: Optional[AuthenticationContext]
    ):
        """Validate that module communication is allowed"""
        # Check if modules are registered
        source_reg = await self.module_registry.get_module_registration(source_module)
        if not source_reg:
            raise ValueError(f"Source module {source_module} not registered")
        
        target_reg = await self.module_registry.get_module_registration(target_module)
        if not target_reg:
            raise ValueError(f"Target module {target_module} not registered")
        
        # Check module status
        if source_reg.status != ModuleStatus.ACTIVE:
            raise ValueError(f"Source module {source_module} is not active")
        
        if target_reg.status != ModuleStatus.ACTIVE:
            raise ValueError(f"Target module {target_module} is not active")
        
        # Check security policies
        source_policy = self.security_policies.get(source_module, {})
        target_policy = self.security_policies.get(target_module, {})
        
        # Validate auth context if required
        if target_policy.get('require_authentication', True) and not auth_context:
            self.metrics['security_violations'] += 1
            raise PermissionError(f"Authentication required for communication with {target_module}")
        
        if auth_context:
            # Check module access permissions
            target_access = auth_context.module_access.get(target_module)
            if not target_access:
                self.metrics['security_violations'] += 1
                raise PermissionError(f"No access to target module {target_module}")
    
    async def _on_module_registered(self, event: DomainEvent):
        """Handle module registration event"""
        try:
            module_id = event.payload.get('module_id')
            if module_id:
                logger.info(f"Module {module_id} registered, updating communication service")
                
                # Auto-advertise basic capabilities
                await self._auto_advertise_capabilities(module_id, event.payload)
                
        except Exception as e:
            logger.error(f"Error handling module registration event: {str(e)}")
    
    async def _on_module_deregistered(self, event: DomainEvent):
        """Handle module deregistration event"""
        try:
            module_id = event.payload.get('module_id')
            if module_id:
                logger.info(f"Module {module_id} deregistered, cleaning up communication service")
                
                # Clean up handler
                self.unregister_module_handler(module_id)
                
                # Clean up capabilities
                self.discovery_service.remove_capability(module_id, f"{module_id}_basic")
                
        except Exception as e:
            logger.error(f"Error handling module deregistration event: {str(e)}")
    
    async def _auto_advertise_capabilities(self, module_id: str, module_data: Dict[str, Any]):
        """Auto-advertise basic capabilities for newly registered module"""
        try:
            # Create basic capability advertisement
            capability = ModuleCapability(
                capability_id=f"{module_id}_basic",
                name=f"Basic {module_id} Capability",
                capability_type=CapabilityType.API_ENDPOINT,
                description=f"Basic API capability for {module_id}",
                version="1.0.0",
                input_schema={'type': 'object'},
                output_schema={'type': 'object'},
                is_available=True
            )
            
            self.discovery_service.advertise_capability(module_id, capability)
            
        except Exception as e:
            logger.error(f"Error auto-advertising capabilities for {module_id}: {str(e)}")


# Global instance
communication_service: Optional[InterModuleCommunicationService] = None


def get_communication_service() -> InterModuleCommunicationService:
    """Get the global communication service instance"""
    global communication_service
    if communication_service is None:
        raise RuntimeError("Communication service not initialized")
    return communication_service


async def initialize_communication_service(
    redis_client: Optional[aioredis.Redis] = None,
    audit_service: Optional[AuditService] = None
) -> InterModuleCommunicationService:
    """Initialize the global communication service"""
    global communication_service
    if communication_service is None:
        communication_service = InterModuleCommunicationService(
            redis_client=redis_client,
            audit_service=audit_service
        )
        await communication_service.start()
        logger.info("Global inter-module communication service initialized")
    return communication_service


def module_communication_handler(
    supported_protocols: List[CommunicationProtocol],
    security_level: SecurityLevel = SecurityLevel.AUTHENTICATED
):
    """Decorator to create module communication handler"""
    def decorator(cls):
        # Add communication capabilities to the class
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Add communication handler if module_id is available
            if hasattr(self, 'module_id'):
                self.comm_handler = ModuleCommunicationHandler(
                    self.module_id,
                    supported_protocols,
                    security_level
                )
                
                # Auto-register with communication service
                try:
                    comm_service = get_communication_service()
                    comm_service.register_module_handler(self.module_id, self.comm_handler)
                except RuntimeError:
                    # Communication service not initialized yet
                    pass
        
        cls.__init__ = new_init
        cls._communication_protocols = supported_protocols
        cls._security_level = security_level
        
        return cls
    
    return decorator


def request_handler(action: str):
    """Decorator to register request handler method"""
    def decorator(method):
        method._is_request_handler = True
        method._action = action
        return method
    return decorator


def event_handler(event_name: str):
    """Decorator to register event handler method"""
    def decorator(method):
        method._is_event_handler = True
        method._event_name = event_name
        return method
    return decorator


def command_handler(command: str):
    """Decorator to register command handler method"""
    def decorator(method):
        method._is_command_handler = True
        method._command = command
        return method
    return decorator