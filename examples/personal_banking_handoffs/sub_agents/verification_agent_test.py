"""Tests for the verification agent."""

from context import BankContext
from google.genai.types import Content, FunctionCall, FunctionResponse, Part
import pytest

from .verification_agent import VerificationAgent


@pytest.mark.asyncio
async def test_successful_verification():
    """Test the complete verification flow using conversation definition."""
    # Define the expected conversation flow
    conversation = [
        Content(
            role="model",
            parts=[Part(text="I'm happy to help with your request! First, could you tell me your name?")],
        ),
        Content(role="user", parts=[Part(text="John Smith")]),
        Content(
            role="model",
            parts=[Part(text="Now, could you tell me your date of birth?")],
        ),
        Content(role="user", parts=[Part(text="March 15, 1985")]),
        Content(
            role="model",
            parts=[
                Part(
                    text="Finally, could you please provide the last four digits of your Social Security Number?"
                )
            ],
        ),
        Content(role="user", parts=[Part(text="one two three four")]),
        Content(
            role="model",
            parts=[
                Part(text="Perfect! You've been verified and are ready for banking services"),
                Part(
                    function_call=FunctionCall(
                        name="verify_user_details",
                        args={
                            "name": "John Smith",
                            "date_of_birth": "1985-03-15",
                            "ssn_last_four": "1234",
                        },
                    )
                ),
                Part(
                    function_response=FunctionResponse(name="verify_user_details", response={"output": True})
                ),
                Part(
                    function_call=FunctionCall(
                        name="handoff_to_transaction",
                        args={},
                    )
                ),
            ],
        ),
    ]

    # Run the conversation and validate responses
    context = BankContext()
    agent = VerificationAgent(context)
    await agent.test_conversation(conversation)

    # Verify final context state was updated by the verification process
    assert context.user_details.name == "John Smith"
    assert context.user_details.date_of_birth == "1985-03-15"
    assert context.user_details.ssn_last_four == "1234"
    assert context.user_details.verified


@pytest.mark.asyncio
async def test_failed_verification_recovery():
    """Test an initial verification failure, then a successful verification after corrected information is provided."""
    # Define the expected conversation flow
    conversation = [
        Content(
            role="model",
            parts=[Part(text="I'm happy to help with your request! First, could you tell me your name?")],
        ),
        Content(role="user", parts=[Part(text="Fake Name")]),
        Content(
            role="model",
            parts=[Part(text="Now, could you tell me your date of birth?")],
        ),
        Content(role="user", parts=[Part(text="March 15, 1985")]),
        Content(
            role="model",
            parts=[
                Part(
                    text="Finally, could you please provide the last four digits of your Social Security Number?"
                )
            ],
        ),
        Content(role="user", parts=[Part(text="one two three four")]),
        Content(
            role="model",
            parts=[
                Part(
                    text="I'm sorry, but I wasn't able to verify your identity with the information provided. Please try again."
                ),
                Part(
                    function_call=FunctionCall(
                        name="verify_user_details",
                        args={
                            "name": "Fake Name",
                            "date_of_birth": "1985-03-15",
                            "ssn_last_four": "1234",
                        },
                    )
                ),
                Part(
                    function_response=FunctionResponse(name="verify_user_details", response={"output": False})
                ),
            ],
        ),
        Content(role="user", parts=[Part(text="Actually, my name is John Smith")]),
        Content(
            role="model",
            parts=[
                Part(text="Perfect! You've been verified and are ready for banking services"),
                Part(
                    function_call=FunctionCall(
                        name="verify_user_details",
                        args={
                            "name": "John Smith",
                            "date_of_birth": "1985-03-15",
                            "ssn_last_four": "1234",
                        },
                    )
                ),
                Part(
                    function_response=FunctionResponse(name="verify_user_details", response={"output": True})
                ),
                Part(function_call=FunctionCall(name="handoff_to_transaction")),
            ],
        ),
    ]

    # Run the conversation and validate responses
    context = BankContext()
    agent = VerificationAgent(context)
    await agent.test_conversation(conversation)

    # Verify final context state was updated by the verification process
    assert context.user_details.name == "John Smith"
    assert context.user_details.date_of_birth == "1985-03-15"
    assert context.user_details.ssn_last_four == "1234"
    assert context.user_details.verified
