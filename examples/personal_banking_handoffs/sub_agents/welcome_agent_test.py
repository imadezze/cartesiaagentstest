"""Tests for the welcome agent."""

from config import BANK_NAME
from context import BankContext
from google.genai.types import Content, FunctionCall, Part
import pytest

from .welcome_agent import WelcomeAgent


@pytest.mark.asyncio
async def test_route_to_transaction():
    """Test that verified user requesting account balance routes directly to transaction agent."""
    # Create context with verified user
    context = BankContext()
    context.user_details.verified = True

    # Define the expected conversation flow
    conversation = [
        Content(
            role="model",
            parts=[
                Part(
                    text=f"Hello! Welcome to {BANK_NAME} customer support. I'm here to help you today. What can I assist you with?"
                )
            ],
        ),
        Content(role="user", parts=[Part(text="I'd like to see my account balance")]),
        Content(
            role="model",
            parts=[
                Part(
                    function_call=FunctionCall(
                        name="handoff_to_transaction",
                    )
                ),
            ],
        ),
    ]

    # Run the conversation and validate responses
    agent = WelcomeAgent(context)
    await agent.test_conversation(conversation)


@pytest.mark.asyncio
async def test_route_to_faq():
    """Test that asking about mortgage rates routes to FAQ agent."""
    # Define the expected conversation flow
    conversation = [
        Content(
            role="model",
            parts=[
                Part(
                    text=f"Hello! Welcome to {BANK_NAME} customer support. I'm here to help you today. What can I assist you with?"
                )
            ],
        ),
        Content(role="user", parts=[Part(text="I'd like to know more about mortgage interest rates")]),
        Content(
            role="model",
            parts=[
                Part(
                    function_call=FunctionCall(
                        name="handoff_to_faq",
                    )
                ),
            ],
        ),
    ]

    # Run the conversation and validate responses
    context = BankContext()
    agent = WelcomeAgent(context)
    await agent.test_conversation(conversation)
