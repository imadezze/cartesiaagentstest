"""ChatNode - Handles basic conversations using OpenAI Realtime API."""

import json
import os
import ssl
from typing import AsyncGenerator

from config import CHAT_MODEL_ID, CHAT_TEMPERATURE
from loguru import logger
from prompts import get_chat_system_prompt
import websockets

from line import ConversationContext, ReasoningNode
from line.events import AgentResponse, EndCall
from line.tools.system_tools import EndCallArgs, EndCallTool, end_call


class ChatNode(ReasoningNode):
    """
    Voice-optimized ReasoningNode using OpenAI Realtime API with text-only mode.

    Provides basic chat functionality using WebSocket connection to OpenAI's Realtime API
    configured for text input/output only.
    """

    def __init__(self, initial_message: str | None = None, max_context_length: int = 100):
        """
        Initialize the Realtime API reasoning node.

        Args:
            max_context_length: Maximum number of conversation turns to keep.
        """
        self.system_prompt = get_chat_system_prompt()
        if initial_message:
            self.system_prompt += f"\n\nYour initial message to the user was: {initial_message}"
        super().__init__(self.system_prompt, max_context_length)
        self.websocket = None
        self.api_key = None

    async def init(self) -> "ChatNode":
        """Initialize the node and establish WebSocket connection.

        Returns:
            Self reference for method chaining.
        """
        # Get API key from environment
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # Establish persistent WebSocket connection
        await self._connect_websocket()

        logger.info("ChatNode initialized for OpenAI Realtime API")
        return self

    async def _connect_websocket(self):
        """Establish WebSocket connection to OpenAI Realtime API."""
        if self.websocket and self.websocket.close_code is None:
            return

        url = f"wss://api.openai.com/v1/realtime?model={CHAT_MODEL_ID}"
        headers = [
            ("Authorization", f"Bearer {self.api_key}"),
            ("OpenAI-Beta", "realtime=v1"),
        ]

        # Create SSL context
        ssl_context = ssl.create_default_context()

        self.websocket = await websockets.connect(
            url,
            additional_headers=headers,
            ssl=ssl_context,
            ping_interval=20,
            ping_timeout=10,
        )
        logger.info("🔌 Connected to OpenAI Realtime API")

        # Configure session for text-only mode
        await self._configure_session()

    async def _configure_session(self):
        """Configure the Realtime API session for text-only mode."""
        end_call_tool = EndCallTool.to_openai_tool()
        # Remove strict flag from the tool since it's not supported by the Realtime API
        end_call_tool.pop("strict")

        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text"],  # Text-only mode
                "instructions": self.system_prompt,
                "tools": [end_call_tool],
                "tool_choice": "auto",
                "temperature": CHAT_TEMPERATURE,
                "max_response_output_tokens": 4096,
                # The following audio parameters are required even for text-only mode
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200,
                },
            },
        }

        await self.websocket.send(json.dumps(session_config))
        logger.info("📝 Configured session for text-only mode")

    async def _send_text_message(self, content: str):
        """Send a text message to the Realtime API."""
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": content}],
            },
        }

        await self.websocket.send(json.dumps(message))

        # Trigger response generation
        response_create = {
            "type": "response.create",
            "response": {
                "modalities": ["text"],
            },
        }

        await self.websocket.send(json.dumps(response_create))

    async def _process_websocket_events(self) -> AsyncGenerator[AgentResponse | EndCall, None]:
        """Process events from the WebSocket connection."""
        full_response = ""

        async for message in self.websocket:
            event = json.loads(message)
            event_type = event.get("type", "")

            # Handle text delta events (streaming response)
            if event_type == "response.text.delta":
                delta = event.get("delta", "")
                if delta:
                    full_response += delta
                    yield AgentResponse(content=delta)

            # Handle text completion
            elif event_type == "response.text.done":
                text = event.get("text", "")
                if text and not full_response.endswith(text):
                    # Sometimes the full text comes in the done event
                    remaining = text[len(full_response) :]
                    if remaining:
                        full_response += remaining
                        yield AgentResponse(content=remaining)

            # Handle tool call completion
            elif event_type == "response.function_call_arguments.done":
                function_name = event.get("name", "")

                if function_name == EndCallTool.name():
                    # Parse function call arguments
                    args_json = event.get("arguments", "{}")
                    args = json.loads(args_json)
                    goodbye_message = args.get("goodbye_message", "Goodbye!")

                    logger.info(f'💬 Goodbye message: "{goodbye_message}"')
                    end_call_args = EndCallArgs(goodbye_message=goodbye_message)
                    async for item in end_call(end_call_args):
                        yield item

            # Handle response completion
            elif event_type == "response.done":
                logger.info(f'🤖 Complete response: "{full_response}" ({len(full_response)} chars)')
                break

            # Handle errors
            elif event_type == "error":
                error_msg = event.get("error", {})
                logger.error(f"❌ OpenAI Realtime API error: {error_msg}")
                raise RuntimeError(f"OpenAI Realtime API error: {error_msg}")

    async def process_context(
        self, context: ConversationContext
    ) -> AsyncGenerator[AgentResponse | EndCall, None]:
        """
        Process conversation context using OpenAI Realtime API.

        Args:
            context: ConversationContext with messages, tools, and metadata

        Yields:
            AgentResponse: Streaming text chunks from OpenAI Realtime API
            EndCall: End call event when goodbye is triggered
        """
        user_message = context.get_latest_user_transcript_message()
        if not user_message:
            logger.warning("No user message found in conversation")
            return

        logger.info(f'🧠 Processing user message: "{user_message}"')

        # Check if WebSocket connection is still alive
        if not self.websocket or self.websocket.close_code is not None:
            logger.warning("🔌 WebSocket connection lost, reconnecting...")
            await self._connect_websocket()

        # Send the user's message
        await self._send_text_message(user_message)

        # Process response events
        async for event in self._process_websocket_events():
            yield event

    async def cleanup(self):
        """Clean up resources."""
        if self.websocket and self.websocket.close_code is None:
            await self.websocket.close()
            logger.info("🔌 WebSocket connection closed during cleanup")
