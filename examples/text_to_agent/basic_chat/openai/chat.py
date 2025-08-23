"""ChatNode - Handles basic conversations using OpenAI."""

# Standard library
import json
from typing import AsyncGenerator

from config import CHAT_MODEL_ID
from loguru import logger
from openai import AsyncOpenAI
from openai._streaming import AsyncStream
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputItemDoneEvent,
    ResponseStreamEvent,
    ResponseTextDeltaEvent,
)
from prompts import get_chat_system_prompt

from line import ConversationContext, ReasoningNode
from line.events import AgentResponse, EndCall
from line.tools.system_tools import EndCallArgs, EndCallTool, end_call
from line.utils.openai_utils import convert_messages_to_openai


class ChatNode(ReasoningNode):
    """
    Voice-optimized ReasoningNode using template method pattern with OpenAI Responses API.

    Provides basic chat functionality without any external tools or search capabilities.
    """

    def __init__(self, max_context_length: int = 100):
        """
        Initialize the Voice reasoning node.

        Args:
            max_context_length: Maximum number of conversation turns to keep.
        """
        self.system_prompt = get_chat_system_prompt()
        super().__init__(self.system_prompt, max_context_length)
        # Initialize OpenAI client
        self.client = AsyncOpenAI()

    async def process_context(
        self, context: ConversationContext
    ) -> AsyncGenerator[AgentResponse | EndCall, None]:
        """
        Voice-specific processing using OpenAI Responses API.

        Implements the template method pattern by providing voice-optimized LLM
        processing while using the parent's conversation management.

        Args:
            context: ConversationContext with messages, tools, and metadata

        Yields:
            AgentResponse: Response text from OpenAI
            EndCall: End call event
        """
        # Convert context events to OpenAI format
        messages = convert_messages_to_openai(context.events)

        user_message = context.get_latest_user_transcript_message()
        if user_message:
            logger.info(f'🧠 Processing user message: "{user_message}"')

        # Ensure we have at least one user message for context
        if not any(msg.get("role") == "user" for msg in messages):
            logger.warning("No user message found in conversation")
            return

        # Make the non-streaming request using Responses API with optimizations
        stream: AsyncStream[ResponseStreamEvent] = await self.client.responses.create(
            model=CHAT_MODEL_ID,
            instructions=self.system_prompt,
            input=messages,
            tools=[EndCallTool.to_openai_tool()],
            reasoning={"effort": "minimal"},
            text={"verbosity": "low"},
            stream=True,
        )

        full_response = ""
        async for event in stream:
            if isinstance(event, ResponseTextDeltaEvent):
                full_response += event.delta
                yield AgentResponse(content=event.delta)

            if isinstance(event, ResponseOutputItemDoneEvent) and isinstance(
                event.item, ResponseFunctionToolCall
            ):
                if event.item.name == EndCallTool.name():
                    args = json.loads(event.item.arguments)
                    end_call_args = EndCallArgs(goodbye_message=args.get("goodbye_message", "Goodbye!"))
                    logger.info(f'🤖 Goodbye message: "{full_response}"')
                    async for item in end_call(end_call_args):
                        yield item

        if full_response:
            logger.info(f'🤖 Full response: "{full_response}" ({len(full_response)} chars)')
