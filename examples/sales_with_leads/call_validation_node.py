"""
Call Validation Node - Validates end-of-call conditions before allowing call termination
"""

from typing import AsyncGenerator, Optional
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from config import LeadsAnalysis
from line.events import AgentResponse
from line.nodes.conversation_context import ConversationContext
from line.nodes.reasoning import ReasoningNode


class CallValidationResult(BaseModel):
    """Result of call validation check."""
    
    is_valid: bool
    missing_info: list[str]
    validation_message: str
    leads_info: Optional[dict] = None
    timestamp: str


class CallValidationNode(ReasoningNode):
    """
    Node that validates end-of-call conditions before allowing call termination.
    
    This node checks that all required information has been collected:
    - Personal name
    - Company name  
    - Email address
    - User has indicated desire to end conversation
    """
    
    def __init__(self):
        super().__init__(system_prompt="Call validation node")
        self.required_fields = ["name", "company", "email"]
        
    def _extract_latest_leads_info(self, context: ConversationContext) -> Optional[dict]:
        """Extract the most recent leads information from the conversation context."""
        for event in reversed(context.events):
            if isinstance(event, LeadsAnalysis):
                return event.leads_info
        return None
    
    def _validate_contact_info(self, leads_info: dict) -> tuple[bool, list[str]]:
        """
        Validate that all required contact information has been collected.
        
        Returns:
            tuple: (is_valid, missing_fields)
        """
        missing_fields = []
        
        for field in self.required_fields:
            value = leads_info.get(field, "").strip()
            if not value or value.lower() in ["", "unknown", "n/a", "not provided"]:
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
    
    def _check_user_intent_to_end(self, context: ConversationContext) -> bool:
        """
        Check if user has explicitly indicated they want to end the conversation.
        
        This looks for common phrases that indicate user wants to wrap up.
        """
        # Get recent user messages
        recent_messages = []
        for event in reversed(context.events):
            if hasattr(event, 'content') and event.__class__.__name__ == 'UserTranscriptionReceived':
                recent_messages.append(event.content.lower())
                if len(recent_messages) >= 3:  # Check last 3 user messages
                    break
        
        # Common phrases that indicate user wants to end
        end_indicators = [
            "goodbye", "bye", "thanks", "thank you", "that's all", "that's it",
            "done", "finished", "wrap up", "end call", "have to go", "gotta go",
            "appreciate it", "sounds good", "perfect", "great", "i'm good",
            "no more questions", "that covers it", "i think we're done"
        ]
        
        for message in recent_messages:
            for indicator in end_indicators:
                if indicator in message:
                    return True
        
        return False
    
    def _generate_validation_message(self, missing_fields: list[str], user_wants_to_end: bool) -> str:
        """Generate appropriate validation message based on what's missing."""
        
        if missing_fields and not user_wants_to_end:
            field_names = []
            for field in missing_fields:
                if field == "name":
                    field_names.append("your name")
                elif field == "company":
                    field_names.append("your company")
                elif field == "email":
                    field_names.append("your email address")
            
            if len(field_names) == 1:
                return f"Before we wrap up, could I get {field_names[0]} so I can follow up with more information about how Cartesia can help?"
            elif len(field_names) == 2:
                return f"Before we wrap up, could I get {field_names[0]} and {field_names[1]} so I can follow up with more information about how Cartesia can help?"
            else:
                return f"Before we wrap up, could I get {', '.join(field_names[:-1])}, and {field_names[-1]} so I can follow up with more information about how Cartesia can help?"
        
        elif missing_fields and user_wants_to_end:
            # User wants to end but we're missing info - be more gentle
            field_names = []
            for field in missing_fields:
                if field == "name":
                    field_names.append("your name")
                elif field == "company": 
                    field_names.append("your company")
                elif field == "email":
                    field_names.append("your email address")
            
            if len(field_names) == 1:
                return f"I completely understand you need to go. Could I quickly get {field_names[0]} for follow-up?"
            else:
                return f"I understand you need to go. Could I quickly get {' and '.join(field_names)} for follow-up?"
        
        elif not user_wants_to_end and not missing_fields:
            return "Is there anything else I can help clarify about Cartesia's voice agents before we wrap up?"
        
        # All conditions met
        return ""
    
    async def process_context(self, context: ConversationContext) -> AsyncGenerator[CallValidationResult, None]:
        """
        Validate end-of-call conditions and return validation result.
        
        This method is called when an EndCall event is intercepted.
        """
        logger.info("🔍 Validating end-of-call conditions")
        
        # Extract latest leads information
        leads_info = self._extract_latest_leads_info(context)
        if not leads_info:
            logger.warning("No leads information found in context")
            leads_info = {}
        
        # Validate contact information
        contact_valid, missing_fields = self._validate_contact_info(leads_info)
        
        # Check if user wants to end conversation
        user_wants_to_end = self._check_user_intent_to_end(context)
        
        # Determine if call can end
        can_end_call = contact_valid and user_wants_to_end
        
        # Generate appropriate message
        validation_message = ""
        if not can_end_call:
            validation_message = self._generate_validation_message(missing_fields, user_wants_to_end)
        
        logger.info(f"🔍 Validation result: can_end={can_end_call}, missing={missing_fields}, user_wants_end={user_wants_to_end}")
        
        validation_result = CallValidationResult(
            is_valid=can_end_call,
            missing_info=missing_fields,
            validation_message=validation_message,
            leads_info=leads_info,
            timestamp=datetime.now().isoformat()
        )
        
        yield validation_result


class ValidatedEndCall(BaseModel):
    """Event indicating a validated end call request."""
    
    reason: str
    validation_passed: bool
    original_reason: str
    timestamp: str


async def validate_end_call_request(message) -> Optional[ValidatedEndCall]:
    """
    Transform EndCall events through validation.
    
    This function intercepts EndCall events and validates them before allowing
    the call to actually end.
    """
    end_call_event = message.event
    context = getattr(message, 'context', None)
    
    if not context:
        logger.warning("No context available for end call validation")
        return ValidatedEndCall(
            reason="System error: no context available",
            validation_passed=False,
            original_reason=end_call_event.reason,
            timestamp=datetime.now().isoformat()
        )
    
    # Create validation node and check conditions
    validator = CallValidationNode()
    
    async for validation_result in validator.process_context(context):
        if validation_result.is_valid:
            logger.info("✅ End call validation passed")
            return ValidatedEndCall(
                reason=end_call_event.reason,
                validation_passed=True,
                original_reason=end_call_event.reason,
                timestamp=datetime.now().isoformat()
            )
        else:
            logger.info(f"❌ End call validation failed: {validation_result.missing_info}")
            # Instead of ending call, return None to prevent end call
            # The validation message will be sent as an agent response instead
            return None
    
    # Fallback - should not reach here
    return ValidatedEndCall(
        reason="Validation incomplete",
        validation_passed=False,
        original_reason=end_call_event.reason,
        timestamp=datetime.now().isoformat()
    )


async def generate_validation_response(message) -> Optional[AgentResponse]:
    """
    Generate agent response when end call validation fails.
    
    This creates an appropriate response to continue the conversation
    when the agent tries to end the call prematurely.
    """
    end_call_event = message.event
    context = getattr(message, 'context', None)
    
    if not context:
        return AgentResponse(content="I'd love to help you further. What else can I assist you with?")
    
    # Create validation node and get validation message
    validator = CallValidationNode()
    
    async for validation_result in validator.process_context(context):
        if not validation_result.is_valid and validation_result.validation_message:
            logger.info(f"🔄 Preventing premature end call, asking for: {validation_result.missing_info}")
            return AgentResponse(content=validation_result.validation_message)
    
    # Fallback response
    return AgentResponse(content="Is there anything else I can help you with today?")