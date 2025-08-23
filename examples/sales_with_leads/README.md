# Sales with Leads Extraction and Research

This template creates a potential Sales Representative agent with a few background tasks :

- The `ChatNode` is responsible for maintaining a good smooth low latency conversation with the user.
- The `LeadsExtractionNode` is responsible for identifying JSON object based on the conversation with the user. This JSON will define a `Leads` object, that contains their name, phone, email, company, etc if we manage to identify that in a conversation.
- The `ResearchNode` that is responsible for running a quick research on the company if identified by the `LeadsExtractionNode` and providing it to the `ChatNode`.

## Key Advanced Features

This example demonstrates three core capabilities on the SDK :

### 🎯 Feature 1: Custom Event Generation with LeadsExtractionNode

**What it does**: Automatically extracts contact information, company details, and sales insights from natural conversations and publishes them as structured events.

The `LeadsExtractionNode` is a specialized `ReasoningNode` that triggers on every `UserStoppedSpeaking` event to analyze the conversation and extract lead information:

**Extraction**

```python
class LeadsAnalysis(BaseModel):
    """Leads analysis results from conversation."""

    leads_info: dict
    confidence: str = "medium"
    timestamp: str

class LeadsExtractionNode(ReasoningNode):
    async def _process_context(self, context: ConversationContext) -> AsyncGenerator[LeadsAnalysis, None]:
        # Convert conversation context using same pattern as ChatNode
        messages = convert_messages_to_gemini(context.events)

        # Stream Gemini response for leads extraction
        stream = await self.client.aio.models.generate_content_stream(
            model=self.model_id,
            contents=messages,
            config=self.generation_config,
        )

        # Process and validate extracted leads information
        leads_info = LeadsInfo.model_validate(leads_data)

        # Yield structured LeadsAnalysis event
        yield LeadsAnalysis(
            leads_info=leads_info.model_dump(),
            confidence="high",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
```

**Bridge Configuration**

```python
# Leads extraction triggers on user speech completion
leads_node = LeadsExtractionNode(gemini_client=leads_client)
leads_bridge = Bridge(leads_node)
leads_bridge.on(UserTranscriptionReceived).map(leads_node.add_event)
leads_bridge.on(UserStoppedSpeaking).stream(leads_node.generate).broadcast()
```

### 🔗 Feature 2: Event Handlers for Context Integration

Extracting the leads is not usually enough, it may be helpful to append these back to the
`ChatNode` conversation context. The SDK allows converting new `Events` into conversation context.

The `EVENT_HANDLERS` example below shows how to transform custom events into formatted conversation context that the LLM can understand and reference.


```python
def leads_analysis_handler(event: LeadsAnalysis) -> types.UserContent:
    """Convert LeadsAnalysis event to Gemini UserContent format."""
    leads_json = json.dumps(event.leads_info, indent=2)
    leads_message = f"[LEADS_ANALYSIS] {leads_json} [/LEADS_ANALYSIS]"
    return types.UserContent(parts=[types.Part.from_text(text=leads_message)])

# Register handlers for automatic processing
EVENT_HANDLERS = {
    LeadsAnalysis: leads_analysis_handler,
}
```

```python
# Automatically process all events including custom LeadsAnalysis
messages = convert_messages_to_gemini(context.events, handlers=EVENT_HANDLERS)
```


```python
# ChatNode automatically receives and processes custom events
conversation_bridge.on(LeadsAnalysis).map(chat_node.add_event)
```

### 🔬 Feature 3: Concurrent Research with Background Processing

You may have operations that are even more intensive, that take much longer to perform. You can push those actions to the background, and flexibly manage context for such cases. Eg: Run a web search analysis using Google on the person and their company as you're talking to them.

The `ResearchNode` uses Gemini Live API with integrated Google Search to automatically research companies mentioned in leads, providing rich context for sales conversations:


**Google Search Integration** (`research_node.py:205-235`):
```python
async def _perform_research(self, leads_info: dict) -> tuple[dict, str]:
    """Perform Google Search research using Gemini Live API."""
    async with self.live_client.aio.live.connect(
        model=self.model_id, config=self.live_config
    ) as stream:
        # Send research prompt
        search_content = types.Content(role="user", parts=[types.Part(text=search_prompt)])
        await stream.send_client_content(turns=[search_content], turn_complete=True)

        # Collect research response and search metadata
        async for msg in stream.receive():
            if msg.text:
                research_summary += msg.text
            search_queries.update(self._parse_search_queries(msg))
            search_pages.update(self._parse_search_pages(msg))
```

**Concurrent Pipeline Configuration** (`main.py:55-57`):
```python
# Research runs in parallel, triggered by LeadsAnalysis events
research_node = ResearchNode(gemini_client=research_client)
research_bridge = Bridge(research_node)
research_bridge.on(LeadsAnalysis).map(research_node.add_event).stream(research_node.generate).broadcast()
```

## Template Information

### Prerequisites

- [Cartesia account](https://play.cartesia.ai)
- [Google Gemini API key](https://aistudio.google.com/app/apikey)

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `MODEL_ID` | Gemini model to use | gemini-2.5-flash-lite-preview-06-17 |

### Use Cases

Sales automation, lead generation, customer research, business development, automated sales conversations with real-time lead extraction and company research.

### File Overview

```
├── main.py                     # Entry point, multi-node setup
├── chat_node.py               # Main conversation node
├── leads_extraction_node.py   # Background leads extraction
├── research_node.py           # Company research with Google Search
├── config.py                  # System prompts and configurations
├── cartesia.toml             # Cartesia deployment config
└── requirements.txt          # Python dependencies
```

## Local Setup

Install the Cartesia CLI.
```zsh
curl -fsSL https://cartesia.sh | sh
cartesia auth login
cartesia auth status
```

### Run the Example

1. Set up your environment variables.
   ```zsh
   export GEMINI_API_KEY=your_api_key_here
   ```

2. Install dependencies and run.

   **pip**
   ```zsh
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   PORT=8000 python main.py
   ```

   **conda**
   ```zsh
   conda create -n sales-with-leads python=3.11 -y
   conda activate sales-with-leads
   pip install -r requirements.txt
   PORT=8000 python main.py
   ```

3. Chat locally by running in a different terminal.
   ```zsh
   cartesia chat 8000
   ```

## Remote Deployment

Read the [Cartesia docs](https://docs.cartesia.ai/line/) to learn how to deploy templates to the Cartesia Line platform.
