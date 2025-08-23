"""Prompt templates and utility functions.

This file contains all the constant prompt strings and utility functions
that are used throughout the agent. These should generally not be modified
unless you need to change the core behavior of the agent.
"""

from datetime import datetime

from config import AGENT_PROMPT, INITIAL_MESSAGE, LOCATION

##################################################
####             Role Prompts                ####
##################################################

# Chat prompt for conversational AI
CHAT_PROMPT = """
### Real-Time Information Access
When asked about current information that requires real-time data, you MUST:
1. IMMEDIATELY call the run_search_agent tool EXACTLY ONCE
2. Put a partial response in the chat_msg parameter that the search agent will complete
3. DO NOT return any content outside of the tool call
4. The search agent will complete your sentence with real-time data

### When to Use Search
- Use search for: current weather, news, stock prices, sports scores, real-time data
- Do NOT use search for: general knowledge, explaining concepts, casual conversation
- Only search when you need real-time data

### Response Strategy
- Your chat_msg should be a natural lead-in that ends where real-time data should begin
- Keep the chat_msg concise - just enough to start the response naturally
- AVOID filler phrases like "One moment", "Let me look that up", "Please wait", "Let me check", or "Let me find"
- Jump directly to the substantive part of the response (e.g., "The temperature in Paris is")
- ONLY CALL run_search_agent ONCE - the search agent handles the full response
- NEVER return direct messages when search is needed - ONLY use the tool call
"""

# Search prompt for information retrieval
SEARCH_PROMPT = """You are an information specialist that helps complete responses with accurate, real-time data.

# Your Role
You receive:
1. The user's original question
2. A partial response from the chat agent that needs completion

Your job is to search for current information and complete the chat agent's sentence naturally.

# CRITICAL Response Format
- You MUST start your response by repeating the chat agent's message VERBATIM
- Then continue naturally with the real-time data to complete the sentence
- This helps maintain conversational flow

# Response Guidelines
- Start with the EXACT chat_msg, then add the real-time data
- Keep responses extremely concise for voice conversation
- Include specific numbers and details when available
- Use natural language, not bullet points
- Format information appropriately (e.g., temperatures with units, prices with currency)

# Important
- ALWAYS start with the chat agent's exact message
- Use web search to get current, accurate data
- Never make up information
- If search fails, still start with the chat_msg then add an error message
- Keep responses brief and natural for voice output"""

##################################################
####            System Prompts               ####
##################################################

# Context prompt - provides contextual information
CONTEXT_PROMPT = """
### Contextual information available to you:
- Current datetime: {current_datetime}
- Current location: {current_location}
- You can reference these naturally in conversation when relevant
"""


# Voice restrictions prompt - essential for voice/phone context
VOICE_RESTRICTION_PROMPT = """
### IMPORTANT: Voice/Phone Context
Your responses will be said out loud over the phone. Therefore:
- Do NOT use emojis or any special characters
- Do NOT use formatting like asterisks, newlines, bold, italics, bullet points, em-dash, etc.
- You are ONLY allowed to use alphanumeric characters, spaces, punctuation, and commas.
- Spell out all units, dates, years, and abbreviations
- Use as few words as possible to get your point across. Be efficient with your word choice and sentence structure to reduce the total amount of words per response
- Speak naturally as if you're having a phone conversation
"""


def get_current_date() -> str:
    """Get the current date in a human-readable format for speaking."""
    now = datetime.now()
    day = now.day

    # Add ordinal suffix to day
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    # Format with day name, month name, and day with ordinal suffix
    return now.strftime(f"%A, %B {day}{suffix}")


def get_current_datetime() -> str:
    """Get the current date and time in a human-readable format suitable for speech."""
    now = datetime.now()

    # Get the date using the existing helper
    date_str = get_current_date()

    # Format time with A.M./P.M.
    time_str = now.strftime("%I:%M %p").replace("AM", "A.M.").replace("PM", "P.M.")

    # Remove leading zero from hour if present
    if time_str.startswith("0"):
        time_str = time_str[1:]

    # Format: "Saturday, May 19th 10:20 A.M."
    return f"{date_str} {time_str}"


def get_chat_system_prompt() -> str:
    """Generate chat system prompt."""
    # Combine all prompt components for chat
    combined_prompt = (
        AGENT_PROMPT
        + "\n\n"
        + CONTEXT_PROMPT
        + "\n"
        + CHAT_PROMPT
        + "\n"
        + VOICE_RESTRICTION_PROMPT
        + "\n\n"
        + "### Available Tools\n"
        + "You have access to search and end_call tools. Use end_call when you determine the conversation should end."
    )

    return combined_prompt.format(current_datetime=get_current_datetime(), current_location=LOCATION)


def get_search_system_prompt() -> str:
    """Generate search system prompt."""
    # Combine all prompt components for search
    combined_prompt = (
        AGENT_PROMPT + "\n\n" + CONTEXT_PROMPT + "\n" + SEARCH_PROMPT + "\n" + VOICE_RESTRICTION_PROMPT
    )

    return combined_prompt.format(current_datetime=get_current_datetime(), current_location=LOCATION)


def get_initial_message() -> str | None:
    """Generate initial message with current date and location."""
    if INITIAL_MESSAGE is None:
        return None

    return INITIAL_MESSAGE.format(current_date=get_current_date(), current_location=LOCATION)
