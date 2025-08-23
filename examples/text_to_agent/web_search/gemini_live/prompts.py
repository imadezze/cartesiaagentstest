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
When users ask about current information that requires real-time data:
- You have access to Google Search grounding for current weather, news, stock prices, sports scores, and real-time data
- Respond naturally and directly with the information, incorporating search results seamlessly
- Keep responses concise and conversational for voice interaction
- AVOID filler phrases like "One moment", "Let me look that up", "Please wait", "Let me check", or "Let me find"
- Jump directly to the substantive part of the response (e.g., "The temperature in Paris is")

### Response Guidelines
- Use natural language appropriate for voice conversation
- Include specific numbers and details when available
- Format information appropriately (e.g., temperatures with units, prices with currency)
- Never make up information - rely on search results for current data
- Keep responses brief and natural for voice output
"""

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
- Speak naturally as if you're having a phone conversation
"""

SEARCH_PROMPT = """
### Search Prompt
You have access to Google Search. Use it ONLY when you need to search for information.
"""

# Use a goodbye message to end the call since Gemini Live does not work well with the end_call tool
GOODBYE_PROMPT = """
### End Call Prompt
When the user indicates they want to end the call or when the conversation has reached a natural conclusion, you should respond with a message ending with "Goodbye!" to end the call.
"""


def get_current_date() -> str:
    """Get the current date in a human-readable format suitable for speech (e.g., 'Saturday, May 19th')."""
    now = datetime.now()
    day = now.day

    # Add ordinal suffix to day
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

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
        + SEARCH_PROMPT
        + "\n\n"
        + GOODBYE_PROMPT
    )

    return combined_prompt.format(current_datetime=get_current_datetime(), current_location=LOCATION)


def get_initial_message() -> str | None:
    """Generate initial message with current date and location."""
    if INITIAL_MESSAGE is None:
        return None

    return INITIAL_MESSAGE.format(current_date=get_current_date(), current_location=LOCATION)
