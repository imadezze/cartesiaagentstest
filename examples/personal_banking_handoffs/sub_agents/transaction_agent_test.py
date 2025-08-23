"""Tests for the transaction agent."""

from context import BankContext
from google.genai.types import Content, FunctionCall, FunctionResponse, Part
import pytest

from .transaction_agent import TransactionAgent


@pytest.fixture
def setup_verified_user():
    """Set up a verified user with loaded bank details for testing."""
    # Create context
    context = BankContext()

    # Set up verified user (John Smith from mock data)
    context.user_details.name = "John Smith"
    context.user_details.date_of_birth = "1985-03-15"
    context.user_details.ssn_last_four = "1234"
    context.user_details.verified = True

    # Load bank details matching mock data
    context.bank_details.account_balances = {
        "checking_001": 2500.75,
        "savings_002": 15000.00,
        "credit_card_003": -1250.50,
    }
    context.bank_details.recent_transactions = [
        {
            "date": "2024-01-15",
            "amount": -45.67,
            "description": "Grocery Store",
            "account": "checking_001",
        },
        {
            "date": "2024-01-14",
            "amount": -120.00,
            "description": "Gas Station",
            "account": "checking_001",
        },
        {
            "date": "2024-01-13",
            "amount": 2000.00,
            "description": "Direct Deposit",
            "account": "checking_001",
        },
        {
            "date": "2024-01-12",
            "amount": 500.00,
            "description": "Transfer to Savings",
            "account": "savings_002",
        },
        {
            "date": "2024-01-10",
            "amount": -89.95,
            "description": "Online Purchase",
            "account": "credit_card_003",
        },
    ]

    return context


@pytest.mark.asyncio
async def test_check_account_balance(setup_verified_user):
    """Test that the agent can provide account balance information."""
    # Simple conversation focusing on balance response
    conversation = [
        Content(role="user", parts=[Part(text="What's my checking account balance?")]),
        Content(
            role="model",
            parts=[Part(text="Your checking account balance is $2,500.75.")],
        ),
    ]

    # Run the conversation and validate responses
    agent = TransactionAgent(setup_verified_user)
    await agent.test_conversation(conversation)


@pytest.mark.asyncio
async def test_report_fraud(setup_verified_user):
    """Test that the agent can handle fraud reporting with actual tool call."""
    # Multi-turn conversation that leads to actual fraud reporting tool call
    conversation = [
        Content(role="user", parts=[Part(text="I need to report fraud on my account")]),
        Content(
            role="model",
            parts=[
                Part(
                    text="I'm sorry to hear that, John. I can help you with this. Which account is affected and can you please describe the fraudulent activity?"
                )
            ],
        ),
        Content(
            role="user",
            parts=[
                Part(
                    text="There is a $500 charge I didn't make at some online store called TechMart on my credit card"
                )
            ],
        ),
        Content(
            role="model",
            parts=[
                Part(
                    function_call=FunctionCall(
                        name="report_fraud",
                        args={
                            "fraud_description": "Unauthorized charge of $500 at TechMart on credit card",
                            "affected_account": "credit_card_003",
                        },
                    )
                ),
                Part(
                    function_response=FunctionResponse(
                        name="report_fraud",
                        response={"output": {"fraud_report_id": "FRAUD_TEST123"}},
                    )
                ),
                Part(text="Your fraud report has been filed with ID FRAUD_TEST123."),
            ],
        ),
    ]

    # Run the conversation and validate responses
    agent = TransactionAgent(setup_verified_user)
    await agent.test_conversation(conversation)
