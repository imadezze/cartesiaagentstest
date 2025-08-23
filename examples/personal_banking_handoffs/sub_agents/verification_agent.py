"""Customer Verification Agent - Handles identity verification for banking operations.

This agent collects customer identity information (name, DOB, SSN last four)
through natural conversation and hands off to transaction agent when complete.
"""

from typing import AsyncGenerator, List, Optional, Union

from config import BANK_NAME
from context import BankContext
from google.genai import Client
from google.genai.types import (
    Content,
    FunctionCall,
    FunctionDeclaration,
    FunctionResponse,
    GenerateContentConfig,
    Part,
    Tool,
)
from loguru import logger
from mock_bank import mock_bank_api
from prompts import make_voice_system_prompt
from pydantic import BaseModel

from line.events import AgentResponse, ToolCall, ToolResult
from line.tools.system_tools import EndCallTool

from .sub_agent import SubAgent

# Verification agent LLM settings
VERIFICATION_MODEL_ID = "gemini-2.5-flash"

SOCIAL_SECURITY_NUMBER_QUESTION = "What are the last four digits of your Social Security Number?"

# Verification agent prompt
VERIFICATION_PROMPT = f"""
You are a {BANK_NAME} identity verification specialist. Your job is to collect exactly three pieces of information from the customer in sequence:

1. **Full Name** (first conversation turn)
2. **Date of Birth** (second conversation turn)
3. **Social Security Number Last Four Digits** (third conversation turn)

### ABSOLUTE RULES - NO EXCEPTIONS:
- ONLY ask for ONE piece of information per response
- NEVER call any tools until you have received ALL THREE pieces from the customer
- Follow this exact sequence: name → date of birth → Social Security Number last four digits
- After collecting all three pieces, THEN verify


### Your Conversation Pattern:
**Turn 1**: Ask for full name
**Turn 2**: Ask for date of birth do not include the format in the question
**Turn 3**: Ask for Social Security Number last four digits.
 IMPORTANT: You have a tendency to repeat yourself in on this turn. Ask the Social Security Number question exactly like: {SOCIAL_SECURITY_NUMBER_QUESTION}

If the verification fails, apologize and ask the user to try again. Afterwards, the user may provide corrected information for any of the three pieces of information. If so, try verifying again with the corrected information.
"""

# Initial message
VERIFICATION_INITIAL_MESSAGE = "I'm happy to help with your request! First, could you tell me your name?"


##################################################
####           Tool Argument Models           ####
##################################################


class VerifyUserDetailsArgs(BaseModel):
    """Arguments for user verification."""

    name: str
    date_of_birth: str
    ssn_last_four: str


##################################################
####            Verification Agent            ####
##################################################


class VerificationAgent(SubAgent):
    """Specialist agent for customer identity verification.

    This agent follows a structured verification process:
    1. Collect and store full name
    2. Collect and store date of birth
    3. Collect and store last 4 digits of SSN
    4. Handoff to transaction agent with collected details
    """

    def __init__(self, context: BankContext):
        """Initialize the verification agent.

        Args:
            context: The bank context object containing user and bank details
        """
        super().__init__(context)
        self.client = Client()
        self.system_prompt = VERIFICATION_PROMPT

        self.generation_config = GenerateContentConfig(
            system_instruction=make_voice_system_prompt(self.system_prompt),
            tool_config={"function_calling_config": {"mode": "AUTO"}},
            tools=[
                Tool(
                    function_declarations=[
                        FunctionDeclaration(
                            name="verify_user_details",
                            description="Verify customer identity using their name, date of birth, and SSN last four digits. Only call this after collecting all three pieces of information from the customer in separate conversation turns.",
                            parameters={
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "Customer's complete full name as provided by the customer (must be a non-empty string with actual name content)",
                                        "minLength": 2,
                                    },
                                    "date_of_birth": {
                                        "type": "string",
                                        "description": "Customer's date of birth in YYYY-MM-DD format converted from whatever format they provided (must be a valid date string)",
                                        "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
                                    },
                                    "ssn_last_four": {
                                        "type": "string",
                                        "description": "Exactly 4 digits representing the last four digits of the customer's Social Security Number (must be exactly 4 numeric digits)",
                                        "pattern": "^[0-9]{4}$",
                                        "minLength": 4,
                                        "maxLength": 4,
                                    },
                                },
                                "required": ["name", "date_of_birth", "ssn_last_four"],
                            },
                            response={
                                "type": "boolean",
                                "description": "Whether the user's identity has been verified",
                            },
                        ),
                    ]
                ),
                EndCallTool.to_gemini_tool(),
            ],
        )

    async def initial_message(
        self, user_message: Optional[str] = None, message_history: Optional[List[Content]] = None
    ) -> AsyncGenerator[AgentResponse, None]:
        """Return the initial verification message.

        Args:
            user_message: The latest message from the user (optional)
            message_history: Previous conversation messages in Gemini format (optional)

        Yields:
            AgentResponse: Initial verification message
        """
        yield AgentResponse(content=VERIFICATION_INITIAL_MESSAGE)

    async def _process_verification(
        self, function_calls: list[FunctionCall], message_history: list[Content]
    ) -> AsyncGenerator[Union[AgentResponse, ToolCall, ToolResult], None]:
        """Process verify_user_details tool calls and generate follow-up response.

        Args:
            function_calls: List of function calls from LLM response
            message_history: Message history for follow-up generation

        Yields:
            AgentResponse: Follow-up response based on verification result
            ToolResult: Verification tool call result
            ToolCall: Handoff to transaction agent
        """
        verify_user_details_fn = next(
            function_call for function_call in function_calls if function_call.name == "verify_user_details"
        )
        if not verify_user_details_fn:
            return

        args = VerifyUserDetailsArgs.model_validate(verify_user_details_fn.args)
        logger.info(f"🔐 Verifying user details: {args.name}, {args.date_of_birth}, {args.ssn_last_four}")

        # Call the actual verification function
        success = self.verify_user_details(args.name, args.date_of_birth, args.ssn_last_four)

        verification_tool_result = ToolResult(
            tool_name="verify_user_details",
            tool_args={
                "name": args.name,
                "date_of_birth": args.date_of_birth,
                "ssn_last_four": args.ssn_last_four,
            },
            result=success,
        )

        yield verification_tool_result

        if success:
            # Verification successful, provide success message then handoff
            yield AgentResponse(content="Perfect! You've been verified and are ready for banking services.")
            logger.info("🔐 Verification successful - customer verified")

            # Handoff to transaction agent
            yield ToolCall(tool_name="handoff_to_transaction")
        else:
            # Verification failed, generate follow-up response based on verification result
            tool_call_content = [
                Content(role="model", parts=[Part(function_call=verify_user_details_fn)]),
                Content(
                    role="model",
                    parts=[
                        Part(
                            function_response=FunctionResponse(
                                name="verify_user_details",
                                response={"output": verification_tool_result.result_str},
                            )
                        )
                    ],
                ),
            ]

            # Generate follow-up response based on verification result
            follow_up_response = await self.client.aio.models.generate_content(
                model=VERIFICATION_MODEL_ID,
                contents=message_history + tool_call_content,
                config=self.generation_config,
            )

            if follow_up_response.text:
                yield AgentResponse(content=follow_up_response.text)
                logger.info(
                    f'🔐 Verification follow-up response: "{follow_up_response.text}" ({len(follow_up_response.text)} chars)'
                )
            else:
                logger.warning("🔐 No follow-up response from verification tool call")
                yield AgentResponse(content="I'm sorry, I couldn't verify your identity. Please try again.")

    def verify_user_details(self, name: str, date_of_birth: str, ssn_last_four: str) -> bool:
        """Verify user details against bank API and update context.

        Args:
            name: Customer's full name
            date_of_birth: Date of birth in YYYY-MM-DD format
            ssn_last_four: Last four digits of SSN

        Returns:
            True if user is verified, False otherwise
        """
        # Update user details in context
        self.context.user_details.name = name
        self.context.user_details.date_of_birth = date_of_birth
        self.context.user_details.ssn_last_four = ssn_last_four

        # Verify customer identity against bank API
        is_verified = mock_bank_api.verify_customer_identity(name, date_of_birth, ssn_last_four)

        if is_verified:
            self.context.user_details.verified = True

            # Load customer's banking data into context
            customer_data = mock_bank_api.get_customer_data(name, date_of_birth, ssn_last_four)
            if customer_data:
                # Load account balances
                self.context.bank_details.account_balances = {
                    account_id: account_info["balance"]
                    for account_id, account_info in customer_data["accounts"].items()
                }

                # Load recent transactions
                self.context.bank_details.recent_transactions = customer_data["recent_transactions"]
        else:
            self.context.user_details.verification_attempts += 1

        return is_verified

    async def generate(
        self, user_message: str, message_history: list[Content]
    ) -> AsyncGenerator[Union[AgentResponse, ToolCall, ToolResult], None]:
        """Handle the customer verification process.

        Args:
            user_message: The latest user message
            message_history: Previous conversation messages, including the latest user message

        Yields:
            AgentResponse: Verification questions and responses
            ToolResult: Verification tool call result
            ToolCall: Handoff to transaction agent
        """
        logger.info(f"🔐 Verification agent processing: {user_message}")

        response = await self.client.aio.models.generate_content(
            model=VERIFICATION_MODEL_ID,
            contents=message_history,
            config=self.generation_config,
        )

        if response.text:
            yield AgentResponse(content=response.text)
            logger.info(f'🔐 Verification agent response: "{response.text}" ({len(response.text)} chars)')

        if response.function_calls:
            # Process function calls
            for function_call in response.function_calls:
                if function_call.name == EndCallTool.name():
                    logger.info("🔐 Verification agent end call requested")
                    yield ToolCall(tool_name=function_call.name, tool_args=function_call.args)
                elif function_call.name == "verify_user_details":
                    # Process verification tool call and generate follow-up
                    async for result in self._process_verification(response.function_calls, message_history):
                        yield result
