# Text to Agent Templates

These templates are used in the [text-to-agent](https://play.cartesia.ai/agents/new/text-to-agent) feature.

## Template Types

### Basic Chat

These templates use a single system prompt with just the `end_call` tool.

| Template Name | Description |
|---------------|-------------|
| `gemini` | Single chat agent using the standard Gemini API |
| `gemini_live` | Single chat agent using the Gemini Live API |
| `openai` | Single chat agent using the OpenAI responses API |
| `openai_realtime` | Single chat agent using the OpenAI Realtime API |

### Web Search

These templates use a single system prompt with an additional tool to perform web search. They typically have a higher response latency compared to **Basic Chat** templates.
| Template Name | Description |
|---------------|-------------|
| `gemini_live` | Single chat agent using the Gemini Live API with the `google_search` tool enabled |
| `gemini_background` | Multi-agent system with a Gemini API based chat agent and Gemini Live API based search agent with the `google_search` tool enabled. To reduce latency, the chat agent sends a partial response to the user while kicking off the search agent in the background. The search agent completes the response leveraging the search results as they become available. |
