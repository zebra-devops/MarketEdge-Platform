"""
US-104: Module Discovery and Capability Negotiation

This module provides capability advertising, module discovery protocols,
version negotiation, and contract testing between modules for the
inter-module communication system.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import threading
import weakref
from collections import defaultdict, OrderedDict
import re
import hashlib

from ..models.modules import ModuleType, ModuleStatus
from ..core.module_registry import get_module_registry, ModuleMetadata, ModuleRegistration
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


class CapabilityType(Enum):
    """Types of capabilities modules can advertise"""
    API_ENDPOINT = "api_endpoint"
    EVENT_HANDLER = "event_handler"
    DATA_PROCESSOR = "data_processor"
    INTEGRATION = "integration"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    STORAGE = "storage"
    COMPUTATION = "computation"
    VISUALIZATION = "visualization"
    NOTIFICATION = "notification"


class ContractType(Enum):
    """Types of contracts between modules"""
    DATA_SCHEMA = "data_schema"
    API_SPECIFICATION = "api_specification"
    EVENT_SCHEMA = "event_schema"
    INTEGRATION_CONTRACT = "integration_contract"


class CompatibilityLevel(Enum):
    """Levels of compatibility between module versions"""
    COMPATIBLE = "compatible"          # Fully compatible
    BACKWARD_COMPATIBLE = "backward_compatible"  # New version supports old clients
    FORWARD_COMPATIBLE = "forward_compatible"    # Old version supports new clients
    BREAKING_CHANGES = "breaking_changes"        # Not compatible, requires migration
    UNKNOWN = "unknown"               # Compatibility not determined


@dataclass
class ModuleCapability:
    """Represents a capability provided by a module"""
    capability_id: str
    name: str
    capability_type: CapabilityType
    description: str
    version: str
    
    # Interface specification
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    error_schema: Dict[str, Any] = field(default_factory=dict)
    
    # Requirements and constraints
    required_permissions: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    performance_characteristics: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    tags: Set[str] = field(default_factory=set)
    documentation_url: Optional[str] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    # Availability
    is_available: bool = True
    availability_schedule: Optional[Dict[str, Any]] = None
    health_check_endpoint: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['capability_type'] = self.capability_type.value
        data['tags'] = list(self.tags)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModuleCapability':
        """Create from dictionary"""
        if 'capability_type' in data:
            data['capability_type'] = CapabilityType(data['capability_type'])
        if 'tags' in data:
            data['tags'] = set(data['tags'])
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class ModuleContract:
    """Contract specification between modules"""
    contract_id: str
    name: str
    contract_type: ContractType
    version: str
    
    # Contract parties
    provider_module: str
    consumer_module: str
    
    # Contract specification
    specification: Dict[str, Any]
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    
    # Validation rules
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    compatibility_constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    is_active: bool = True
    last_validated: Optional[datetime] = None
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['contract_type'] = self.contract_type.value
        data['last_validated'] = self.last_validated.isoformat() if self.last_validated else None
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModuleContract':
        """Create from dictionary"""
        if 'contract_type' in data:
            data['contract_type'] = ContractType(data['contract_type'])
        if 'last_validated' in data and data['last_validated']:
            data['last_validated'] = datetime.fromisoformat(data['last_validated'])
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class DiscoveryQuery:
    """Query for discovering modules and capabilities"""
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Query criteria
    module_types: Optional[List[ModuleType]] = None
    capability_types: Optional[List[CapabilityType]] = None
    tags: Optional[Set[str]] = None
    version_constraints: Optional[Dict[str, str]] = None
    
    # Requirements
    required_permissions: Optional[List[str]] = None
    performance_requirements: Optional[Dict[str, Any]] = None
    availability_requirements: Optional[Dict[str, Any]] = None
    
    # Filtering
    exclude_modules: Optional[Set[str]] = None
    only_available: bool = True
    only_healthy: bool = True
    
    # Response preferences
    include_examples: bool = False
    include_health_status: bool = False
    max_results: int = 100


@dataclass
class DiscoveryResult:
    """Result of a discovery query"""
    query_id: str
    
    # Results
    modules: List[Dict[str, Any]] = field(default_factory=list)
    capabilities: List[ModuleCapability] = field(default_factory=list)
    
    # Metadata
    total_found: int = 0
    query_duration_ms: float = 0
    cached: bool = False
    
    created_at: datetime = field(default_factory=datetime.utcnow)


class VersionCompatibilityChecker:
    """Check version compatibility between modules"""
    
    def __init__(self):
        self.compatibility_cache: Dict[str, CompatibilityLevel] = {}
    
    def check_compatibility(
        self, 
        required_version: str, 
        available_version: str,
        module_id: str
    ) -> CompatibilityLevel:
        """
        Check if available version is compatible with required version
        
        Args:
            required_version: Version required by consumer
            available_version: Version provided by producer
            module_id: Module identifier for caching
            
        Returns:
            CompatibilityLevel indicating compatibility
        """
        cache_key = f"{module_id}:{required_version}:{available_version}"
        
        # Check cache first
        if cache_key in self.compatibility_cache:
            return self.compatibility_cache[cache_key]
        
        try:
            compatibility = self._analyze_compatibility(required_version, available_version)
            self.compatibility_cache[cache_key] = compatibility
            return compatibility
            
        except Exception as e:
            logger.error(f"Error checking version compatibility: {str(e)}")
            return CompatibilityLevel.UNKNOWN
    
    def _analyze_compatibility(self, required: str, available: str) -> CompatibilityLevel:
        """Analyze semantic version compatibility"""
        try:
            # Parse semantic versions
            req_parts = self._parse_version(required)
            avail_parts = self._parse_version(available)
            
            if not req_parts or not avail_parts:
                return CompatibilityLevel.UNKNOWN
            
            req_major, req_minor, req_patch = req_parts
            avail_major, avail_minor, avail_patch = avail_parts
            
            # Major version compatibility
            if avail_major > req_major:
                # New major version might have breaking changes
                return CompatibilityLevel.BACKWARD_COMPATIBLE
            elif avail_major < req_major:
                # Old major version is likely incompatible
                return CompatibilityLevel.BREAKING_CHANGES
            
            # Same major version
            if avail_minor > req_minor:
                # New minor version should be backward compatible
                return CompatibilityLevel.BACKWARD_COMPATIBLE
            elif avail_minor < req_minor:
                # Old minor version might not have required features
                return CompatibilityLevel.FORWARD_COMPATIBLE
            
            # Same major and minor version
            if avail_patch >= req_patch:
                # Same or newer patch version
                return CompatibilityLevel.COMPATIBLE
            else:
                # Older patch version might have bugs
                return CompatibilityLevel.FORWARD_COMPATIBLE
                
        except Exception:
            return CompatibilityLevel.UNKNOWN
    
    def _parse_version(self, version: str) -> Optional[Tuple[int, int, int]]:
        """Parse semantic version string"""
        try:
            # Remove pre-release and build metadata
            version = re.sub(r'[-+].*', '', version)
            parts = version.split('.')
            
            if len(parts) >= 3:
                major = int(parts[0])
                minor = int(parts[1])
                patch = int(parts[2])
                return (major, minor, patch)
            
        except (ValueError, IndexError):
            pass
        
        return None


class ContractValidator:
    """Validate contracts between modules"""
    
    def __init__(self):
        self.validation_cache: Dict[str, Dict[str, Any]] = {}
    
    async def validate_contract(
        self, 
        contract: ModuleContract, 
        provider_capabilities: List[ModuleCapability],
        consumer_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate contract between provider and consumer
        
        Args:
            contract: Contract to validate
            provider_capabilities: Capabilities offered by provider
            consumer_requirements: Requirements from consumer
            
        Returns:
            Validation results with pass/fail status and details
        """
        cache_key = self._get_validation_cache_key(contract, provider_capabilities, consumer_requirements)
        
        # Check cache first
        if cache_key in self.validation_cache:
            cached_result = self.validation_cache[cache_key]
            if datetime.utcnow() - datetime.fromisoformat(cached_result['validated_at']) < timedelta(hours=1):
                return cached_result
        
        validation_result = {
            'contract_id': contract.contract_id,
            'valid': True,
            'errors': [],
            'warnings': [],
            'validated_at': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        try:
            # Schema compatibility check
            schema_check = await self._validate_schema_compatibility(contract, provider_capabilities)
            validation_result['checks']['schema_compatibility'] = schema_check
            if not schema_check['passed']:
                validation_result['valid'] = False
                validation_result['errors'].extend(schema_check['errors'])
            
            # Version compatibility check
            version_check = await self._validate_version_compatibility(contract, provider_capabilities)
            validation_result['checks']['version_compatibility'] = version_check
            if not version_check['passed']:
                validation_result['valid'] = False
                validation_result['errors'].extend(version_check['errors'])
            
            # Performance requirements check
            perf_check = await self._validate_performance_requirements(contract, provider_capabilities, consumer_requirements)
            validation_result['checks']['performance'] = perf_check
            if not perf_check['passed']:
                validation_result['warnings'].extend(perf_check['warnings'])
            
            # Security requirements check
            security_check = await self._validate_security_requirements(contract, provider_capabilities, consumer_requirements)
            validation_result['checks']['security'] = security_check
            if not security_check['passed']:
                validation_result['valid'] = False
                validation_result['errors'].extend(security_check['errors'])
            
            # Test cases validation
            if contract.test_cases:
                test_check = await self._validate_test_cases(contract, provider_capabilities)
                validation_result['checks']['test_cases'] = test_check
                if not test_check['passed']:
                    validation_result['warnings'].extend(test_check['warnings'])
            
            # Cache result
            self.validation_cache[cache_key] = validation_result
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Contract validation failed: {str(e)}")
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            return validation_result
    
    async def _validate_schema_compatibility(
        self, 
        contract: ModuleContract, 
        capabilities: List[ModuleCapability]
    ) -> Dict[str, Any]:
        """Validate schema compatibility"""
        result = {'passed': True, 'errors': [], 'warnings': []}
        
        try:
            # Find matching capabilities
            matching_caps = [
                cap for cap in capabilities 
                if cap.capability_type.value in contract.specification.get('required_capabilities', [])
            ]
            
            if not matching_caps:
                result['passed'] = False
                result['errors'].append("No matching capabilities found for contract requirements")
                return result
            
            # Validate input/output schemas
            for cap in matching_caps:
                if contract.specification.get('input_schema'):
                    if not self._schemas_compatible(contract.specification['input_schema'], cap.input_schema):
                        result['errors'].append(f"Input schema incompatible for capability {cap.capability_id}")
                        result['passed'] = False
                
                if contract.specification.get('output_schema'):
                    if not self._schemas_compatible(cap.output_schema, contract.specification['output_schema']):
                        result['errors'].append(f"Output schema incompatible for capability {cap.capability_id}")
                        result['passed'] = False
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Schema validation error: {str(e)}")
        
        return result
    
    def _schemas_compatible(self, provider_schema: Dict[str, Any], consumer_schema: Dict[str, Any]) -> bool:
        """Check if provider schema is compatible with consumer schema"""
        # Simplified schema compatibility check
        # In a real implementation, this would use JSON Schema validation
        
        if not provider_schema or not consumer_schema:
            return True  # Empty schemas are compatible
        
        # Check required fields
        provider_required = provider_schema.get('required', [])
        consumer_required = consumer_schema.get('required', [])
        
        # Provider must provide all fields required by consumer
        for field in consumer_required:
            if field not in provider_required:
                return False
        
        return True
    
    async def _validate_version_compatibility(
        self, 
        contract: ModuleContract, 
        capabilities: List[ModuleCapability]
    ) -> Dict[str, Any]:
        """Validate version compatibility"""
        result = {'passed': True, 'errors': [], 'warnings': []}
        
        try:
            checker = VersionCompatibilityChecker()
            
            for cap in capabilities:
                required_version = contract.specification.get('version_requirements', {}).get(cap.capability_id)
                if required_version:
                    compatibility = checker.check_compatibility(
                        required_version, 
                        cap.version, 
                        cap.capability_id
                    )
                    
                    if compatibility == CompatibilityLevel.BREAKING_CHANGES:
                        result['passed'] = False
                        result['errors'].append(
                            f"Breaking changes between required version {required_version} "
                            f"and available version {cap.version} for {cap.capability_id}"
                        )
                    elif compatibility == CompatibilityLevel.UNKNOWN:
                        result['warnings'].append(
                            f"Unknown compatibility between versions for {cap.capability_id}"
                        )
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Version validation error: {str(e)}")
        
        return result
    
    async def _validate_performance_requirements(
        self, 
        contract: ModuleContract, 
        capabilities: List[ModuleCapability], 
        consumer_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate performance requirements"""
        result = {'passed': True, 'errors': [], 'warnings': []}
        
        try:
            perf_requirements = consumer_requirements.get('performance', {})
            if not perf_requirements:
                return result
            
            for cap in capabilities:
                cap_perf = cap.performance_characteristics
                
                # Check response time requirements
                max_response_time = perf_requirements.get('max_response_time_ms')
                if max_response_time and cap_perf.get('avg_response_time_ms', 0) > max_response_time:
                    result['warnings'].append(
                        f"Capability {cap.capability_id} average response time exceeds requirement"
                    )
                
                # Check throughput requirements
                min_throughput = perf_requirements.get('min_throughput_rps')
                if min_throughput and cap_perf.get('max_throughput_rps', float('inf')) < min_throughput:
                    result['warnings'].append(
                        f"Capability {cap.capability_id} throughput below requirement"
                    )
            
        except Exception as e:
            result['warnings'].append(f"Performance validation error: {str(e)}")
        
        return result
    
    async def _validate_security_requirements(
        self, 
        contract: ModuleContract, 
        capabilities: List[ModuleCapability], 
        consumer_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate security requirements"""
        result = {'passed': True, 'errors': [], 'warnings': []}
        
        try:
            security_requirements = consumer_requirements.get('security', {})
            if not security_requirements:
                return result
            
            required_permissions = security_requirements.get('required_permissions', [])
            
            for cap in capabilities:
                # Check if capability requires permissions consumer doesn't have
                for perm in cap.required_permissions:
                    if perm not in required_permissions:
                        result['errors'].append(
                            f"Capability {cap.capability_id} requires permission {perm} "
                            f"not provided by consumer"
                        )
                        result['passed'] = False
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Security validation error: {str(e)}")
        
        return result
    
    async def _validate_test_cases(
        self, 
        contract: ModuleContract, 
        capabilities: List[ModuleCapability]
    ) -> Dict[str, Any]:
        """Validate contract test cases"""
        result = {'passed': True, 'errors': [], 'warnings': []}
        
        try:
            # This would run actual test cases against the provider
            # For now, just validate test case structure
            for test_case in contract.test_cases:
                if not test_case.get('name') or not test_case.get('input'):
                    result['warnings'].append("Test case missing required fields")
                    result['passed'] = False
            
        except Exception as e:
            result['warnings'].append(f"Test case validation error: {str(e)}")
        
        return result
    
    def _get_validation_cache_key(
        self, 
        contract: ModuleContract, 
        capabilities: List[ModuleCapability], 
        requirements: Dict[str, Any]
    ) -> str:
        """Generate cache key for validation result"""
        key_data = {
            'contract_id': contract.contract_id,
            'contract_version': contract.version,
            'capabilities': [cap.capability_id + cap.version for cap in capabilities],
            'requirements_hash': hashlib.md5(json.dumps(requirements, sort_keys=True).encode()).hexdigest()
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()


class ModuleDiscoveryService:
    """
    Service for module discovery and capability negotiation
    
    Provides:
    - Module and capability discovery
    - Version compatibility checking
    - Contract validation
    - Capability negotiation between modules
    """
    
    def __init__(self, audit_service: Optional[AuditService] = None):
        self.audit_service = audit_service
        
        # Capability registry
        self.advertised_capabilities: Dict[str, List[ModuleCapability]] = defaultdict(list)
        self.active_contracts: Dict[str, ModuleContract] = {}
        
        # Discovery cache
        self.discovery_cache: OrderedDict[str, DiscoveryResult] = OrderedDict()
        self.max_cache_size = 1000
        
        # Validation components
        self.version_checker = VersionCompatibilityChecker()
        self.contract_validator = ContractValidator()
        
        # Thread safety
        self._capabilities_lock = threading.RLock()
        self._cache_lock = threading.RLock()
        
        logger.info("Module discovery service initialized")
    
    def advertise_capability(self, module_id: str, capability: ModuleCapability):
        """Advertise a capability for a module"""
        with self._capabilities_lock:
            self.advertised_capabilities[module_id].append(capability)
            logger.info(f"Module {module_id} advertised capability {capability.capability_id}")
    
    def remove_capability(self, module_id: str, capability_id: str):
        """Remove an advertised capability"""
        with self._capabilities_lock:
            capabilities = self.advertised_capabilities.get(module_id, [])
            self.advertised_capabilities[module_id] = [
                cap for cap in capabilities if cap.capability_id != capability_id
            ]
            logger.info(f"Removed capability {capability_id} from module {module_id}")
    
    async def discover_modules(self, query: DiscoveryQuery) -> DiscoveryResult:
        """
        Discover modules and capabilities based on query
        
        Args:
            query: Discovery query with search criteria
            
        Returns:
            DiscoveryResult with matching modules and capabilities
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = self._get_discovery_cache_key(query)
        with self._cache_lock:
            if cache_key in self.discovery_cache:
                cached_result = self.discovery_cache[cache_key]
                # Cache is valid for 5 minutes
                if datetime.utcnow() - cached_result.created_at < timedelta(minutes=5):
                    cached_result.cached = True
                    return cached_result
        
        try:
            result = DiscoveryResult(query_id=query.query_id)
            
            # Get module registry
            module_registry = get_module_registry()
            
            # Get all registered modules
            all_modules = await module_registry.get_registered_modules()
            
            # Filter modules based on query criteria
            matching_modules = []
            matching_capabilities = []
            
            for registration in all_modules:
                if self._module_matches_query(registration, query):
                    # Get module capabilities
                    module_capabilities = self.advertised_capabilities.get(registration.metadata.id, [])
                    
                    # Filter capabilities based on query
                    filtered_capabilities = [
                        cap for cap in module_capabilities
                        if self._capability_matches_query(cap, query)
                    ]
                    
                    if filtered_capabilities or not query.capability_types:
                        # Include module data
                        module_data = {
                            'module_id': registration.metadata.id,
                            'name': registration.metadata.name,
                            'version': registration.metadata.version,
                            'module_type': registration.metadata.module_type.value,
                            'status': registration.status.value,
                            'health': registration.health.value,
                            'capabilities': [cap.to_dict() for cap in filtered_capabilities]
                        }
                        
                        # Add health status if requested
                        if query.include_health_status:
                            module_data['health_check_results'] = registration.health_check_results
                        
                        matching_modules.append(module_data)
                        matching_capabilities.extend(filtered_capabilities)
            
            # Apply result limits
            if len(matching_modules) > query.max_results:
                matching_modules = matching_modules[:query.max_results]
                matching_capabilities = matching_capabilities[:query.max_results]
            
            # Build result
            result.modules = matching_modules
            result.capabilities = matching_capabilities
            result.total_found = len(matching_modules)
            result.query_duration_ms = (time.time() - start_time) * 1000
            
            # Cache result
            with self._cache_lock:
                if len(self.discovery_cache) >= self.max_cache_size:
                    # Remove oldest entry
                    self.discovery_cache.popitem(last=False)
                
                self.discovery_cache[cache_key] = result
                self.discovery_cache.move_to_end(cache_key)
            
            logger.info(f"Discovery query {query.query_id} found {result.total_found} modules")
            return result
            
        except Exception as e:
            logger.error(f"Module discovery failed: {str(e)}")
            result = DiscoveryResult(
                query_id=query.query_id,
                query_duration_ms=(time.time() - start_time) * 1000
            )
            return result
    
    async def negotiate_capability(
        self,
        consumer_module: str,
        provider_module: str,
        capability_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Negotiate capability usage between consumer and provider modules
        
        Args:
            consumer_module: Module requesting capability
            provider_module: Module providing capability
            capability_requirements: Requirements from consumer
            
        Returns:
            Negotiation result with contract or rejection reason
        """
        try:
            # Get provider capabilities
            provider_capabilities = self.advertised_capabilities.get(provider_module, [])
            if not provider_capabilities:
                return {
                    'success': False,
                    'reason': f'Provider module {provider_module} has no advertised capabilities'
                }
            
            # Find matching capabilities
            required_capability_type = capability_requirements.get('capability_type')
            matching_caps = [
                cap for cap in provider_capabilities
                if not required_capability_type or cap.capability_type.value == required_capability_type
            ]
            
            if not matching_caps:
                return {
                    'success': False,
                    'reason': f'No matching capabilities found for type {required_capability_type}'
                }
            
            # Check version compatibility
            required_version = capability_requirements.get('version')
            if required_version:
                compatible_caps = []
                for cap in matching_caps:
                    compatibility = self.version_checker.check_compatibility(
                        required_version, cap.version, cap.capability_id
                    )
                    if compatibility in [CompatibilityLevel.COMPATIBLE, CompatibilityLevel.BACKWARD_COMPATIBLE]:
                        compatible_caps.append(cap)
                
                if not compatible_caps:
                    return {
                        'success': False,
                        'reason': f'No version-compatible capabilities found for version {required_version}'
                    }
                
                matching_caps = compatible_caps
            
            # Create contract
            contract_id = str(uuid.uuid4())
            contract = ModuleContract(
                contract_id=contract_id,
                name=f"{consumer_module}-{provider_module}-capability-contract",
                contract_type=ContractType.API_SPECIFICATION,
                version="1.0.0",
                provider_module=provider_module,
                consumer_module=consumer_module,
                specification=capability_requirements
            )
            
            # Validate contract
            validation_result = await self.contract_validator.validate_contract(
                contract, matching_caps, capability_requirements
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'reason': f'Contract validation failed: {validation_result["errors"]}',
                    'validation_details': validation_result
                }
            
            # Store active contract
            self.active_contracts[contract_id] = contract
            
            # Audit log
            if self.audit_service:
                await self.audit_service.log_action(
                    user_id="system",
                    action="CAPABILITY_NEGOTIATION",
                    resource_type="module_contract",
                    resource_id=contract_id,
                    description=f"Negotiated capability contract between {consumer_module} and {provider_module}",
                    metadata={
                        'consumer_module': consumer_module,
                        'provider_module': provider_module,
                        'capability_type': required_capability_type,
                        'matching_capabilities': [cap.capability_id for cap in matching_caps]
                    }
                )
            
            return {
                'success': True,
                'contract_id': contract_id,
                'contract': contract.to_dict(),
                'matching_capabilities': [cap.to_dict() for cap in matching_caps],
                'validation_result': validation_result
            }
            
        except Exception as e:
            logger.error(f"Capability negotiation failed: {str(e)}")
            return {
                'success': False,
                'reason': f'Negotiation error: {str(e)}'
            }
    
    async def validate_contract(self, contract_id: str) -> Dict[str, Any]:
        """Validate an existing contract"""
        try:
            contract = self.active_contracts.get(contract_id)
            if not contract:
                return {
                    'valid': False,
                    'error': f'Contract {contract_id} not found'
                }
            
            # Get current provider capabilities
            provider_capabilities = self.advertised_capabilities.get(contract.provider_module, [])
            
            # Re-validate contract
            validation_result = await self.contract_validator.validate_contract(
                contract, provider_capabilities, contract.specification
            )
            
            # Update contract validation results
            contract.last_validated = datetime.utcnow()
            contract.validation_results = validation_result
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Contract validation failed: {str(e)}")
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def get_module_capabilities(self, module_id: str) -> List[ModuleCapability]:
        """Get all capabilities advertised by a module"""
        with self._capabilities_lock:
            return self.advertised_capabilities.get(module_id, []).copy()
    
    def get_active_contracts(self, module_id: Optional[str] = None) -> List[ModuleContract]:
        """Get active contracts, optionally filtered by module"""
        contracts = list(self.active_contracts.values())
        
        if module_id:
            contracts = [
                contract for contract in contracts
                if contract.provider_module == module_id or contract.consumer_module == module_id
            ]
        
        return contracts
    
    def get_discovery_metrics(self) -> Dict[str, Any]:
        """Get discovery service metrics"""
        with self._capabilities_lock, self._cache_lock:
            return {
                'total_advertised_capabilities': sum(
                    len(caps) for caps in self.advertised_capabilities.values()
                ),
                'modules_with_capabilities': len(self.advertised_capabilities),
                'active_contracts': len(self.active_contracts),
                'discovery_cache_size': len(self.discovery_cache),
                'capability_types_distribution': self._get_capability_type_distribution()
            }
    
    # Private helper methods
    
    def _module_matches_query(self, registration: ModuleRegistration, query: DiscoveryQuery) -> bool:
        """Check if module matches discovery query criteria"""
        metadata = registration.metadata
        
        # Check module types
        if query.module_types and metadata.module_type not in query.module_types:
            return False
        
        # Check exclusions
        if query.exclude_modules and metadata.id in query.exclude_modules:
            return False
        
        # Check availability
        if query.only_available and registration.status != ModuleStatus.ACTIVE:
            return False
        
        # Check health
        if query.only_healthy and registration.health.value != 'healthy':
            return False
        
        # Check tags
        if query.tags:
            if not query.tags.intersection(set(metadata.tags)):
                return False
        
        # Check version constraints
        if query.version_constraints:
            constraint = query.version_constraints.get(metadata.id)
            if constraint:
                compatibility = self.version_checker.check_compatibility(
                    constraint, metadata.version, metadata.id
                )
                if compatibility == CompatibilityLevel.BREAKING_CHANGES:
                    return False
        
        return True
    
    def _capability_matches_query(self, capability: ModuleCapability, query: DiscoveryQuery) -> bool:
        """Check if capability matches discovery query criteria"""
        # Check capability types
        if query.capability_types and capability.capability_type not in query.capability_types:
            return False
        
        # Check availability
        if query.only_available and not capability.is_available:
            return False
        
        # Check tags
        if query.tags:
            if not query.tags.intersection(capability.tags):
                return False
        
        # Check permissions
        if query.required_permissions:
            if not set(query.required_permissions).issubset(set(capability.required_permissions)):
                return False
        
        return True
    
    def _get_discovery_cache_key(self, query: DiscoveryQuery) -> str:
        """Generate cache key for discovery query"""
        key_data = {
            'module_types': [mt.value for mt in query.module_types] if query.module_types else None,
            'capability_types': [ct.value for ct in query.capability_types] if query.capability_types else None,
            'tags': list(query.tags) if query.tags else None,
            'version_constraints': query.version_constraints,
            'exclude_modules': list(query.exclude_modules) if query.exclude_modules else None,
            'only_available': query.only_available,
            'only_healthy': query.only_healthy,
            'max_results': query.max_results
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _get_capability_type_distribution(self) -> Dict[str, int]:
        """Get distribution of capability types"""
        distribution = defaultdict(int)
        for capabilities in self.advertised_capabilities.values():
            for capability in capabilities:
                distribution[capability.capability_type.value] += 1
        return dict(distribution)


# Global instance
discovery_service: Optional[ModuleDiscoveryService] = None


def get_discovery_service() -> ModuleDiscoveryService:
    """Get the global discovery service instance"""
    global discovery_service
    if discovery_service is None:
        raise RuntimeError("Discovery service not initialized")
    return discovery_service


async def initialize_discovery_service(
    audit_service: Optional[AuditService] = None
) -> ModuleDiscoveryService:
    """Initialize the global discovery service"""
    global discovery_service
    if discovery_service is None:
        discovery_service = ModuleDiscoveryService(audit_service=audit_service)
        logger.info("Global discovery service initialized")
    return discovery_service