"""
ChatNode - Voice-optimized ReasoningNode implementation for sales with leads
"""

from typing import AsyncGenerator

from config import (
    DEFAULT_MODEL_ID,
    DEFAULT_TEMPERATURE,
    EVENT_HANDLERS,
    SYSTEM_PROMPT,
    LeadsAnalysis,
    ResearchAnalysis,
)
from call_validation_node import CallValidationNode
from google.genai import types as gemini_types
from loguru import logger

from line.events import AgentResponse, EndCall, ToolCall
from line.nodes.conversation_context import ConversationContext
from line.nodes.reasoning import ReasoningNode
from line.utils.gemini_utils import convert_messages_to_gemini


class ChatNode(ReasoningNode):
    """
    Chat node for a conversational sales agent.
    """

    def __init__(
        self,
        system_prompt: str = SYSTEM_PROMPT,
        gemini_client=None,
        model_id: str = DEFAULT_MODEL_ID,
        temperature: float = DEFAULT_TEMPERATURE,
        max_context_length: int = 100,
        max_output_tokens: int = 1000,
    ):
        """
        Initialize the Voice reasoning node with proven Gemini configuration

        Args:
            system_prompt: System prompt for the LLM
            gemini_client: Google Gemini client instance
            model_id: Gemini model ID to use
            temperature: Temperature for generation
            max_context_length: Maximum number of conversation turns to keep
            max_output_tokens: Maximum output tokens
        """
        super().__init__(system_prompt=system_prompt, max_context_length=max_context_length)

        self.client = gemini_client
        self.model_id = model_id
        self.temperature = temperature
        self.validation_node = CallValidationNode()

        # Define the end_call tool for the sales agent
        end_call_tool = gemini_types.Tool(
            function_declarations=[
                gemini_types.FunctionDeclaration(
                    name="end_call",
                    description="End the call when the conversation is complete and all conditions are met",
                    parameters=gemini_types.Schema(
                        type=gemini_types.Type.OBJECT,
                        properties={
                            "reason": gemini_types.Schema(
                                type=gemini_types.Type.STRING,
                                description="Reason for ending the call"
                            )
                        },
                        required=["reason"]
                    )
                )
            ]
        )

        self.generation_config = gemini_types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            temperature=self.temperature,
            tools=[end_call_tool],
            max_output_tokens=max_output_tokens,
            thinking_config=gemini_types.ThinkingConfig(thinking_budget=0),
        )

        logger.info(f"ChatNode initialized with model: {model_id}")

    def _get_background_context(self, context: ConversationContext) -> str:
        """
        Extract background context from LeadsAnalysis and ResearchAnalysis events.
        
        This information will be added to the system prompt to inform the agent
        without being part of the conversation flow.
        """
        background_info = []
        
        # Get the latest leads analysis
        latest_leads = None
        latest_research = None
        
        for event in reversed(context.events):
            if isinstance(event, LeadsAnalysis) and latest_leads is None:
                latest_leads = event
            elif isinstance(event, ResearchAnalysis) and latest_research is None:
                latest_research = event
            
            # Stop once we have both or looked through enough events
            if latest_leads and latest_research:
                break
        
        if latest_leads:
            leads_info = latest_leads.leads_info
            company = leads_info.get('company', '')
            interest_level = leads_info.get('interest_level', 'unknown')
            pain_points = leads_info.get('pain_points', [])
            
            if company:
                background_info.append(f"LEAD INFO: Customer is from {company} with {interest_level} interest level")
                if pain_points:
                    background_info.append(f"IDENTIFIED NEEDS: {', '.join(pain_points)}")
        
        if latest_research:
            company_info = latest_research.company_info
            overview = company_info.get('company_overview', '')
            sales_ops = company_info.get('sales_opportunities', [])
            key_people = company_info.get('key_people', [])
            
            if overview and 'unavailable' not in overview.lower():
                background_info.append(f"COMPANY RESEARCH: {overview}")
                if sales_ops:
                    background_info.append(f"SALES OPPORTUNITIES: {', '.join(sales_ops)}")
                if key_people:
                    background_info.append(f"KEY CONTACTS: {', '.join(key_people)}")
        
        return " | ".join(background_info) if background_info else ""

    async def process_context(self, context: ConversationContext) -> AsyncGenerator[AgentResponse, None]:
        """
        Process the conversation context and yield responses from Gemini.

        Yields:
            AgentResponse: Text chunks from Gemini
        """
        if not context.events:
            logger.info("No messages to process")
            return

        # Filter out background analysis events from conversation history
        conversation_events = [
            event for event in context.events 
            if not isinstance(event, (LeadsAnalysis, ResearchAnalysis))
        ]
        
        # Convert conversation events to messages (excluding background analysis)
        messages = convert_messages_to_gemini(conversation_events, handlers=EVENT_HANDLERS)

        # Get background context from analysis events
        background_context = self._get_background_context(context)
        
        # If we have background context, modify the system instruction
        config = self.generation_config
        if background_context:
            enhanced_system_prompt = f"{self.system_prompt}\n\n=== CURRENT CONTEXT ===\n{background_context}\n\nUse this context to personalize your responses but do not mention that you analyzed their information."
            # Create new config with enhanced system prompt but keep the same tools
            config = gemini_types.GenerateContentConfig(
                system_instruction=enhanced_system_prompt,
                temperature=self.temperature,
                tools=self.generation_config.tools,  # Keep the end_call tool
                max_output_tokens=1000,
                thinking_config=gemini_types.ThinkingConfig(thinking_budget=0),
            )

        user_message = context.get_latest_user_transcript_message()
        if user_message:
            logger.info(f'🧠 Processing user message: "{user_message}"')
        
        if background_context:
            logger.info(f'🔍 Background context: {background_context}')

        full_response = ""
        stream: AsyncGenerator[
            gemini_types.GenerateContentResponse
        ] = await self.client.aio.models.generate_content_stream(
            model=self.model_id,
            contents=messages,
            config=config,
        )

        async for msg in stream:
            if msg.text:
                full_response += msg.text
                yield AgentResponse(content=msg.text)
            
            # Handle tool calls
            if msg.candidates and len(msg.candidates) > 0:
                candidate = msg.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            func_call = part.function_call
                            if func_call.name == "end_call":
                                reason = func_call.args.get('reason', 'Call completed')
                                logger.info(f"🔚 Agent requested to end call: {reason}")
                                
                                # Validate end call conditions
                                async for validation_result in self.validation_node.process_context(context):
                                    if validation_result.is_valid:
                                        logger.info("✅ End call validation passed")
                                        yield EndCall(reason=reason)
                                    else:
                                        logger.info(f"❌ End call validation failed: {validation_result.missing_info}")
                                        if validation_result.validation_message:
                                            yield AgentResponse(content=validation_result.validation_message)

        if full_response:
            logger.info(f'🤖 Agent response: "{full_response}" ({len(full_response)} chars)')
