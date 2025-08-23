"""ChatNode - Handles conversations and delegates complex queries to search agent."""

from typing import AsyncGenerator

from config import CHAT_MODEL_ID, CHAT_TEMPERATURE
from google.genai import Client
from google.genai.types import (
    FunctionDeclaration,
    GenerateContentConfig,
    GenerateContentResponse,
    ThinkingConfig,
    Tool,
)
from loguru import logger
from prompts import get_chat_system_prompt
from pydantic import BaseModel
from search import SearchAgent

from line import ConversationContext, ReasoningNode
from line.events import AgentResponse, EndCall, ToolCall
from line.tools.system_tools import EndCallArgs, EndCallTool, end_call
from line.utils.gemini_utils import convert_messages_to_gemini


class RunSearchAgentArgs(BaseModel):
    """Arguments for the run_search_agent function.

    Attributes:
        chat_msg: The chat agent's partial response to complete
    """

    chat_msg: str


class ChatNode(ReasoningNode):
    """Voice-optimized ReasoningNode using template method pattern with Gemini streaming.

    Properly inherits conversation management and tool handling from ReasoningNode
    while providing voice-specific Gemini streaming and interruption support.
    """

    def __init__(self, max_context_length: int = 100):
        """Initialize the Voice reasoning node with proven Gemini configuration.

        Args:
            max_context_length: Maximum number of conversation turns to keep.
        """
        self.system_prompt = get_chat_system_prompt()
        super().__init__(self.system_prompt, max_context_length)

        # Initialize Gemini client and configuration
        self.client = Client()
        self.generation_config = GenerateContentConfig(
            system_instruction=self.system_prompt,
            temperature=CHAT_TEMPERATURE,
            thinking_config=ThinkingConfig(thinking_budget=0),
            tools=[
                Tool(
                    function_declarations=[
                        FunctionDeclaration(
                            name="run_search_agent",
                            description="Get information from web search when needed",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "chat_msg": {
                                        "type": "string",
                                        "description": "Your partial response that needs completion with real-time data",
                                    }
                                },
                                "required": ["chat_msg"],
                            },
                        ),
                    ]
                ),
                EndCallTool.to_gemini_tool(),
            ],
        )

        self.search_agent = SearchAgent()

    async def process_context(
        self, context: ConversationContext
    ) -> AsyncGenerator[AgentResponse | ToolCall | EndCall, None]:
        """Voice-specific processing using Gemini streaming.

        Args:
            context: ConversationContext with messages, tools, and metadata

        Yields:
            AgentResponse: Streaming text chunks from Gemini
            ToolCall: Search tool calls and end call tool call when end_call function is called
        """
        messages = convert_messages_to_gemini(context.events)

        user_message = context.get_latest_user_transcript_message()
        if user_message:
            logger.info(f'🧠 Processing user message: "{user_message}"')
        full_response = ""
        stream: AsyncGenerator[
            GenerateContentResponse
        ] = await self.client.aio.models.generate_content_stream(
            model=CHAT_MODEL_ID,
            contents=messages,
            config=self.generation_config,
        )

        async for msg in stream:
            if msg.text:
                full_response += msg.text
                yield AgentResponse(content=msg.text)

            if msg.function_calls:
                for function_call in msg.function_calls:
                    if function_call.name == "run_search_agent":
                        args = RunSearchAgentArgs.model_validate(function_call.args)
                        logger.info(f'💬 Chat response: "{args.chat_msg}"')
                        yield AgentResponse(content=args.chat_msg + " ")

                        # Call the search agent and stream its response
                        logger.info("🔧 Calling search agent")

                        # Stream the search agent's response with message history excluding the current user message
                        async for item in self.search_agent.get_search_response(
                            user_message, args.chat_msg, messages[:-1]
                        ):
                            # Track search response text in full_response
                            if isinstance(item, AgentResponse):
                                full_response += item.content
                            yield item

                    elif function_call.name == EndCallTool.name():
                        goodbye_message = function_call.args.get("goodbye_message", "Goodbye!")
                        args = EndCallArgs(goodbye_message=goodbye_message)
                        logger.info(
                            f"🤖 End call tool called. Ending conversation with goodbye message: "
                            f"{args.goodbye_message}"
                        )
                        async for item in end_call(args):
                            yield item

        if full_response:
            logger.info(f'🤖 Agent response: "{full_response}" ({len(full_response)} chars)')
