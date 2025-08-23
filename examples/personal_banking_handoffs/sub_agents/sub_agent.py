"""Abstract base class for Personal Banking Customer Support Sub-Agents.

This module provides the base class that all specialized agents inherit from,
ensuring a consistent interface and initialization pattern.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Union

from context import BankContext
from google.genai import Client
from google.genai.types import Content, GenerateContentConfig, Part

from line.events import AgentResponse, ToolCall, ToolResult


class SubAgent(ABC):
    """Abstract base class for sub-agents.

    All sub-agents must inherit from this class and implement the generate method.
    The base class handles common initialization patterns while allowing each
    agent to customize their specific behavior.
    """

    @abstractmethod
    def __init__(self, context: BankContext):
        """Initialize the sub-agent.

        Args:
            context: The bank context object containing user and bank details

        Subclasses should call super().__init__(context) and then perform their
        specific initialization (setting up clients, configs, etc.) in
        their constructor rather than having a separate init() method.
        """
        self.context = context

    async def initial_message(
        self, user_message: Optional[str] = None, message_history: Optional[List[Content]] = None
    ) -> AsyncGenerator[Union[AgentResponse, ToolCall], None]:
        """Return the initial message for this agent.

        This method can be overridden by subclasses to provide dynamic initial messages
        based on the user message and conversation history.

        Args:
            user_message: The latest message from the user (optional)
            message_history: Previous conversation messages in Gemini format (optional)

        Yields:
            AgentResponse: Initial messages
            ToolCall: Initial tool calls
        """
        return
        yield  # Make this a generator (unreachable but satisfies type checker)

    @abstractmethod
    async def generate(
        self, user_message: str, message_history: list[Content]
    ) -> AsyncGenerator[Union[AgentResponse, ToolCall], None]:
        """Generate responses for the given user message and conversation history.

        This is the main method that each sub-agent must implement. It should
        process the user's message in the context of the conversation history
        and yield appropriate responses and tool calls.

        Args:
            user_message: The latest message from the user
            message_history: Previous conversation messages in Gemini format

        Yields:
            AgentResponse: Text responses to be spoken to the user
            ToolCall: Tool calls for actions or state transitions
        """
        pass

    def _validate_response(
        self, response: List[Union[AgentResponse, ToolCall, ToolResult]], expected_response: Content
    ) -> None:
        """Validate agent response against expected response.

        Args:
            response: List of AgentResponse, ToolCall, and ToolResult objects from agent
            expected_response: Expected Content with text and optional function response

        Raises:
            AssertionError: If response doesn't match expected
        """
        # Prepare agent data
        messages = [r.content for r in response if isinstance(r, AgentResponse)]
        agent_message = " ".join(messages)

        # Create dict mapping tool name to tool call or result
        tools: Dict[str, Union[ToolCall, ToolResult]] = {}
        for item in response:
            if isinstance(item, ToolCall) or isinstance(item, ToolResult):
                tools[item.tool_name] = item

        # Validate each expected part
        for expected_part in expected_response.parts:
            if expected_part.text:
                # Check text similarity
                error = is_similar_str(agent_message, expected_part.text)
                if error is not None:
                    raise AssertionError(
                        f"Agent response doesn't match expected meaning.\nAgent response: {agent_message}\nExpected: {expected_part.text}\nReason: {error}"
                    )

            if expected_part.function_call:
                tool_name = expected_part.function_call.name
                # Check for either ToolCall or ToolResult
                if tool_name not in tools:
                    raise AssertionError(f"Expected tool call '{tool_name}' not found in response")

                # Get the tool call or result
                tool_item = tools.get(tool_name)
                expected_args = expected_part.function_call.args

                # Compare tool args with expected
                if expected_args is not None:
                    actual_args = tool_item.tool_args
                    error = is_similar_dict(actual_args, expected_args)
                    if error is not None:
                        raise AssertionError(
                            f"Tool call args mismatch for '{tool_name}': {error}\nActual: {actual_args}\nExpected: {expected_args}"
                        )

            if expected_part.function_response:
                tool_name = expected_part.function_response.name
                # Check for ToolResult specifically
                if tool_name not in tools:
                    raise AssertionError(f"Expected tool call '{tool_name}' not found in response")

                if not isinstance(tool_item, ToolResult):
                    raise AssertionError(f"Expected tool result for '{tool_name}' not found in response")

                # Compare result with expected
                if expected_part.function_response.response is not None:
                    expected_result = expected_part.function_response.response["output"]
                    if tool_item.result != expected_result:
                        raise AssertionError(
                            f"Tool result mismatch for '{tool_name}'\nActual: {tool_item.result}\nExpected: {expected_result}"
                        )

        # Check for unexpected messages
        expected_text = any(part.text for part in expected_response.parts)
        if agent_message.strip() and not expected_text:
            raise AssertionError(
                f"Unexpected message content found: '{agent_message.strip()}' (expected no text)"
            )

        # Check for unexpected tool calls
        expected_tool_names = set()
        for part in expected_response.parts:
            if part.function_call:
                expected_tool_names.add(part.function_call.name)
            if part.function_response:
                expected_tool_names.add(part.function_response.name)

        unexpected_tools = set(tools.keys()) - expected_tool_names
        if unexpected_tools:
            raise AssertionError(f"Unexpected tool calls found: {list(unexpected_tools)}")

    async def test_conversation(self, conversation: list[Content]) -> None:
        """Test the agent with a predefined conversation flow.

        Args:
            conversation: List of Content objects representing the full conversation,
                         alternating between user and model roles
        """
        message_history = []
        ii = 0

        # Handle initial model message if present
        if conversation[0].role == "model":
            message_history.append(conversation[0])
            ii = 1

        while ii < len(conversation):
            user_turn = conversation[ii]

            # Should be processing a user message at this point
            assert user_turn.role == "user", f"Expected user message at index {ii}, got {user_turn.role}"

            # Add user message to history
            message_history.append(user_turn)
            ii += 1

            # Extract user message text
            user_message = user_turn.parts[0].text

            # Generate agent response
            results = []
            async for result in self.generate(user_message, message_history):
                results.append(result)

            # Next message should be the expected model response
            assert ii < len(conversation), (
                f"Expected model response after user message {user_message} at index {ii - 1}"
            )
            expected_turn = conversation[ii]
            assert expected_turn.role == "model", (
                f"Expected model message after user message {user_message} at index {ii}, got {expected_turn.role}"
            )

            # Validate response using helper method
            try:
                self._validate_response(results, expected_turn)
            except AssertionError as e:
                raise AssertionError(f"Turn {ii}: {e}") from e

            # Add the agent response to history for next turn
            messages = [r.content for r in results if isinstance(r, AgentResponse)]
            agent_message = " ".join(messages)
            message_history.append(Content(role="model", parts=[Part(text=agent_message)]))
            ii += 1


def is_similar_str(a: str, b: str) -> Optional[str]:
    """Check if two strings have the same meaning using Gemini.

    Args:
        a: First string to compare
        b: Second string to compare

    Returns:
        None if strings are similar, error message string if not
    """
    # * means any string is allowed
    if a == "*" or b == "*":
        return None

    # First check if strings are equal after basic normalization
    if a.lower().strip() == b.lower().strip():
        return None

    client = Client()

    prompt = f"""
    Compare these two strings and determine if they have the same or very similar meaning:

    String A: "{a}"
    String B: "{b}"

    Respond with "YES" if they have the same meaning, or "NO: [reason]" if they don't.
    Consider paraphrasing, synonyms, and different ways of expressing the same concept.
    Ignore filler prefixes like "Now", "Thank you", "Finally", etc.

    Examples:
    - "What's your name?" vs "Can you tell me your name?" → YES
    - "What's your name?" vs "What's your age?" → NO: Different information being requested
    - "You are verified" vs "Your identity is confirmed" → YES
    - "Now, what's your Name?" vs "Thank you, what's your name?" → YES
    - "Hello" vs "Goodbye" → NO: Opposite greetings with different meanings
    """

    config = GenerateContentConfig(
        temperature=0.1,  # Low temperature for consistent results
    )

    response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt, config=config)

    response_text = response.text.strip()

    if response_text.upper().startswith("YES"):
        return None  # Strings are similar
    elif response_text.upper().startswith("NO"):
        # Extract and return reason
        reason = response_text[3:].strip().lstrip(":").strip()
        return reason
    else:
        # Fallback in case of unexpected response format
        return f'Unexpected response format from similarity check: {response_text}\nString A: "{a}"\nString B: "{b}"'


def is_similar_dict(actual: Dict, expected: Dict) -> Optional[str]:
    """Recursively check if two dictionaries are similar.

    Uses string similarity checking for string values and recursive comparison for nested dicts.

    Args:
        actual: The actual dictionary
        expected: The expected dictionary

    Returns:
        None if dictionaries are similar, error message string if not
    """
    # Check if keys match
    actual_keys = set(actual.keys())
    expected_keys = set(expected.keys())

    if actual_keys != expected_keys:
        missing_keys = expected_keys - actual_keys
        extra_keys = actual_keys - expected_keys
        error_parts = []
        if missing_keys:
            error_parts.append(f"missing keys: {list(missing_keys)}")
        if extra_keys:
            error_parts.append(f"extra keys: {list(extra_keys)}")
        return f"Key mismatch - {', '.join(error_parts)}"

    # Check each key-value pair
    for key in expected_keys:
        actual_value = actual[key]
        expected_value = expected[key]

        # Handle None values
        if expected_value is None and actual_value is None:
            continue
        if expected_value is None or actual_value is None:
            return f"Value mismatch for key '{key}': expected {expected_value}, got {actual_value}"

        # Handle string values with similarity checking
        if isinstance(expected_value, str) and isinstance(actual_value, str):
            error = is_similar_str(actual_value, expected_value)
            if error is not None:
                return f"String value mismatch for key '{key}': {error}"

        # Handle nested dictionaries
        elif isinstance(expected_value, dict) and isinstance(actual_value, dict):
            error = is_similar_dict(actual_value, expected_value)
            if error is not None:
                return f"Nested dict mismatch for key '{key}': {error}"

        # Handle other types with exact comparison
        else:
            if actual_value != expected_value:
                return f"Value mismatch for key '{key}': expected {expected_value}, got {actual_value}"

    return None
