"""ChatNode - Handles basic conversations using Gemini."""

from typing import AsyncGenerator

from config import CHAT_MODEL_ID, CHAT_TEMPERATURE
from google.genai import Client
from google.genai.types import GenerateContentConfig, GenerateContentResponse, ThinkingConfig
from loguru import logger
from prompts import GOODBYE_PROMPT, get_chat_system_prompt

from line import ConversationContext, ReasoningNode
from line.events import AgentResponse, EndCall
from line.tools.system_tools import EndCallArgs, EndCallTool, end_call
from line.utils.gemini_utils import convert_messages_to_gemini


class ChatNode(ReasoningNode):
    """Voice-optimized ReasoningNode for basic chat using Gemini streaming.

    Provides simple conversation capabilities without external tools or search.
    """

    def __init__(self, max_context_length: int = 100):
        """Initialize the Voice reasoning node with proven Gemini configuration.

        Args:
            max_context_length: Maximum number of conversation turns to keep.
        """
        self.system_prompt = get_chat_system_prompt()
        super().__init__(self.system_prompt, max_context_length)

        self.tools = []

        # Add the EndCallTool if we don't have a goodbye prompt for ending the call
        if not GOODBYE_PROMPT:
            self.tools.append(EndCallTool.to_gemini_tool())

        # Initialize Gemini client and configuration
        self.client = Client()
        self.generation_config = GenerateContentConfig(
            system_instruction=self.system_prompt,
            temperature=CHAT_TEMPERATURE,
            thinking_config=ThinkingConfig(thinking_budget=0),
            tools=self.tools,
        )

    async def process_context(
        self, context: ConversationContext
    ) -> AsyncGenerator[AgentResponse | EndCall, None]:
        """Basic chat processing using Gemini streaming.

        Args:
            context: ConversationContext with messages, tools, and metadata

        Yields:
            AgentResponse: Streaming text chunks from Gemini
            EndCall: End call event
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

        if GOODBYE_PROMPT and full_response.endswith("Goodbye!"):
            # If we have a goodbye prompt, use the Goodbye! message to end the call
            logger.info("🤖 Goodbye message detected. Ending call")
            yield EndCall()
