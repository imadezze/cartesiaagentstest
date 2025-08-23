"""Prompt constants and utility functions.

This file contains all the constant prompt strings and utility functions
that are used to generate system prompts and initial messages for the agent.
These should not be modified during normal agent configuration.
"""

from datetime import datetime

from config import AGENT_PROMPT, INITIAL_MESSAGE, LOCATION

##################################################
####           System Prompts                  ####
##################################################

# Context prompt - provides contextual information
CONTEXT_PROMPT = """
### Contextual information available to you:
- Today's date: {current_date}
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


##################################################
####           Utility Functions               ####
##################################################


def get_current_date() -> str:
    """Get the current date in a human-readable format for speech."""
    now = datetime.now()
    day = now.day

    # Add ordinal suffix to the day
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    # Format as "Saturday, May 19th"
    return now.strftime(f"%A, %B {day}{suffix}")


def get_chat_system_prompt() -> str:
    """Generate chat system prompt."""
    # Combine all prompt components for chat
    combined_prompt = AGENT_PROMPT + "\n\n" + CONTEXT_PROMPT + "\n" + VOICE_RESTRICTION_PROMPT

    return combined_prompt.format(current_date=get_current_date(), current_location=LOCATION)


def get_initial_message() -> str | None:
    """Generate initial message with current date and location."""
    if INITIAL_MESSAGE is None:
        return None

    return INITIAL_MESSAGE.format(current_date=get_current_date(), current_location=LOCATION)
