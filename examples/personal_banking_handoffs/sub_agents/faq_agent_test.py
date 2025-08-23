"""Tests for the FAQ agent."""

from context import BankContext
from google.genai.types import Content, FunctionCall, FunctionResponse, Part
import pytest

from .faq_agent import FAQAgent


@pytest.mark.asyncio
async def test_mortgage_rates():
    """Test FAQ agent handling mortgage rate inquiry with web search capability."""
    # Define the expected conversation flow for jumbo loan rate inquiry
    conversation = [
        Content(
            role="user",
            parts=[Part(text="What is the current rate for a 30-year fixed jumbo loan?")],
        ),
        Content(
            role="model",
            parts=[
                Part(
                    text="*",  # Non-deterministic text response, allow any text
                ),
                Part(
                    function_call=FunctionCall(
                        name="web_search",
                        args=None,  # Non-deterministic args, skip validation
                    )
                ),
                Part(
                    function_response=FunctionResponse(
                        name="web_search",
                        response=None,  # Non-deterministic response, skip validation
                    )
                ),
            ],
        ),
    ]

    # Run the conversation and validate responses
    context = BankContext()
    agent = FAQAgent(context)
    await agent.test_conversation(conversation)
