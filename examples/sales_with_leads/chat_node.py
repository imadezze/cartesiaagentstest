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
    
    def _should_present_value_proposition(self, context: ConversationContext) -> tuple[bool, str]:
        """
        Check if conditions are met to present value proposition.
        
        Returns:
            tuple: (should_present, company_name)
        """
        # Get latest leads and research info
        latest_leads = None
        latest_research = None
        
        for event in reversed(context.events):
            if isinstance(event, LeadsAnalysis) and latest_leads is None:
                latest_leads = event
            elif isinstance(event, ResearchAnalysis) and latest_research is None:
                latest_research = event
            
            if latest_leads and latest_research:
                break
        
        # Check if we have both company name and research
        if latest_leads and latest_research:
            company = latest_leads.leads_info.get('company', '').strip()
            if company:
                # Check if we've already presented value prop for this company
                # Look for recent agent responses containing value proposition language
                recent_agent_responses = []
                for event in reversed(context.events[-10:]):  # Check last 10 events
                    if hasattr(event, 'content') and event.__class__.__name__ == 'AgentResponse':
                        recent_agent_responses.append(event.content.lower())
                        if len(recent_agent_responses) >= 3:
                            break
                
                # Check if we already presented SPECIFIC value prop (not generic)
                value_prop_indicators = [
                    "here's exactly how cartesia can help " + company.lower(),
                    "cartesia can specifically help " + company.lower(),
                    "knowing " + company.lower() + "'s challenges",
                    company.lower() + " struggles with",
                    "for " + company.lower() + " specifically",
                    "your challenges at " + company.lower()
                ]
                
                already_presented = any(
                    any(indicator in response for indicator in value_prop_indicators)
                    for response in recent_agent_responses
                )
                
                return not already_presented, company
        
        return False, ""

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

        # Check if we should present value proposition
        should_present_vp, company_name = self._should_present_value_proposition(context)
        
        # Get background context from analysis events
        background_context = self._get_background_context(context)
        
        # If we have background context, modify the system instruction
        config = self.generation_config
        enhanced_system_prompt = self.system_prompt
        
        if background_context:
            enhanced_system_prompt += f"\n\n=== CURRENT CONTEXT ===\n{background_context}\n\nUse this context to personalize your responses but do not mention that you analyzed their information."
            
        # Get user message first to check for questions
        user_message = context.get_latest_user_transcript_message()
        if user_message:
            logger.info(f'🧠 Processing user message: "{user_message}"')
            
        # Check if user is asking a question that needs to be answered
        user_asking_question = False
        if user_message:
            question_indicators = ['how', 'what', 'why', 'when', 'where', 'can you', 'could you', 'is it possible', '?']
            user_asking_question = any(indicator in user_message.lower() for indicator in question_indicators)

        if should_present_vp:
            enhanced_system_prompt += f"\n\n🚨 CRITICAL OVERRIDE: You have company information ({company_name}) AND research data available. You MUST:\n1. IMMEDIATELY present how Cartesia specifically helps {company_name}\n2. Reference their exact pain points from the research analysis\n3. Give concrete examples of how our voice AI solves their problems\n4. NEVER ask for email/contact info until you've presented the solution\n5. Answer any user questions about the solution before collecting contact info\n\nSTOP asking for contact information and START presenting the tailored value proposition!"
            
        if user_asking_question:
            enhanced_system_prompt += f"\n\n🚨🚨 CRITICAL PRIORITY: The user just asked a question: '{user_message}'. YOU MUST:\n1. STOP all other activities immediately\n2. ANSWER their specific question directly and thoroughly\n3. NEVER repeat previous wrap-up questions\n4. NEVER ask for contact information\n5. Focus ONLY on answering their question about Cartesia's voice AI implementation\n\nIGNORE all other instructions until you have fully answered their question!"
        
        # Get the latest leads analysis to check for critical information
        leads_analysis = None
        for event in reversed(context.events):
            if isinstance(event, LeadsAnalysis):
                leads_analysis = event
                break
        
        # Check if critical information is missing
        missing_critical_info = True
        if leads_analysis and leads_analysis.leads_info:
            name = leads_analysis.leads_info.get('name', '').strip()
            company = leads_analysis.leads_info.get('company', '').strip()
            email = leads_analysis.leads_info.get('email', '').strip()
            missing_critical_info = not name or not company or not email
            
            if missing_critical_info:
                missing_fields = []
                if not name: missing_fields.append("personal name")
                if not company: missing_fields.append("company name")
                if not email: missing_fields.append("email address")
                
                enhanced_system_prompt += f"\n\n🚨 DISCOVERY REQUIRED: You are missing {', '.join(missing_fields)}. You MUST:\n1. Continue the conversation to gather this information\n2. Ask appropriate follow-up questions about their needs\n3. NEVER try to end the conversation\n4. Focus on discovery and understanding their pain points\n5. Ask for company name next if they've expressed business needs\n\nDO NOT try to wrap up - continue building rapport and gathering information!"
        # Remove end_call tool when user asks questions OR when critical info is missing
        should_remove_endcall = user_asking_question or missing_critical_info
        tools_to_use = [] if should_remove_endcall else self.generation_config.tools
        
        if missing_critical_info:
            logger.info(f"🚫 Removing end_call tool - missing critical info: name={bool(name if 'name' in locals() else False)}, company={bool(company if 'company' in locals() else False)}, email={bool(email if 'email' in locals() else False)}")
        
        # Create new config if system prompt changed OR if we need to modify tools
        if enhanced_system_prompt != self.system_prompt or should_remove_endcall:
            config = gemini_types.GenerateContentConfig(
                system_instruction=enhanced_system_prompt,
                temperature=self.temperature,
                tools=tools_to_use,
                max_output_tokens=1000,
                thinking_config=gemini_types.ThinkingConfig(thinking_budget=0),
            )
        
        if background_context:
            logger.info(f'🔍 Background context: {background_context}')
            
        if should_present_vp:
            logger.info(f'💡 VALUE PROPOSITION TRIGGER: Should present solution for {company_name}')
            
        if user_asking_question:
            logger.info(f'❓ USER QUESTION DETECTED: "{user_message}" - Must answer before proceeding')

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
