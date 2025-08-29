"""
Test suite for US-104: Inter-Module Communication

Comprehensive test coverage for message bus, discovery service, event system,
and integrated communication patterns.
"""

import asyncio
import json
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, AsyncMock, patch

from app.core.message_bus import (
    InterModuleMessageBus,
    Message,
    MessageType,
    MessagePriority,
    MessageMetadata,
    MessageHandler,
    CircuitBreaker,
    CircuitBreakerConfig,
    MessageBusMetrics
)
from app.core.module_discovery import (
    ModuleDiscoveryService,
    ModuleCapability,
    CapabilityType,
    DiscoveryQuery,
    ContractValidator,
    VersionCompatibilityChecker
)
from app.core.event_system import (
    EventDrivenSystem,
    DomainEvent,
    EventMetadata,
    EventType,
    WorkflowDefinition,
    WorkflowStep,
    EventStore
)
from app.core.module_communication import (
    InterModuleCommunicationService,
    ModuleCommunicationHandler,
    CommunicationProtocol,
    SecurityLevel,
    CommunicationContext
)
from app.models.modules import ModuleType, ModuleStatus
from app.services.audit_service import AuditService


class TestMessageBus:
    """Test message bus functionality"""
    
    @pytest.fixture
    async def message_bus(self):
        """Create message bus for testing"""
        bus = InterModuleMessageBus(max_concurrent_messages=10)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest.fixture
    def sample_message(self):
        """Create sample message for testing"""
        metadata = MessageMetadata(
            message_id=str(uuid.uuid4()),
            sender_module="test_sender",
            recipient_module="test_recipient",
            priority=MessagePriority.NORMAL
        )
        
        return Message(
            message_type=MessageType.REQUEST,
            payload={"action": "test", "data": {"key": "value"}},
            metadata=metadata
        )
    
    @pytest.fixture
    def mock_handler(self):
        """Create mock message handler"""
        class MockHandler(MessageHandler):
            def __init__(self):
                self.received_messages = []
            
            def get_supported_message_types(self):
                return [MessageType.REQUEST, MessageType.EVENT]
            
            def get_topics(self):
                return ["test.topic"]
            
            async def handle_message(self, message: Message):
                self.received_messages.append(message)
                return {"status": "handled", "message_id": message.metadata.message_id}
        
        return MockHandler()
    
    async def test_message_bus_initialization(self, message_bus):
        """Test message bus initializes correctly"""
        assert message_bus is not None
        assert len(message_bus.background_tasks) > 0
        assert message_bus.processing_semaphore._value == 10
    
    async def test_handler_registration(self, message_bus, mock_handler):
        """Test message handler registration"""
        module_id = "test_module"
        
        # Register handler
        message_bus.register_handler(mock_handler, module_id)
        
        # Verify handler is registered
        assert module_id in message_bus.circuit_breakers
        assert f"{module_id}:{MessageType.REQUEST.value}" in message_bus.message_handlers
        assert "test.topic" in message_bus.topic_subscribers
    
    async def test_request_response_pattern(self, message_bus, mock_handler):
        """Test request-response communication pattern"""
        module_id = "test_module"
        message_bus.register_handler(mock_handler, module_id)
        
        # Send request
        response = await message_bus.send_request(
            sender_module="client",
            recipient_module=module_id,
            payload={"action": "test", "data": {"key": "value"}},
            timeout_seconds=5
        )
        
        # Verify response
        assert response is not None
        assert response.get("status") == "handled"
        assert len(mock_handler.received_messages) == 1
    
    async def test_publish_subscribe_pattern(self, message_bus, mock_handler):
        """Test publish-subscribe communication pattern"""
        module_id = "test_module"
        message_bus.register_handler(mock_handler, module_id)
        
        # Publish event
        await message_bus.publish_event(
            sender_module="publisher",
            topic="test.topic",
            payload={"event": "test_event", "data": {"key": "value"}}
        )
        
        # Wait for event processing
        await asyncio.sleep(0.1)
        
        # Verify event was received
        assert len(mock_handler.received_messages) >= 1
        event_message = mock_handler.received_messages[-1]
        assert event_message.message_type == MessageType.EVENT
        assert event_message.payload["event"] == "test_event"
    
    async def test_circuit_breaker_functionality(self):
        """Test circuit breaker fault tolerance"""
        config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=1)
        circuit_breaker = CircuitBreaker(config)
        
        # Mock function that always fails
        async def failing_function():
            raise Exception("Test failure")
        
        # First failure
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_function)
        
        # Second failure (should open circuit)
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_function)
        
        # Circuit should be open now
        assert circuit_breaker.state.value == "open"
        
        # Next call should be rejected
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await circuit_breaker.call(failing_function)
    
    async def test_dead_letter_queue(self, message_bus, sample_message):
        """Test dead letter queue functionality"""
        # Create message that will fail processing
        sample_message.metadata.max_retries = 0
        
        # Mock a failing handler
        class FailingHandler(MessageHandler):
            def get_supported_message_types(self):
                return [MessageType.REQUEST]
            
            def get_topics(self):
                return []
            
            async def handle_message(self, message: Message):
                raise Exception("Handler failure")
        
        # Register failing handler
        handler = FailingHandler()
        message_bus.register_handler(handler, sample_message.metadata.recipient_module)
        
        # Process message (should fail and go to DLQ)
        await message_bus._queue_message(sample_message)
        await asyncio.sleep(0.1)  # Wait for processing
        
        # Check dead letter queue
        dead_messages = await message_bus.dead_letter_queue.get_dead_messages()
        assert len(dead_messages) > 0
    
    async def test_metrics_collection(self, message_bus, mock_handler):
        """Test metrics collection"""
        module_id = "test_module"
        message_bus.register_handler(mock_handler, module_id)
        
        # Send some messages
        await message_bus.send_request(
            sender_module="client",
            recipient_module=module_id,
            payload={"action": "test"},
            timeout_seconds=5
        )
        
        # Check metrics
        metrics = message_bus.get_metrics()
        assert metrics["total_messages_sent"] > 0
        assert metrics["total_messages_processed"] >= 0
        assert "success_rate" in metrics


class TestModuleDiscovery:
    """Test module discovery and capability negotiation"""
    
    @pytest.fixture
    def discovery_service(self):
        """Create discovery service for testing"""
        return ModuleDiscoveryService()
    
    @pytest.fixture
    def sample_capability(self):
        """Create sample capability"""
        return ModuleCapability(
            capability_id="test_capability",
            name="Test Capability",
            capability_type=CapabilityType.API_ENDPOINT,
            description="A test capability",
            version="1.0.0",
            input_schema={"type": "object", "required": ["input"]},
            output_schema={"type": "object", "required": ["result"]},
            is_available=True
        )
    
    def test_capability_advertisement(self, discovery_service, sample_capability):
        """Test capability advertisement"""
        module_id = "test_module"
        
        # Advertise capability
        discovery_service.advertise_capability(module_id, sample_capability)
        
        # Verify capability is advertised
        capabilities = discovery_service.get_module_capabilities(module_id)
        assert len(capabilities) == 1
        assert capabilities[0].capability_id == "test_capability"
    
    async def test_module_discovery_by_type(self, discovery_service):
        """Test module discovery by capability type"""
        # Mock module registry
        with patch('app.core.module_discovery.get_module_registry') as mock_registry:
            mock_registration = Mock()
            mock_registration.metadata.id = "test_module"
            mock_registration.metadata.name = "Test Module"
            mock_registration.metadata.version = "1.0.0"
            mock_registration.metadata.module_type = ModuleType.CORE
            mock_registration.metadata.tags = ["test"]
            mock_registration.status = ModuleStatus.ACTIVE
            mock_registration.health.value = "healthy"
            
            mock_registry.return_value.get_registered_modules.return_value = [mock_registration]
            
            # Advertise capability
            capability = ModuleCapability(
                capability_id="api_capability",
                name="API Capability",
                capability_type=CapabilityType.API_ENDPOINT,
                description="API capability",
                version="1.0.0"
            )
            discovery_service.advertise_capability("test_module", capability)
            
            # Create discovery query
            query = DiscoveryQuery(
                capability_types=[CapabilityType.API_ENDPOINT],
                max_results=10
            )
            
            # Perform discovery
            result = await discovery_service.discover_modules(query)
            
            # Verify results
            assert result.total_found == 1
            assert len(result.modules) == 1
            assert result.modules[0]['module_id'] == "test_module"
    
    async def test_capability_negotiation(self, discovery_service, sample_capability):
        """Test capability negotiation between modules"""
        provider_module = "provider_module"
        consumer_module = "consumer_module"
        
        # Advertise capability
        discovery_service.advertise_capability(provider_module, sample_capability)
        
        # Define capability requirements
        requirements = {
            "capability_type": CapabilityType.API_ENDPOINT.value,
            "version": "1.0.0",
            "input_schema": {"type": "object", "required": ["input"]},
            "output_schema": {"type": "object", "required": ["result"]}
        }
        
        # Negotiate capability
        result = await discovery_service.negotiate_capability(
            consumer_module, provider_module, requirements
        )
        
        # Verify negotiation success
        assert result["success"] is True
        assert "contract_id" in result
        assert len(result["matching_capabilities"]) == 1
    
    def test_version_compatibility_checking(self):
        """Test version compatibility checking"""
        checker = VersionCompatibilityChecker()
        
        # Test compatible versions
        compatibility = checker.check_compatibility("1.0.0", "1.0.1", "test_module")
        assert compatibility.value == "compatible"
        
        # Test backward compatibility
        compatibility = checker.check_compatibility("1.0.0", "1.1.0", "test_module")
        assert compatibility.value == "backward_compatible"
        
        # Test breaking changes
        compatibility = checker.check_compatibility("2.0.0", "1.0.0", "test_module")
        assert compatibility.value == "breaking_changes"
    
    async def test_contract_validation(self, sample_capability):
        """Test contract validation"""
        from app.core.module_discovery import ModuleContract, ContractType
        
        validator = ContractValidator()
        
        # Create test contract
        contract = ModuleContract(
            contract_id="test_contract",
            name="Test Contract",
            contract_type=ContractType.API_SPECIFICATION,
            version="1.0.0",
            provider_module="provider",
            consumer_module="consumer",
            specification={
                "input_schema": {"type": "object", "required": ["input"]},
                "output_schema": {"type": "object", "required": ["result"]},
                "required_capabilities": [CapabilityType.API_ENDPOINT.value]
            }
        )
        
        # Validate contract
        result = await validator.validate_contract(
            contract, [sample_capability], {}
        )
        
        # Verify validation
        assert result["valid"] is True
        assert len(result["errors"]) == 0


class TestEventSystem:
    """Test event-driven system functionality"""
    
    @pytest.fixture
    async def event_system(self):
        """Create event system for testing"""
        system = EventDrivenSystem()
        await system.start()
        yield system
        await system.stop()
    
    @pytest.fixture
    def sample_event(self):
        """Create sample domain event"""
        metadata = EventMetadata(
            event_id=str(uuid.uuid4()),
            event_type=EventType.DOMAIN_EVENT,
            source_module="test_module",
            aggregate_id="test_aggregate"
        )
        
        return DomainEvent(
            name="test.event",
            payload={"data": "test_data"},
            metadata=metadata
        )
    
    async def test_event_publishing_and_subscription(self, event_system):
        """Test event publishing and subscription"""
        received_events = []
        
        def event_handler(event: DomainEvent):
            received_events.append(event)
        
        # Subscribe to event
        event_system.subscribe_to_event("test.event", event_handler)
        
        # Publish event
        event_id = await event_system.publish_event(
            event_name="test.event",
            payload={"data": "test_data"},
            source_module="test_module"
        )
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0].name == "test.event"
        assert received_events[0].payload["data"] == "test_data"
    
    async def test_event_store_functionality(self):
        """Test event store operations"""
        event_store = EventStore(max_memory_events=100)
        
        # Create test event
        metadata = EventMetadata(
            event_id=str(uuid.uuid4()),
            event_type=EventType.DOMAIN_EVENT,
            aggregate_id="test_aggregate",
            version=1
        )
        
        event = DomainEvent(
            name="test.event",
            payload={"data": "test"},
            metadata=metadata
        )
        
        # Append event
        success = await event_store.append_event(event)
        assert success is True
        
        # Retrieve events
        events = await event_store.get_events(aggregate_id="test_aggregate")
        assert len(events) == 1
        assert events[0].name == "test.event"
    
    async def test_event_replay(self):
        """Test event replay functionality"""
        event_store = EventStore(max_memory_events=100)
        aggregate_id = "test_aggregate"
        
        # Create multiple events
        for i in range(3):
            metadata = EventMetadata(
                event_id=str(uuid.uuid4()),
                event_type=EventType.DOMAIN_EVENT,
                aggregate_id=aggregate_id,
                version=i + 1
            )
            
            event = DomainEvent(
                name=f"test.event.{i}",
                payload={"sequence": i},
                metadata=metadata
            )
            
            await event_store.append_event(event)
        
        # Replay events
        replayed_events = []
        
        async def replay_handler(event: DomainEvent):
            replayed_events.append(event)
        
        events = await event_store.replay_events(
            aggregate_id, 
            from_version=0,
            event_handler=replay_handler
        )
        
        # Verify replay
        assert len(events) == 3
        assert len(replayed_events) == 3
        assert replayed_events[0].name == "test.event.0"
        assert replayed_events[2].name == "test.event.2"
    
    async def test_workflow_execution(self, event_system):
        """Test workflow definition and execution"""
        # Create workflow definition
        workflow = WorkflowDefinition(
            workflow_id="test_workflow",
            name="Test Workflow",
            description="A test workflow",
            version="1.0.0",
            trigger_events=["workflow.start"],
            steps=[
                WorkflowStep(
                    step_id="step1",
                    name="First Step",
                    handler="test_module.handle_step",
                    input_mapping={"input": "trigger_data"},
                    output_mapping={"result": "step1_result"}
                ),
                WorkflowStep(
                    step_id="step2",
                    name="Second Step",
                    handler="test_module.handle_step2",
                    input_mapping={"input": "step1_result"},
                    depends_on=["step1"]
                )
            ]
        )
        
        # Register workflow
        event_system.register_workflow(workflow)
        
        # Start workflow
        execution_id = await event_system.start_workflow(
            "test_workflow",
            context={"trigger_data": "test"}
        )
        
        # Verify workflow started
        assert execution_id is not None
        
        # Check workflow status
        await asyncio.sleep(0.1)  # Wait for processing
        metrics = event_system.get_metrics()
        assert metrics["workflows_started"] >= 1


class TestIntegratedCommunication:
    """Test integrated communication service"""
    
    @pytest.fixture
    async def communication_service(self):
        """Create communication service for testing"""
        with patch('app.core.module_communication.get_module_registry'), \
             patch('app.core.module_communication.get_auth_context_manager'):
            
            service = InterModuleCommunicationService()
            await service.start()
            yield service
            await service.stop()
    
    @pytest.fixture
    def mock_auth_context(self):
        """Create mock authentication context"""
        from app.core.auth_context import AuthenticationContext
        from app.models.user import User, UserRole
        
        user = Mock(spec=User)
        user.id = "test_user"
        user.organisation_id = "test_org"
        user.role = UserRole.USER
        user.is_active = True
        
        context = AuthenticationContext(
            user_id="test_user",
            user=user,
            session_id="test_session",
            organisation_id="test_org",
            access_token="test_token"
        )
        
        # Add module access
        context.module_access["target_module"] = "authenticated"
        
        return context
    
    @pytest.fixture
    def mock_handler(self):
        """Create mock communication handler"""
        handler = ModuleCommunicationHandler(
            module_id="test_module",
            supported_protocols=[CommunicationProtocol.REQUEST_RESPONSE],
            security_level=SecurityLevel.AUTHENTICATED
        )
        
        # Register test handlers
        async def test_request_handler(data, context):
            return {"status": "success", "received_data": data}
        
        handler.register_request_handler("test_action", test_request_handler)
        
        return handler
    
    async def test_module_handler_registration(self, communication_service, mock_handler):
        """Test module handler registration"""
        module_id = "test_module"
        
        # Register handler
        communication_service.register_module_handler(module_id, mock_handler)
        
        # Verify registration
        assert module_id in communication_service.module_handlers
    
    @pytest.mark.skip(reason="Requires full integration setup")
    async def test_authenticated_request(self, communication_service, mock_handler, mock_auth_context):
        """Test authenticated inter-module request"""
        module_id = "test_module"
        communication_service.register_module_handler(module_id, mock_handler)
        
        # Mock module validation
        with patch.object(communication_service, '_validate_module_communication'):
            response = await communication_service.send_request(
                source_module="client_module",
                target_module=module_id,
                action="test_action",
                data={"key": "value"},
                auth_context=mock_auth_context,
                timeout_seconds=5
            )
            
            # Verify response
            assert response is not None
            assert response.get("status") == "success"
    
    async def test_security_validation(self, mock_handler, mock_auth_context):
        """Test security validation in message handling"""
        # Create message with auth context
        metadata = MessageMetadata(
            message_id=str(uuid.uuid4()),
            sender_module="client",
            recipient_module="test_module"
        )
        
        message = Message(
            message_type=MessageType.REQUEST,
            payload={
                "action": "test_action",
                "data": {"key": "value"},
                "auth_context_id": mock_auth_context.session_id
            },
            metadata=metadata
        )
        
        # Mock auth context manager
        with patch.object(mock_handler, 'auth_context_manager') as mock_acm:
            mock_acm.get_context.return_value = mock_auth_context
            mock_acm.validate_context.return_value = True
            
            # Handle message
            result = await mock_handler.handle_message(message)
            
            # Verify result
            assert result is not None
            assert result.get("status") == "success"
    
    async def test_communication_metrics(self, communication_service):
        """Test communication metrics collection"""
        # Get initial metrics
        metrics = communication_service.get_communication_metrics()
        
        # Verify metrics structure
        assert "messages_sent" in metrics
        assert "messages_received" in metrics
        assert "events_published" in metrics
        assert "workflows_triggered" in metrics
        assert "security_violations" in metrics
        assert "communication_errors" in metrics
    
    async def test_decorator_functionality(self):
        """Test communication decorators"""
        from app.core.module_communication import (
            module_communication_handler,
            request_handler,
            event_handler
        )
        
        @module_communication_handler(
            supported_protocols=[CommunicationProtocol.REQUEST_RESPONSE],
            security_level=SecurityLevel.BASIC
        )
        class TestModule:
            def __init__(self):
                self.module_id = "test_decorated_module"
            
            @request_handler("decorated_action")
            async def handle_decorated_request(self, data, context):
                return {"handled": True, "data": data}
            
            @event_handler("decorated.event")
            async def handle_decorated_event(self, event_data, context):
                pass
        
        # Create instance
        module = TestModule()
        
        # Verify decorator added communication capabilities
        assert hasattr(module, 'comm_handler')
        assert module.comm_handler.module_id == "test_decorated_module"
        assert len(module.comm_handler.supported_protocols) == 1


class TestPerformanceAndReliability:
    """Test performance and reliability features"""
    
    async def test_concurrent_message_processing(self):
        """Test concurrent message processing limits"""
        bus = InterModuleMessageBus(max_concurrent_messages=2)
        await bus.start()
        
        try:
            # Verify semaphore limit
            assert bus.processing_semaphore._value == 2
            
            # Acquire semaphore to test limit
            async with bus.processing_semaphore:
                async with bus.processing_semaphore:
                    # Both slots taken
                    assert bus.processing_semaphore._value == 0
        
        finally:
            await bus.stop()
    
    async def test_message_persistence(self):
        """Test message persistence and recovery"""
        from app.core.message_bus import MessageStorage
        
        storage = MessageStorage(max_memory_messages=10)
        
        # Create test message
        metadata = MessageMetadata(
            message_id=str(uuid.uuid4()),
            sender_module="test"
        )
        
        message = Message(
            message_type=MessageType.EVENT,
            payload={"data": "test"},
            metadata=metadata
        )
        
        # Store message
        await storage.store_message(message)
        
        # Retrieve message
        retrieved = await storage.retrieve_message(metadata.message_id)
        
        # Verify persistence
        assert retrieved is not None
        assert retrieved.metadata.message_id == metadata.message_id
        assert retrieved.payload["data"] == "test"
    
    async def test_memory_bounds_enforcement(self):
        """Test memory bounds are enforced"""
        storage = MessageStorage(max_memory_messages=2)
        
        # Add messages beyond limit
        for i in range(5):
            metadata = MessageMetadata(message_id=f"msg_{i}", sender_module="test")
            message = Message(MessageType.EVENT, {"seq": i}, metadata)
            await storage.store_message(message)
        
        # Verify memory bounds
        assert len(storage.memory_storage) <= 2
        
        # Verify oldest messages were evicted
        assert "msg_0" not in storage.memory_storage
        assert "msg_1" not in storage.memory_storage
        assert "msg_4" in storage.memory_storage
    
    async def test_timeout_handling(self):
        """Test message timeout handling"""
        bus = InterModuleMessageBus()
        await bus.start()
        
        try:
            # Create handler that takes too long
            class SlowHandler(MessageHandler):
                def get_supported_message_types(self):
                    return [MessageType.REQUEST]
                
                def get_topics(self):
                    return []
                
                async def handle_message(self, message):
                    await asyncio.sleep(2)  # Longer than timeout
                    return {"status": "too_late"}
            
            handler = SlowHandler()
            bus.register_handler(handler, "slow_module")
            
            # Send request with short timeout
            with pytest.raises(Exception, match="timed out"):
                await bus.send_request(
                    sender_module="client",
                    recipient_module="slow_module",
                    payload={"action": "slow_action"},
                    timeout_seconds=1
                )
        
        finally:
            await bus.stop()


@pytest.mark.asyncio
async def test_full_integration_scenario():
    """Test complete integration scenario"""
    # This would be a comprehensive test that exercises all components
    # together in a realistic scenario
    
    # Mock all required services
    with patch('app.core.module_communication.get_module_registry'), \
         patch('app.core.module_communication.get_auth_context_manager'), \
         patch('app.core.message_bus.get_db'):
        
        # Initialize communication service
        comm_service = InterModuleCommunicationService()
        await comm_service.start()
        
        try:
            # Create test modules
            producer = ModuleCommunicationHandler(
                "producer_module",
                [CommunicationProtocol.EVENT_DRIVEN],
                SecurityLevel.BASIC
            )
            
            consumer = ModuleCommunicationHandler(
                "consumer_module",
                [CommunicationProtocol.EVENT_DRIVEN],
                SecurityLevel.BASIC
            )
            
            # Register modules
            comm_service.register_module_handler("producer_module", producer)
            comm_service.register_module_handler("consumer_module", consumer)
            
            # Test event-driven communication
            received_events = []
            
            def event_handler(event_data, context):
                received_events.append(event_data)
            
            consumer.register_event_handler("test.integration.event", event_handler)
            
            # Publish event
            await comm_service.publish_event(
                source_module="producer_module",
                event_name="test.integration.event",
                data={"integration": "test", "timestamp": datetime.utcnow().isoformat()}
            )
            
            # Wait for processing
            await asyncio.sleep(0.2)
            
            # Verify integration
            metrics = comm_service.get_communication_metrics()
            assert metrics["events_published"] >= 1
            
        finally:
            await comm_service.stop()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])