"""ChatNode - Handles basic conversations using Gemini Live."""

from typing import AsyncGenerator

from config import CHAT_MODEL_ID, CHAT_TEMPERATURE
import google.genai as genai
from google.genai.types import LiveConnectConfig
from loguru import logger
from prompts import get_chat_system_prompt

from line import ConversationContext, ReasoningNode
from line.events import AgentResponse, EndCall
from line.tools.system_tools import EndCallArgs, EndCallTool, end_call
from line.utils.gemini_utils import convert_messages_to_gemini


class ChatNode(ReasoningNode):
    """Voice-optimized ReasoningNode using template method pattern with Gemini streaming.

    Properly inherits conversation management from ReasoningNode
    while providing voice-specific Gemini streaming and basic chat functionality.

    Architecture:
    - Uses ReasoningNode's template method generate() for consistent flow
    - Implements () for voice-optimized Gemini streaming
    - Provides basic chat functionality without external tools
    """

    def __init__(self, max_context_length: int = 100):
        """Initialize the Voice reasoning node with proven Gemini configuration.

        Args:
            max_context_length: Maximum number of conversation turns to keep.
        """
        self.system_prompt = get_chat_system_prompt()
        super().__init__(self.system_prompt, max_context_length)

        # Initialize Gemini client with Live API support
        self.client = genai.Client(http_options={"api_version": "v1alpha"})

        # Create Live API configuration for basic chat
        self.live_config = LiveConnectConfig(
            system_instruction=self.system_prompt,
            temperature=CHAT_TEMPERATURE,
            response_modalities=["TEXT"],
            tools=[EndCallTool.to_gemini_tool()],
        )

        logger.info("ChatNode initialized with Live API for basic chat")

    async def process_context(
        self, context: ConversationContext
    ) -> AsyncGenerator[AgentResponse | EndCall, None]:
        """Voice-specific processing using Gemini streaming.

        Implements the template method pattern by providing voice-optimized LLM
        processing while using the parent's conversation management.

        Args:
            context: ConversationContext with messages, tools, and metadata

        Yields:
            AgentResponse: Streaming text chunks from Gemini
            EndCall: End call event
        """
        messages = convert_messages_to_gemini(context.events, text_events_only=True)
        user_message = context.get_latest_user_transcript_message()
        if user_message:
            logger.info(f'🧠 Processing user message: "{user_message}"')

        full_response = ""
        async with self.client.aio.live.connect(model=CHAT_MODEL_ID, config=self.live_config) as stream:
            await stream.send_client_content(turns=messages, turn_complete=True)

            async for msg in stream.receive():
                if msg.text:
                    full_response += msg.text
                    yield AgentResponse(content=msg.text)

                if msg.tool_call:
                    for function_call in msg.tool_call.function_calls:
                        if function_call.name == EndCallTool.name():
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
