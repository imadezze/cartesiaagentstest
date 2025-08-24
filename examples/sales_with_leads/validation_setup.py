"""
Setup file for integrating end-of-call validation into the sales agent system.

This module provides setup functions and event routing for call validation.
"""

from loguru import logger
from call_validation_node import (
    CallValidationResult, 
    ValidatedEndCall,
    validate_end_call_request,
    generate_validation_response
)
from line.events import EndCall, AgentResponse


def setup_call_validation(bridge):
    """
    Set up call validation routing in the voice agent system.
    
    This function configures the event routing to intercept EndCall events
    and validate them before allowing the call to terminate.
    
    Args:
        bridge: The event bridge instance to configure
    """
    logger.info("🔧 Setting up call validation system")
    
    # Route 1: Intercept EndCall events for validation
    # This transforms EndCall events through validation logic
    (
        bridge.on(EndCall)
        .map(validate_end_call_request)
        .filter(lambda validated_call: validated_call is not None)
        .map(lambda validated_call: EndCall(reason=validated_call.reason) if validated_call.validation_passed else None)
        .filter(lambda end_call: end_call is not None)
        .broadcast()
    )
    
    # Route 2: Generate validation responses when end call fails
    # This creates agent responses when validation fails
    (
        bridge.on(EndCall)
        .map(generate_validation_response)
        .filter(lambda response: response is not None)
        .broadcast()
    )
    
    logger.info("✅ Call validation system configured")


def setup_validation_logging(bridge):
    """
    Set up logging for validation events to help with debugging.
    
    Args:
        bridge: The event bridge instance to configure
    """
    
    def log_validation_result(message):
        """Log validation results for monitoring."""
        result = message.event
        if isinstance(result, CallValidationResult):
            if result.is_valid:
                logger.info(f"✅ Call validation passed for leads: {result.leads_info}")
            else:
                logger.warning(f"❌ Call validation failed - missing: {result.missing_info}")
        return None  # Don't broadcast, just log
    
    def log_validated_end_call(message):
        """Log validated end call events."""
        validated_call = message.event
        if isinstance(validated_call, ValidatedEndCall):
            if validated_call.validation_passed:
                logger.info(f"✅ Validated end call: {validated_call.reason}")
            else:
                logger.warning(f"❌ Invalid end call attempt: {validated_call.original_reason}")
        return None
    
    # Set up logging routes
    bridge.on(CallValidationResult).map(log_validation_result)
    bridge.on(ValidatedEndCall).map(log_validated_end_call)
    
    logger.info("🔧 Validation logging configured")


# Example usage configuration
def configure_sales_agent_with_validation(bridge, chat_node):
    """
    Complete setup for a sales agent with call validation.
    
    This is an example of how to integrate the validation system
    into a sales agent configuration.
    
    Args:
        bridge: Event bridge instance
        chat_node: ChatNode instance
    """
    
    # 1. Set up standard conversation routing
    (
        bridge.on("UserStoppedSpeaking")
        .interrupt_on("UserStartedSpeaking") 
        .stream(chat_node.process_context)
        .broadcast()
    )
    
    # 2. Set up call validation
    setup_call_validation(bridge)
    
    # 3. Set up validation logging  
    setup_validation_logging(bridge)
    
    # 4. Route leads analysis events to chat node for context
    bridge.on("LeadsAnalysis").map(chat_node.add_event)
    bridge.on("ResearchAnalysis").map(chat_node.add_event)
    
    logger.info("🚀 Sales agent with validation fully configured")


# Validation statistics and monitoring
class ValidationStats:
    """Track validation statistics for monitoring and optimization."""
    
    def __init__(self):
        self.total_end_call_attempts = 0
        self.successful_validations = 0
        self.failed_validations = 0
        self.common_missing_fields = {}
        
    def record_validation(self, validation_result: CallValidationResult):
        """Record a validation result for statistics."""
        self.total_end_call_attempts += 1
        
        if validation_result.is_valid:
            self.successful_validations += 1
        else:
            self.failed_validations += 1
            
            # Track which fields are commonly missing
            for field in validation_result.missing_info:
                self.common_missing_fields[field] = self.common_missing_fields.get(field, 0) + 1
    
    def get_stats(self):
        """Get validation statistics summary."""
        if self.total_end_call_attempts == 0:
            return {"status": "No end call attempts yet"}
            
        return {
            "total_attempts": self.total_end_call_attempts,
            "success_rate": self.successful_validations / self.total_end_call_attempts,
            "most_missing_fields": sorted(
                self.common_missing_fields.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
        }


# Global stats instance
validation_stats = ValidationStats()


def setup_validation_monitoring(bridge):
    """Set up monitoring for validation statistics."""
    
    def record_validation_stats(message):
        """Record validation statistics."""
        result = message.event
        if isinstance(result, CallValidationResult):
            validation_stats.record_validation(result)
        return None
    
    bridge.on(CallValidationResult).map(record_validation_stats)
    
    logger.info("📊 Validation monitoring configured")