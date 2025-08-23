from datetime import datetime, timezone
import json
from typing import AsyncGenerator

from config import DEFAULT_MODEL_ID, EVENT_HANDLERS, LEADS_EXTRACTION_PROMPT, LeadsAnalysis
from google.genai import types as gemini_types
from loguru import logger
from pydantic import BaseModel, Field

from line.nodes.conversation_context import ConversationContext
from line.nodes.reasoning import ReasoningNode
from line.utils.gemini_utils import convert_messages_to_gemini


class LeadsInfo(BaseModel):
    """Schema for extracted leads information."""

    name: str = Field(description="Contact's full name")
    company: str = Field(description="Company or organization name")
    email: str = Field(default="", description="Email address if mentioned")
    phone: str = Field(default="", description="Phone number if mentioned")
    interest_level: str = Field(description="Level of interest: high, medium, low")
    pain_points: list[str] = Field(default_factory=list, description="Mentioned challenges or needs")
    budget_mentioned: bool = Field(default=False, description="Whether budget was discussed")
    next_steps: str = Field(default="", description="Agreed upon next steps or follow-up")
    notes: str = Field(description="Additional relevant notes about the conversation")


class LeadsExtractionNode(ReasoningNode):
    """
    Node that extracts leads information from conversations.

    The goal of this node is to trigger every time a user stops speaking, and use the conversation context from the user
    to extract leads information.
    """

    def __init__(
        self,
        gemini_client,
        model_id: str = DEFAULT_MODEL_ID,
        temperature: float = 0.1,
        max_context_length: int = 100,
        max_output_tokens: int = 1000,
    ):
        super().__init__(system_prompt=LEADS_EXTRACTION_PROMPT, max_context_length=max_context_length)

        self.client = gemini_client
        self.model_id = model_id
        self.temperature = temperature

        # Create generation config for leads extraction
        self.generation_config = gemini_types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            temperature=self.temperature,
            tools=[],  # No tools needed for leads extraction
            max_output_tokens=max_output_tokens,
            thinking_config=gemini_types.ThinkingConfig(thinking_budget=0),
        )

        logger.info(f"🔍 LeadsExtractionNode initialized with model: {model_id}, node_id: {self.id}")

    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from LLM response.

        Most LMs, even if prompted to return JSON, can return a markdown code block. If a markdown code block is returned,
        we will be unable to parse the JSON directly, this function is a safe parser to pull the json string itself out of
        weirdly structured markdown blocks.
        """
        response = response.strip()

        # Check if response is wrapped in markdown code blocks
        if response.startswith("```json\n") and response.endswith("\n```"):
            # Extract content between ```json and ``` (with newlines)
            json_str = response[8:-4].strip()  # Remove ```json\n and \n```
            return json_str
        elif response.startswith("```json") and response.endswith("```"):
            # Extract content between ```json and ``` (without newlines)
            json_str = response[7:-3].strip()  # Remove ```json and ```
            return json_str
        elif response.startswith("```\n") and response.endswith("\n```"):
            # Extract content between ``` and ``` (generic code block with newlines)
            json_str = response[4:-4].strip()
            return json_str
        elif response.startswith("```") and response.endswith("```"):
            # Extract content between ``` and ``` (generic code block)
            json_str = response[3:-3].strip()
            return json_str
        else:
            # Response is already raw JSON
            return response

    async def process_context(self, context: ConversationContext) -> AsyncGenerator[LeadsAnalysis, None]:
        """
        Extract leads information from the conversation context and yield a LeadsAnalysis event.

        Args:
            context: Conversation context with events.

        Yields:
            LeadsAnalysis: Leads extraction results.
        """
        logger.info("🔍 Starting leads extraction analysis")

        if not context.events:
            logger.info("No conversation events to analyze for leads")
            return

        try:
            # Use the SAME pattern as ChatNode - convert context.events directly
            messages = convert_messages_to_gemini(context.events, handlers=EVENT_HANDLERS)

            logger.info(f"🔍 Analyzing conversation with {len(context.events)} events")

            # Generate leads extraction analysis using same pattern as ChatNode
            extracted_info = ""
            stream: AsyncGenerator[
                gemini_types.GenerateContentResponse
            ] = await self.client.aio.models.generate_content_stream(
                model=self.model_id,
                contents=messages,
                config=self.generation_config,
            )

            async for chunk in stream:
                if chunk.text:
                    extracted_info += chunk.text

            # Process the extracted information
            if extracted_info:
                extracted_info = extracted_info.strip()

                try:
                    # Extract JSON from response (handle markdown code blocks)
                    json_str = self._extract_json_from_response(extracted_info)

                    # Parse as JSON to validate structure
                    leads_data = json.loads(json_str)
                    leads_info = LeadsInfo.model_validate(leads_data)

                    logger.info(f"Validated leads info: {leads_info}")

                    # Yield LeadsAnalysis event with structured leads information
                    yield LeadsAnalysis(
                        leads_info=leads_info.model_dump(),
                        confidence="high",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )

                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse leads extraction as JSON: {e}")

                    # Yield LeadsAnalysis event even if parsing failed
                    yield LeadsAnalysis(
                        leads_info={"raw_extraction": extracted_info},
                        confidence="low",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
            else:
                logger.warning("No leads information extracted from conversation")

        except Exception as e:
            logger.exception(f"Error during leads extraction: {e}")

        logger.info("Finished leads extraction analysis")
