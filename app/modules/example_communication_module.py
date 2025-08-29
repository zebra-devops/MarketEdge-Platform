"""
Example Module Implementation: Inter-Module Communication

This example demonstrates how to implement a module that uses the complete
US-104 inter-module communication system including message bus, discovery,
event sourcing, and workflow capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from ..core.module_communication import (
    ModuleCommunicationHandler,
    CommunicationProtocol,
    SecurityLevel,
    CommunicationContext,
    get_communication_service,
    module_communication_handler,
    request_handler,
    event_handler,
    command_handler
)
from ..core.module_discovery import (
    ModuleCapability,
    CapabilityType,
    get_discovery_service
)
from ..core.event_system import (
    WorkflowDefinition,
    WorkflowStep,
    get_event_system
)
from ..core.message_bus import MessagePriority
from ..models.user import User

logger = logging.getLogger(__name__)


@module_communication_handler(
    supported_protocols=[
        CommunicationProtocol.REQUEST_RESPONSE,
        CommunicationProtocol.PUBLISH_SUBSCRIBE,
        CommunicationProtocol.EVENT_DRIVEN,
        CommunicationProtocol.WORKFLOW
    ],
    security_level=SecurityLevel.AUTHENTICATED
)
class MarketAnalysisModule:
    """
    Example module that provides market analysis capabilities
    and demonstrates inter-module communication patterns.
    """
    
    def __init__(self):
        self.module_id = "market_analysis"
        self.version = "1.0.0"
        
        # Module state
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.active_analyses: Dict[str, str] = {}  # analysis_id -> status
        
        # Communication metrics
        self.communication_metrics = {
            'requests_processed': 0,
            'events_published': 0,
            'workflows_started': 0
        }
    
    async def initialize(self):
        """Initialize the module and register capabilities"""
        try:
            # Get services
            comm_service = get_communication_service()
            discovery_service = get_discovery_service()
            event_system = get_event_system()
            
            # Advertise capabilities
            await self._advertise_capabilities(discovery_service)
            
            # Register workflows
            await self._register_workflows(event_system)
            
            # Subscribe to relevant events
            await self._setup_event_subscriptions(comm_service)
            
            logger.info(f"Market Analysis Module initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Market Analysis Module: {str(e)}")
            raise
    
    # Request handlers
    
    @request_handler("analyze_market_data")
    async def handle_market_analysis_request(
        self, 
        data: Dict[str, Any], 
        context: CommunicationContext
    ) -> Dict[str, Any]:
        """Handle market analysis requests from other modules"""
        try:
            self.communication_metrics['requests_processed'] += 1
            
            # Extract request parameters
            market_data = data.get('market_data', {})
            analysis_type = data.get('analysis_type', 'basic')
            time_frame = data.get('time_frame', '1d')
            
            # Validate user permissions
            if context.auth_context:
                user_permissions = context.auth_context.permissions
                if 'market:analyze' not in user_permissions:
                    raise PermissionError("Insufficient permissions for market analysis")
            
            # Generate analysis ID
            analysis_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            self.active_analyses[analysis_id] = "processing"
            
            # Perform analysis (simplified)
            analysis_result = await self._perform_market_analysis(
                market_data, analysis_type, time_frame
            )
            
            # Cache result
            self.analysis_cache[analysis_id] = {
                'result': analysis_result,
                'created_at': datetime.utcnow(),
                'requested_by': context.user.id if context.user else 'system'
            }
            
            # Update status
            self.active_analyses[analysis_id] = "completed"
            
            # Publish completion event
            await self._publish_analysis_completed_event(
                analysis_id, analysis_result, context
            )
            
            return {
                'analysis_id': analysis_id,
                'status': 'completed',
                'result': analysis_result,
                'metadata': {
                    'analysis_type': analysis_type,
                    'time_frame': time_frame,
                    'processed_at': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Market analysis request failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'analysis_id': analysis_id if 'analysis_id' in locals() else None
            }
    
    @request_handler("get_analysis_status")
    async def handle_analysis_status_request(
        self, 
        data: Dict[str, Any], 
        context: CommunicationContext
    ) -> Dict[str, Any]:
        """Get status of ongoing or completed analysis"""
        try:
            analysis_id = data.get('analysis_id')
            if not analysis_id:
                raise ValueError("Analysis ID is required")
            
            # Check if analysis exists
            if analysis_id not in self.active_analyses:
                return {
                    'status': 'not_found',
                    'analysis_id': analysis_id
                }
            
            status = self.active_analyses[analysis_id]
            result_data = {'analysis_id': analysis_id, 'status': status}
            
            # Include result if completed
            if status == 'completed' and analysis_id in self.analysis_cache:
                cached_result = self.analysis_cache[analysis_id]
                result_data.update({
                    'result': cached_result['result'],
                    'created_at': cached_result['created_at'].isoformat()
                })
            
            return result_data
            
        except Exception as e:
            logger.error(f"Analysis status request failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    @request_handler("trigger_batch_analysis")
    async def handle_batch_analysis_request(
        self, 
        data: Dict[str, Any], 
        context: CommunicationContext
    ) -> Dict[str, Any]:
        """Trigger batch analysis workflow"""
        try:
            batch_data = data.get('batch_data', [])
            analysis_config = data.get('config', {})
            
            # Start batch analysis workflow
            comm_service = get_communication_service()
            
            workflow_context = {
                'batch_data': batch_data,
                'config': analysis_config,
                'requested_by': context.user.id if context.user else 'system',
                'request_timestamp': datetime.utcnow().isoformat()
            }
            
            execution_id = await comm_service.start_workflow(
                workflow_id="batch_market_analysis",
                context=workflow_context,
                auth_context=context.auth_context
            )
            
            self.communication_metrics['workflows_started'] += 1
            
            return {
                'status': 'workflow_started',
                'execution_id': execution_id,
                'batch_size': len(batch_data)
            }
            
        except Exception as e:
            logger.error(f"Batch analysis request failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    # Event handlers
    
    @event_handler("market.data.updated")
    async def handle_market_data_update(
        self, 
        event_data: Dict[str, Any], 
        context: CommunicationContext
    ):
        """Handle market data update events"""
        try:
            logger.info("Received market data update event")
            
            # Extract update information
            market_symbol = event_data.get('symbol')
            update_type = event_data.get('update_type', 'price_change')
            
            # Invalidate related analysis cache
            await self._invalidate_related_analyses(market_symbol)
            
            # Check if any active analyses need updating
            for analysis_id, status in self.active_analyses.items():
                if status == 'processing':
                    # Notify analysis process of data update
                    await self._notify_analysis_of_update(analysis_id, event_data)
            
            # Publish derived event if significant change
            if event_data.get('change_magnitude', 0) > 0.05:  # 5% threshold
                await self._publish_significant_change_event(market_symbol, event_data)
            
        except Exception as e:
            logger.error(f"Error handling market data update: {str(e)}")
    
    @event_handler("user.preferences.updated")
    async def handle_user_preferences_update(
        self, 
        event_data: Dict[str, Any], 
        context: CommunicationContext
    ):
        """Handle user preference updates that may affect analyses"""
        try:
            user_id = event_data.get('user_id')
            preferences = event_data.get('preferences', {})
            
            # Update analysis parameters based on preferences
            analysis_preferences = preferences.get('market_analysis', {})
            
            if analysis_preferences:
                # Store user-specific analysis preferences
                await self._update_user_analysis_preferences(user_id, analysis_preferences)
                
                # Refresh any cached analyses for this user
                await self._refresh_user_analyses(user_id)
            
        except Exception as e:
            logger.error(f"Error handling user preferences update: {str(e)}")
    
    # Command handlers
    
    @command_handler("refresh_analysis_cache")
    async def handle_refresh_cache_command(
        self, 
        data: Dict[str, Any], 
        context: CommunicationContext
    ) -> Dict[str, Any]:
        """Handle cache refresh commands"""
        try:
            # Clear analysis cache
            cleared_count = len(self.analysis_cache)
            self.analysis_cache.clear()
            
            # Reset active analyses that are stale
            stale_analyses = []
            current_time = datetime.utcnow()
            
            for analysis_id, status in list(self.active_analyses.items()):
                if status == 'processing':
                    # Check if analysis has been running too long (e.g., > 1 hour)
                    # In a real implementation, you'd track start times
                    stale_analyses.append(analysis_id)
                    del self.active_analyses[analysis_id]
            
            logger.info(f"Cache refresh completed: cleared {cleared_count} analyses, "
                       f"removed {len(stale_analyses)} stale analyses")
            
            return {
                'status': 'completed',
                'cleared_analyses': cleared_count,
                'removed_stale': len(stale_analyses)
            }
            
        except Exception as e:
            logger.error(f"Cache refresh command failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    # Private helper methods
    
    async def _advertise_capabilities(self, discovery_service):
        """Advertise module capabilities"""
        try:
            # Market analysis capability
            analysis_capability = ModuleCapability(
                capability_id="market_analysis",
                name="Market Data Analysis",
                capability_type=CapabilityType.DATA_PROCESSOR,
                description="Provides comprehensive market data analysis",
                version=self.version,
                input_schema={
                    "type": "object",
                    "properties": {
                        "market_data": {"type": "object"},
                        "analysis_type": {"type": "string", "enum": ["basic", "advanced", "predictive"]},
                        "time_frame": {"type": "string", "enum": ["1h", "1d", "1w", "1m"]}
                    },
                    "required": ["market_data"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_id": {"type": "string"},
                        "status": {"type": "string"},
                        "result": {"type": "object"}
                    }
                },
                required_permissions=["market:analyze"],
                performance_characteristics={
                    "avg_response_time_ms": 2000,
                    "max_throughput_rps": 10
                },
                is_available=True
            )
            
            discovery_service.advertise_capability(self.module_id, analysis_capability)
            
            # Batch processing capability
            batch_capability = ModuleCapability(
                capability_id="batch_market_analysis",
                name="Batch Market Analysis",
                capability_type=CapabilityType.COMPUTATION,
                description="Performs batch analysis of multiple market datasets",
                version=self.version,
                input_schema={
                    "type": "object",
                    "properties": {
                        "batch_data": {"type": "array"},
                        "config": {"type": "object"}
                    },
                    "required": ["batch_data"]
                },
                required_permissions=["market:batch_analyze"],
                is_available=True
            )
            
            discovery_service.advertise_capability(self.module_id, batch_capability)
            
            logger.info("Market analysis capabilities advertised")
            
        except Exception as e:
            logger.error(f"Failed to advertise capabilities: {str(e)}")
            raise
    
    async def _register_workflows(self, event_system):
        """Register workflow definitions"""
        try:
            # Batch analysis workflow
            batch_workflow = WorkflowDefinition(
                workflow_id="batch_market_analysis",
                name="Batch Market Analysis Workflow",
                description="Processes multiple market analyses in parallel",
                version="1.0.0",
                trigger_events=["workflow.manual_trigger"],
                steps=[
                    WorkflowStep(
                        step_id="validate_batch_data",
                        name="Validate Batch Data",
                        handler="market_analysis.validate_batch_data",
                        input_mapping={"data": "batch_data"},
                        output_mapping={"validated_data": "validated_batch_data"},
                        timeout_seconds=60
                    ),
                    WorkflowStep(
                        step_id="split_batch",
                        name="Split Batch into Chunks",
                        handler="market_analysis.split_batch",
                        input_mapping={"data": "validated_batch_data", "config": "config"},
                        output_mapping={"chunks": "batch_chunks"},
                        depends_on=["validate_batch_data"]
                    ),
                    WorkflowStep(
                        step_id="process_chunks",
                        name="Process Data Chunks",
                        handler="market_analysis.process_chunks_parallel",
                        input_mapping={"chunks": "batch_chunks"},
                        output_mapping={"results": "chunk_results"},
                        depends_on=["split_batch"],
                        timeout_seconds=600
                    ),
                    WorkflowStep(
                        step_id="aggregate_results",
                        name="Aggregate Analysis Results",
                        handler="market_analysis.aggregate_results",
                        input_mapping={"results": "chunk_results"},
                        output_mapping={"final_result": "batch_analysis_result"},
                        depends_on=["process_chunks"]
                    ),
                    WorkflowStep(
                        step_id="notify_completion",
                        name="Notify Analysis Completion",
                        handler="market_analysis.notify_batch_completion",
                        input_mapping={"result": "batch_analysis_result"},
                        depends_on=["aggregate_results"]
                    )
                ],
                parallel_execution=True,  # Allow parallel step execution where possible
                timeout_seconds=1800  # 30 minutes total timeout
            )
            
            event_system.register_workflow(batch_workflow)
            
            logger.info("Market analysis workflows registered")
            
        except Exception as e:
            logger.error(f"Failed to register workflows: {str(e)}")
            raise
    
    async def _setup_event_subscriptions(self, comm_service):
        """Setup event subscriptions"""
        try:
            # Subscribe to market data updates
            await comm_service.subscribe_to_event(
                self.module_id,
                "market.data.updated",
                self.handle_market_data_update
            )
            
            # Subscribe to user preference updates
            await comm_service.subscribe_to_event(
                self.module_id,
                "user.preferences.updated",
                self.handle_user_preferences_update
            )
            
            logger.info("Event subscriptions setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup event subscriptions: {str(e)}")
            raise
    
    async def _perform_market_analysis(
        self, 
        market_data: Dict[str, Any], 
        analysis_type: str, 
        time_frame: str
    ) -> Dict[str, Any]:
        """Perform the actual market analysis (simplified implementation)"""
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Extract market data
        symbol = market_data.get('symbol', 'UNKNOWN')
        price_data = market_data.get('prices', [])
        volume_data = market_data.get('volumes', [])
        
        # Basic analysis calculations
        if not price_data:
            return {'error': 'No price data available'}
        
        current_price = price_data[-1] if price_data else 0
        price_change = ((current_price - price_data[0]) / price_data[0] * 100) if len(price_data) > 1 else 0
        avg_volume = sum(volume_data) / len(volume_data) if volume_data else 0
        
        # Analysis result based on type
        if analysis_type == 'basic':
            result = {
                'symbol': symbol,
                'current_price': current_price,
                'price_change_percent': round(price_change, 2),
                'average_volume': round(avg_volume, 2),
                'trend': 'bullish' if price_change > 0 else 'bearish',
                'analysis_type': analysis_type,
                'time_frame': time_frame
            }
        elif analysis_type == 'advanced':
            # More sophisticated analysis
            volatility = self._calculate_volatility(price_data)
            rsi = self._calculate_rsi(price_data)
            
            result = {
                'symbol': symbol,
                'current_price': current_price,
                'price_change_percent': round(price_change, 2),
                'volatility': round(volatility, 4),
                'rsi': round(rsi, 2),
                'trend_strength': 'strong' if abs(price_change) > 5 else 'weak',
                'recommendation': self._generate_recommendation(price_change, rsi),
                'analysis_type': analysis_type,
                'time_frame': time_frame
            }
        else:
            # Predictive analysis placeholder
            result = {
                'symbol': symbol,
                'current_price': current_price,
                'predicted_prices': [current_price * (1 + (i * 0.01)) for i in range(5)],
                'confidence_level': 0.75,
                'prediction_horizon': '5 periods',
                'analysis_type': analysis_type,
                'time_frame': time_frame
            }
        
        return result
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility (simplified)"""
        if len(prices) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        if not returns:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        
        return variance ** 0.5
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index (simplified)"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _generate_recommendation(self, price_change: float, rsi: float) -> str:
        """Generate trading recommendation based on analysis"""
        if rsi > 70:
            return 'sell'  # Overbought
        elif rsi < 30:
            return 'buy'   # Oversold
        elif price_change > 2:
            return 'hold_bullish'
        elif price_change < -2:
            return 'hold_bearish'
        else:
            return 'neutral'
    
    async def _publish_analysis_completed_event(
        self, 
        analysis_id: str, 
        result: Dict[str, Any],
        context: CommunicationContext
    ):
        """Publish analysis completion event"""
        try:
            comm_service = get_communication_service()
            
            event_data = {
                'analysis_id': analysis_id,
                'symbol': result.get('symbol'),
                'analysis_type': result.get('analysis_type'),
                'completed_at': datetime.utcnow().isoformat(),
                'result_summary': {
                    'trend': result.get('trend'),
                    'recommendation': result.get('recommendation')
                }
            }
            
            await comm_service.publish_event(
                source_module=self.module_id,
                event_name="market.analysis.completed",
                data=event_data,
                auth_context=context.auth_context,
                priority=MessagePriority.NORMAL,
                tags={'analysis', 'completion'}
            )
            
            self.communication_metrics['events_published'] += 1
            
        except Exception as e:
            logger.error(f"Failed to publish analysis completion event: {str(e)}")
    
    async def _publish_significant_change_event(
        self, 
        symbol: str, 
        market_data: Dict[str, Any]
    ):
        """Publish significant market change event"""
        try:
            comm_service = get_communication_service()
            
            event_data = {
                'symbol': symbol,
                'change_magnitude': market_data.get('change_magnitude'),
                'change_direction': 'up' if market_data.get('change_magnitude', 0) > 0 else 'down',
                'current_price': market_data.get('current_price'),
                'detected_at': datetime.utcnow().isoformat(),
                'alert_level': 'high' if market_data.get('change_magnitude', 0) > 0.1 else 'medium'
            }
            
            await comm_service.publish_event(
                source_module=self.module_id,
                event_name="market.significant_change",
                data=event_data,
                priority=MessagePriority.HIGH,
                tags={'market', 'alert', 'significant_change'}
            )
            
        except Exception as e:
            logger.error(f"Failed to publish significant change event: {str(e)}")
    
    async def _invalidate_related_analyses(self, symbol: str):
        """Invalidate cached analyses related to a symbol"""
        try:
            invalidated_count = 0
            
            for analysis_id, cached_data in list(self.analysis_cache.items()):
                result = cached_data.get('result', {})
                if result.get('symbol') == symbol:
                    # Remove from cache
                    del self.analysis_cache[analysis_id]
                    invalidated_count += 1
            
            if invalidated_count > 0:
                logger.info(f"Invalidated {invalidated_count} cached analyses for symbol {symbol}")
                
        except Exception as e:
            logger.error(f"Error invalidating related analyses: {str(e)}")
    
    async def _notify_analysis_of_update(self, analysis_id: str, update_data: Dict[str, Any]):
        """Notify ongoing analysis of data update"""
        try:
            # In a real implementation, this would communicate with the analysis process
            # For now, just log the notification
            logger.info(f"Analysis {analysis_id} notified of data update for {update_data.get('symbol')}")
            
        except Exception as e:
            logger.error(f"Error notifying analysis of update: {str(e)}")
    
    async def _update_user_analysis_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any]
    ):
        """Update user-specific analysis preferences"""
        try:
            # Store preferences (would typically use database)
            logger.info(f"Updated analysis preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user analysis preferences: {str(e)}")
    
    async def _refresh_user_analyses(self, user_id: str):
        """Refresh cached analyses for a user"""
        try:
            refreshed_count = 0
            
            for analysis_id, cached_data in self.analysis_cache.items():
                if cached_data.get('requested_by') == user_id:
                    # Mark for refresh (in real implementation, would re-run analysis)
                    logger.debug(f"Marked analysis {analysis_id} for refresh")
                    refreshed_count += 1
            
            if refreshed_count > 0:
                logger.info(f"Refreshed {refreshed_count} analyses for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error refreshing user analyses: {str(e)}")
    
    def get_module_metrics(self) -> Dict[str, Any]:
        """Get module performance and communication metrics"""
        return {
            **self.communication_metrics,
            'cached_analyses': len(self.analysis_cache),
            'active_analyses': len([s for s in self.active_analyses.values() if s == 'processing']),
            'completed_analyses': len([s for s in self.active_analyses.values() if s == 'completed']),
            'uptime_seconds': (datetime.utcnow() - datetime.utcnow()).total_seconds(),  # Placeholder
            'module_id': self.module_id,
            'version': self.version
        }


# Example usage and integration
async def main():
    """Example of how to initialize and use the market analysis module"""
    try:
        # Initialize communication service first
        from ..core.module_communication import initialize_communication_service
        from ..services.audit_service import AuditService
        
        # Mock audit service for example
        audit_service = AuditService(None)
        
        # Initialize communication service
        comm_service = await initialize_communication_service(audit_service=audit_service)
        
        # Create and initialize the module
        market_module = MarketAnalysisModule()
        await market_module.initialize()
        
        logger.info("Market Analysis Module example started successfully")
        
        # Example: Test request-response communication
        test_data = {
            'market_data': {
                'symbol': 'AAPL',
                'prices': [150.0, 152.5, 148.0, 155.0, 153.0],
                'volumes': [1000000, 1200000, 800000, 1500000, 1100000]
            },
            'analysis_type': 'advanced',
            'time_frame': '1d'
        }
        
        # This would typically be called by another module
        # result = await comm_service.send_request(
        #     source_module="test_client",
        #     target_module="market_analysis",
        #     action="analyze_market_data",
        #     data=test_data
        # )
        
        # Keep running
        await asyncio.sleep(10)
        
    except Exception as e:
        logger.error(f"Example execution failed: {str(e)}")
        raise
    finally:
        if 'comm_service' in locals():
            await comm_service.stop()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run example
    asyncio.run(main())