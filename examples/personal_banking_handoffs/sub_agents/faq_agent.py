"""FAQ Agent for Personal Banking Customer Support.

This agent handles general information queries and frequently asked questions
using a chat/search pattern with web search capabilities.
"""

from typing import AsyncGenerator, List, Optional, Union

from config import BANK_NAME
from context import BankContext
from google.genai import Client
from google.genai.types import (
    Content,
    FunctionDeclaration,
    GenerateContentConfig,
    Tool,
)
from loguru import logger
from prompts import make_voice_system_prompt
from pydantic import BaseModel

from line.events import AgentResponse, ToolCall, ToolResult
from line.tools.system_tools import EndCallTool

from .faq_search_agent import FAQSearchAgent
from .sub_agent import SubAgent

# FAQ agent LLM settings
FAQ_CHAT_MODEL_ID = "gemini-2.5-flash"

# FAQ chat agent prompt
FAQ_CHAT_PROMPT = f"""
You are a {BANK_NAME} customer service specialist for general information and frequently asked questions.

### Your Role:
- Provide helpful, accurate information about {BANK_NAME} services, policies, and general banking
- Answer common questions about account types, fees, branches, hours, website navigation
- For real-time information (rates, current promotions, specific policies), use the search tool
- If customers need account-specific help or transactions, route them to our banking services team

### Your Style:
- Be helpful, professional, and informative
- Provide clear, concise answers
- When you don't have current information, use the search tool to get real-time data
- If the question requires account access or transactions, explain that you'll connect them to banking services

### Use the search tool when you need:
- Current interest rates, fees, or promotional offers
- Recent policy changes or updates
- Specific branch information or hours
- Current website features or navigation help
- Any information that changes frequently

### Example Interactions:
Customer: "What are your current mortgage rates?"
You: "The current mortgage rates from {BANK_NAME} are..." [Use search tool]

Customer: "How do I reset my online banking password?"
You: "Here's how to reset your online banking password..." [Use search tool for current process]

Customer: "I need to check my account balance"
You: "For account-specific services like checking your balance, I'll connect you with our banking services team who can help with your account."
"""


# Initial FAQ message
FAQ_INITIAL_MESSAGE = f"I can help answer general questions about {BANK_NAME}. What would you like to know?"


##################################################
####           Tool Argument Models           ####
##################################################


class RunFAQSearchArgs(BaseModel):
    """Arguments for the run_faq_search function.

    Attributes:
        chat_msg: The chat agent's partial response to complete
    """

    chat_msg: str


##################################################
####               FAQ Agent                   ####
##################################################


class FAQAgent(SubAgent):
    """Agent for handling general questions and FAQ with web search capabilities.

    This agent handles:
    - General {BANK_NAME} information
    - Website navigation help
    - Service information
    - Current rates and policies
    - Non-transactional support

    Uses a chat/search pattern where complex queries are delegated to a search agent.
    """

    def __init__(self, context: BankContext):
        """Initialize the FAQ agent.

        Args:
            context: The bank context object containing user and bank details
        """
        super().__init__(context)
        self.client = Client()
        self.system_prompt = FAQ_CHAT_PROMPT

        self.generation_config = GenerateContentConfig(
            system_instruction=make_voice_system_prompt(self.system_prompt),
            tool_config={},
            tools=[
                Tool(
                    function_declarations=[
                        FunctionDeclaration(
                            name="run_faq_search",
                            description=f"Get current {BANK_NAME} information from web search when you need real-time data like rates, policies, branch info, or current website features",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "chat_msg": {
                                        "type": "string",
                                        "description": f"Your partial response that needs completion with real-time {BANK_NAME} data",
                                    }
                                },
                                "required": ["chat_msg"],
                            },
                        ),
                        FunctionDeclaration(
                            name="handoff_to_transaction",
                            description="Route customer to banking services for account access, transactions, balances, or account-specific help",
                        ),
                    ]
                ),
                EndCallTool.to_gemini_tool(),
            ],
        )

        self.search_agent = FAQSearchAgent()
        logger.info("❓ FAQ agent initialized")

    async def initial_message(
        self, user_message: Optional[str] = None, message_history: Optional[List[Content]] = None
    ) -> AsyncGenerator[Union[AgentResponse, ToolResult], None]:
        """Return initial message for FAQ agent.

        Args:
            user_message: The latest message from the user (optional)
            message_history: Previous conversation messages in Gemini format (optional)

        Yields:
            AgentResponse: Initial messages or responses from generate
            ToolCall: Handoff to transaction agent
            ToolResult: Search tool call result
        """
        if user_message and message_history:
            # If we have input, call generate to handle the full conversation
            async for item in self.generate(user_message, message_history):
                yield item
        else:
            # Simple initial message
            yield AgentResponse(content=FAQ_INITIAL_MESSAGE)

    async def generate(
        self, user_message: str, message_history: list[Content]
    ) -> AsyncGenerator[Union[AgentResponse, ToolCall, ToolResult], None]:
        """Handle general information requests with search capabilities.

        Args:
            user_message: The latest user message
            message_history: Previous conversation messages

        Yields:
            AgentResponse: FAQ responses with real-time data
            ToolCall: Search tool calls and handoff calls
        """
        logger.info(f"❓ FAQ agent processing: {user_message}")

        # Generate response using Gemini
        full_response = ""
        response = await self.client.aio.models.generate_content(
            model=FAQ_CHAT_MODEL_ID,
            contents=message_history,
            config=self.generation_config,
        )

        # Yield text response if present
        if response.text:
            yield AgentResponse(content=response.text)
            full_response += response.text
            logger.info(f'❓ FAQ agent response: "{response.text}" ({len(response.text)} chars)')

        # Process function calls
        if response.function_calls:
            for function_call in response.function_calls:
                logger.info(f"❓ FAQ agent tool call: {function_call.name}")

                if function_call.name == EndCallTool.name():
                    logger.info("❓ FAQ agent end call requested")
                    yield ToolCall(tool_name=function_call.name, tool_args=function_call.args)
                elif function_call.name == "run_faq_search":
                    args = RunFAQSearchArgs.model_validate(function_call.args)
                    logger.info(f'❓ FAQ chat response: "{args.chat_msg}"')
                    full_response += args.chat_msg + " "
                    yield AgentResponse(content=args.chat_msg + " ")

                    # Call the search agent and stream its response
                    logger.info("🔧 Calling FAQ search agent")

                    # Stream the search agent's response with message history excluding the current user message
                    async for item in self.search_agent.get_search_response(
                        user_message, args.chat_msg, message_history[:-1]
                    ):
                        # Track search response text in full_response
                        if isinstance(item, AgentResponse):
                            full_response += item.content
                        yield item

                elif function_call.name == "handoff_to_transaction":
                    yield ToolCall(tool_name="handoff_to_transaction")

        if full_response:
            logger.info(f'❓ FAQ agent response: "{full_response}" ({len(full_response)} chars)')
