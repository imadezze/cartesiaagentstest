"""ChatNode - Handles conversations with integrated web search capabilities."""

import re
from typing import AsyncGenerator

from config import CHAT_MODEL_ID, CHAT_TEMPERATURE
import google.genai as genai
from google.genai.types import LiveConnectConfig, LiveServerMessage
from loguru import logger
from prompts import get_chat_system_prompt

from line import ConversationContext, ReasoningNode
from line.events import AgentResponse, EndCall, ToolResult
from line.utils.gemini_utils import convert_messages_to_gemini


class ChatNode(ReasoningNode):
    """Voice-optimized ReasoningNode with integrated web search using Gemini Live API.

    This node handles conversations and performs web searches directly through Gemini's
    Google Search grounding, providing simple search tool call observability while
    returning message text directly.
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

        # Create Live API configuration with Google Search tool and end_call tool
        self.live_config = LiveConnectConfig(
            system_instruction=self.system_prompt,
            temperature=CHAT_TEMPERATURE,
            tools=[{"google_search": {}}],
            response_modalities=["TEXT"],
        )

        logger.info("ChatNode initialized with Live API and Google Search")

    def _parse_search_queries(self, msg: LiveServerMessage) -> set[str]:
        """Parse search queries from message content."""
        queries = set()

        # Parse queries from grounding metadata
        if (
            msg.server_content
            and msg.server_content.grounding_metadata
            and msg.server_content.grounding_metadata.web_search_queries
        ):
            queries.update(msg.server_content.grounding_metadata.web_search_queries)

        # Parse queries from executable_code parts
        if msg.server_content and msg.server_content.model_turn:
            for part in msg.server_content.model_turn.parts:
                if hasattr(part, "executable_code") and part.executable_code:
                    code = part.executable_code.code
                    # Extract queries from google_search.search(queries=[...]) pattern
                    pattern = r"google_search\.search\(queries=\[(.*?)\]"
                    match = re.search(pattern, code)
                    if match:
                        queries_str = match.group(1)
                        # Extract individual quoted strings
                        query_pattern = r'"([^"]*)"'
                        extracted_queries = re.findall(query_pattern, queries_str)
                        queries.update(extracted_queries)

        return queries

    def _parse_search_pages(self, msg: LiveServerMessage) -> set[str]:
        """Parse search page titles from message grounding metadata."""
        pages = set()

        # Parse page titles from grounding metadata
        if (
            msg.server_content
            and msg.server_content.grounding_metadata
            and msg.server_content.grounding_metadata.grounding_chunks
        ):
            for chunk in msg.server_content.grounding_metadata.grounding_chunks:
                if chunk.web and chunk.web.title:
                    pages.add(chunk.web.uri)

        return pages

    async def process_context(
        self, context: ConversationContext
    ) -> AsyncGenerator[AgentResponse | ToolResult | EndCall, None]:
        """Voice-specific processing using Gemini streaming with integrated search.

        Args:
            context: ConversationContext with messages, tools, and metadata

        Yields:
            AgentResponse: Streaming text chunks from Gemini
            ToolResult: Google Search tool result with queries and pages (for observability)
            EndCall: End call event
        """
        messages = convert_messages_to_gemini(context.events, text_events_only=True)
        user_message = context.get_latest_user_transcript_message()
        if user_message:
            logger.info(f'🧠 Processing user message: "{user_message}"')

        full_response = ""
        search_queries = set()
        search_pages = set()

        async with self.client.aio.live.connect(model=CHAT_MODEL_ID, config=self.live_config) as stream:
            await stream.send_client_content(turns=messages, turn_complete=True)

            async for msg in stream.receive():
                if msg.text:
                    full_response += msg.text
                    yield AgentResponse(content=msg.text)

                # Extract search queries and pages from the message
                search_queries.update(self._parse_search_queries(msg))
                search_pages.update(self._parse_search_pages(msg))

        # Yield search tool call for observability if any search was performed
        if search_queries or search_pages:
            logger.info(f"🔍 Search queries used: {list(search_queries)}")
            logger.info(f"📄 Pages referenced: {list(search_pages)}")

            yield ToolResult(
                tool_name="google_search",
                tool_args={"queries": list(search_queries)},
                result={"pages": list(search_pages)},
            )

        if full_response:
            logger.info(f'🤖 Agent response: "{full_response}" ({len(full_response)} chars)')

        if full_response.endswith("Goodbye!"):
            logger.info("🤖 Goodbye message detected. Ending call")
            yield EndCall()
