"""Shared prompt utilities for Personal Banking Customer Support Agent.

This file contains shared prompt components and utilities that are common
across multiple agents in the personal banking customer support system.
"""

from datetime import datetime

from config import BANK_LOCATION

##################################################
####            Shared Prompts               ####
##################################################

# Context prompt
CONTEXT_PROMPT = """
### Contextual Information
- Today's date: {current_date}
- Location: {bank_location}
"""

# Voice restrictions prompt
VOICE_RESTRICTION_PROMPT = """
### IMPORTANT: Voice/Phone Rules
Your responses will be spoken over the phone. Therefore:
- Do NOT use emojis, special characters, or formatting
- Do NOT use asterisks, newlines, bold, italics, bullet points
- Use only alphanumeric characters, spaces, and punctuation
- Spell out abbreviations, units, and numbers clearly
- Speak naturally as if having a phone conversation
- For dollar amounts, say "dollars and cents" clearly
"""

##################################################
####            Helper Functions             ####
##################################################


def get_current_date() -> str:
    """Get current date formatted for prompts."""
    return datetime.now().strftime("%Y-%m-%d")


def make_voice_system_prompt(base_system_prompt: str) -> str:
    """Create a voice-optimized system prompt by appending shared context and voice restrictions.

    Args:
        base_system_prompt: The agent-specific system prompt

    Returns:
        Complete system prompt with context and voice restrictions appended
    """
    combined_prompt = base_system_prompt + "\n\n" + CONTEXT_PROMPT + "\n" + VOICE_RESTRICTION_PROMPT

    return combined_prompt.format(
        current_date=get_current_date(),
        bank_location=BANK_LOCATION,
    )
