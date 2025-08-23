"""Transaction Agent for Personal Banking Customer Support.

This agent handles banking transactions and account operations for verified customers.
"""

from datetime import datetime
from typing import AsyncGenerator, List, Optional, Union

from config import BANK_NAME
from context import BankContext
from google.genai import Client
from google.genai.types import (
    Content,
    FunctionCall,
    FunctionDeclaration,
    GenerateContentConfig,
    Tool,
)
from loguru import logger
from mock_bank import mock_bank_api
from prompts import make_voice_system_prompt
from pydantic import BaseModel

from line.events import AgentResponse, ToolCall, ToolResult
from line.tools.system_tools import EndCallTool

from .sub_agent import SubAgent

# Transaction agent LLM settings
TRANSACTION_MODEL_ID = "gemini-2.5-flash"

# Transaction agent prompt
TRANSACTION_PROMPT = f"""
You are a {BANK_NAME} banking specialist for verified customers. You have access to complete customer banking information and can help with:

### Your Capabilities:
1. **Account Information**: Check balances, view account details
2. **Transaction History**: Show recent transactions, explain specific charges
3. **Fraud Reporting**: File fraud reports for suspicious activity
4. **General Banking**: Answer questions about banking products and services

### Your Tools:
- `report_fraud`: Use when customer reports suspicious activity or fraud
- `handoff_to_faq`: Use when customer asks about general {BANK_NAME} information, rates, policies, or non-transactional questions

### Customer Context Available:
- Customer identity verification status
- Account balances across all accounts
- Recent transaction history

### Your Style:
- Be helpful, professional, and security-conscious
- Use specific account information when available
- Explain banking terms clearly
- Take fraud concerns seriously and act quickly
- Suggest relevant banking products when appropriate

### When to Use report_fraud:
- Customer mentions unauthorized transactions
- Customer reports suspicious account activity
- Customer says they lost their card or it was stolen
- Customer notices unfamiliar charges

### Example Interactions:
Customer: "What's my checking account balance?"
You: "Your checking account (ending in 001) currently has a balance of $2,500.75."

Customer: "I see a charge I don't recognize"
You: "Let me help you with that. Which account is affected and can you please describe the fraudulent activity?" [Then potentially use report_fraud tool]
You: "I've reported the fraud. Your fraud report ID is FRAUD_TEST123."
"""


##################################################
####           Tool Argument Models           ####
##################################################


class ReportFraudArgs(BaseModel):
    """Arguments for fraud reporting.

    Attributes:
        fraud_description: Description of the suspected fraudulent activity
        affected_account: Account ID that is affected
    """

    fraud_description: str
    affected_account: str


##################################################
####            Transaction Agent             ####
##################################################


class TransactionAgent(SubAgent):
    """Agent for handling banking transactions and account operations.

    This agent handles:
    - Account balance inquiries
    - Transaction history
    - Money transfers
    - Account management
    - Fraud reporting
    """

    def __init__(self, context: BankContext):
        """Initialize the transaction agent.

        Args:
            context: The bank context object containing user and bank details
        """
        super().__init__(context)
        self.client = Client()
        self.system_prompt = TRANSACTION_PROMPT

        self.generation_config = GenerateContentConfig(
            system_instruction=make_voice_system_prompt(self.system_prompt),
            tool_config={"function_calling_config": {"mode": "AUTO"}},
            tools=[
                Tool(
                    function_declarations=[
                        FunctionDeclaration(
                            name="report_fraud",
                            description="Report fraudulent activity and initiate fraud response procedures. Use when customer reports suspicious activity, unauthorized transactions, or fraud concerns.",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "fraud_description": {
                                        "type": "string",
                                        "description": "Description of the suspected fraudulent activity reported by the customer",
                                    },
                                    "affected_account": {
                                        "type": "string",
                                        "description": "Account ID that is affected by the fraud",
                                    },
                                },
                                "required": ["fraud_description", "affected_account"],
                            },
                            response={
                                "type": "object",
                                "properties": {
                                    "fraud_report_id": {
                                        "type": "string",
                                        "description": "The ID of the fraud report",
                                    },
                                },
                            },
                        ),
                        FunctionDeclaration(
                            name="handoff_to_faq",
                            description=f"Route customer to FAQ specialist for general {BANK_NAME} information, rates, policies, or non-transactional questions",
                        ),
                    ]
                ),
                EndCallTool.to_gemini_tool(),
            ],
        )

        logger.info("💰 Transaction agent initialized")

    async def _process_fraud_report(
        self, function_calls: list[FunctionCall], message_history: list[Content]
    ) -> AsyncGenerator[Union[AgentResponse, ToolResult], None]:
        """Process report_fraud tool calls and generate follow-up response.

        Args:
            function_calls: List of function calls from LLM response
            message_history: Message history for follow-up generation

        Yields:
            AgentResponse: Follow-up response based on fraud report result
            ToolResult: Fraud report tool call result
        """
        report_fraud_fn = next(
            function_call for function_call in function_calls if function_call.name == "report_fraud"
        )
        if not report_fraud_fn:
            return

        args = ReportFraudArgs.model_validate(report_fraud_fn.args)
        logger.info(f"💰 Processing fraud report: {args.fraud_description}")

        # Call the actual fraud reporting function
        fraud_report_id = self.report_fraud(args.fraud_description, args.affected_account)

        fraud_tool_result = ToolResult(
            tool_name="report_fraud",
            tool_args={
                "fraud_description": args.fraud_description,
                "affected_account": args.affected_account,
            },
            result={"fraud_report_id": fraud_report_id},
        )

        yield fraud_tool_result

        yield AgentResponse(content=f"Your fraud report has been filed with ID {fraud_report_id}.")

    async def initial_message(
        self, user_message: Optional[str] = None, message_history: Optional[List[Content]] = None
    ) -> AsyncGenerator[AgentResponse, None]:
        """Return initial message for transaction agent.

        Args:
            user_message: The latest message from the user (optional)
            message_history: Previous conversation messages in Gemini format (optional)

        Yields:
            AgentResponse: Initial messages or responses from generate
        """
        if not self.context.user_details.verified:
            yield AgentResponse(
                content="I'm sorry, but you need to be verified before you can use transaction services."
            )
        else:
            yield AgentResponse(content="How can I help you with your account today?")

    async def generate(
        self, user_message: str, message_history: list[Content]
    ) -> AsyncGenerator[Union[AgentResponse, ToolCall, ToolResult], None]:
        """Handle banking transaction requests.

        Args:
            user_message: The latest user message
            message_history: Previous conversation messages

        Yields:
            AgentResponse: Transaction responses
            ToolCall: Handoff to FAQ agent
            ToolResult: Fraud report tool call result
        """
        logger.info(f"💰 Transaction agent processing: {user_message}")

        if not self.context.user_details.verified:
            yield AgentResponse(
                content="I'm sorry, but you need to be verified before you can use this service."
            )
            return
        else:
            self.load_bank_details()

        # Prepend banking context to message history
        bank_context = self.context.dump_context()
        context_message = Content(
            role="user",
            parts=[
                {
                    "text": f"[Banking Context for Customer Service]\n{bank_context}\n\n[Continue with customer conversation below]"
                }
            ],
        )

        # Generate response using Gemini
        response = await self.client.aio.models.generate_content(
            model=TRANSACTION_MODEL_ID,
            contents=[context_message] + message_history,
            config=self.generation_config,
        )

        # Yield text response if present
        if response.text:
            yield AgentResponse(content=response.text)
            logger.info(f'💰 Transaction agent response: "{response.text}" ({len(response.text)} chars)')

        # Process function calls
        if response.function_calls:
            for function_call in response.function_calls:
                logger.info(f"💰 Transaction agent tool call: {function_call.name}")

                if function_call.name == EndCallTool.name():
                    logger.info("💰 Transaction agent end call requested")
                    yield ToolCall(tool_name=function_call.name, tool_args=function_call.args)
                elif function_call.name == "report_fraud":
                    # Process fraud report and generate follow-up
                    async for result in self._process_fraud_report(response.function_calls, message_history):
                        yield result
                elif function_call.name == "handoff_to_faq":
                    # Handoff to FAQ agent
                    yield ToolCall(tool_name="handoff_to_faq")

    def report_fraud(self, fraud_description: str, affected_account: str) -> str:
        """Report fraudulent activity and initiate fraud response procedures.

        This method logs fraud reports and prepares for escalation to human agents.
        Used when customers report suspicious activity.

        Args:
            fraud_description: Description of the suspected fraudulent activity
            affected_account: Account ID that is affected

        Returns:
            Fraud report ID for tracking purposes
        """
        # Generate fraud report ID (using fixed value for testing)
        fraud_report_id = "FRAUD_TEST123"

        # Log the fraud report
        user_details = self.context.user_details
        log_entry = {
            "fraud_report_id": fraud_report_id,
            "timestamp": datetime.now().isoformat(),
            "customer_name": user_details.name,
            "customer_verified": user_details.verified,
            "fraud_description": fraud_description,
            "affected_account": affected_account,
            "session_id": self.context.session_id,
        }

        logger.info(f"FRAUD REPORT FILED: {log_entry}")

        # TODO: Transfer to live human agent for immediate fraud response
        # This should:
        # 1. Escalate the call to the fraud department
        # 2. Immediately freeze affected accounts if specified
        # 3. Initiate fraud investigation procedures
        # 4. Connect customer with specialized fraud agent
        # 5. Send fraud alert notifications to customer

        return fraud_report_id

    def load_bank_details(self) -> bool:
        """Load comprehensive banking data into context for verified users.

        This function loads complete banking information (account balances, transactions,
        account types, credit products, and preferences) into the context
        for users who have been successfully verified.

        Returns:
            True if bank details were loaded successfully, False if user not verified
        """
        user_details = self.context.user_details

        # Only load bank details for verified users
        if not user_details.verified:
            return False

        # Check if bank details are already loaded
        if self.context.bank_details.account_balances:
            return True

        # Load bank details using verified user information
        customer_data = mock_bank_api.get_customer_data(
            user_details.name, user_details.date_of_birth, user_details.ssn_last_four
        )

        if customer_data:
            # Load account balances
            self.context.bank_details.account_balances = {
                account_id: account_info["balance"]
                for account_id, account_info in customer_data["accounts"].items()
            }

            # Load recent transactions
            self.context.bank_details.recent_transactions = customer_data["recent_transactions"]

            return True

        return False
