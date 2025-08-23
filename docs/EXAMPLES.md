# Cartesia Examples Repository

This repository contains a comprehensive collection of examples demonstrating various features and use cases of the Cartesia voice agent platform. Each example is designed to showcase specific capabilities and can serve as a starting point for building your own voice agents.

## Table of Contents

1. [Basic Voice Examples](#basic-voice-examples)
2. [Advanced Multi-Agent Systems](#advanced-multi-agent-systems)
3. [Text-to-Agent Templates](#text-to-agent-templates)

---

## Basic Voice Examples

### 1. Basic Chat (`examples/basic_chat/`)
**Type**: Single-agent voice system  
**LLM Provider**: Google Gemini  
**Complexity**: Beginner  

A simple voice agent that uses a single system prompt to handle conversations with Gemini. Demonstrates basic chat functionality with call ending detection.

**Key Features**:
- Single system prompt voice agent
- Uses Google Gemini API
- Tool-based call ending
- Configurable model and prompts

**Use Cases**: Customer service, personal assistants, educational tutoring, business receptionists

**Prerequisites**: Cartesia account, Google Gemini API key

---

### 2. Counter (`examples/counter/`)
**Type**: Simple state management demo  
**LLM Provider**: None (pure logic)  
**Complexity**: Beginner  

A voice agent that counts from 1 to a configurable maximum value and automatically ends the call when reached. Perfect for testing voice agent state management.

**Key Features**:
- Automated counting with configurable delay
- State management demonstration
- Automatic call termination
- No LLM dependencies

**Use Cases**: Testing voice agent functionality, demonstrating automated call termination, simple interactive counting games

**Environment Variables**:
- `MAX_COUNT`: Maximum number to count to (default: 100)
- `SLEEP_MS`: Delay between counts in milliseconds (default: 0)

---

### 3. Echo (`examples/echo/`)
**Type**: Simple response demo  
**LLM Provider**: None (direct echo)  
**Complexity**: Beginner  

A voice agent that echoes back what users say with an optional configurable delay. Useful for testing speech recognition and basic voice agent functionality.

**Key Features**:
- Direct speech echo functionality
- Configurable response delay
- Simple debugging tool
- No LLM processing

**Use Cases**: Testing voice agent functionality, debugging speech recognition, simple echo interactions

**Environment Variables**:
- `SLEEP_MS`: Delay before responding in milliseconds (default: 0)

---

### 4. Outbound Call Info (`examples/outbound_call_info/`)
**Type**: Outbound call configuration demo  
**LLM Provider**: Google Gemini  
**Complexity**: Intermediate  

Demonstrates how to handle outbound call requests with dynamic configuration based on the target phone number. Shows call routing, rejection, and personalized TTS settings.

**Key Features**:
- Pre-call request handling
- Dynamic TTS voice configuration
- Call rejection logic
- Phone number-based customization

**Use Cases**: Outbound calling systems, personalized customer outreach, call routing

**Prerequisites**: Cartesia account, Google Gemini API key

---

## Advanced Multi-Agent Systems

### 5. Form Filling (`examples/form-filling/`)
**Type**: Structured conversation system  
**LLM Provider**: Google Gemini  
**Complexity**: Advanced  

A sophisticated voice agent that conducts structured questionnaires using YAML configuration with conditional logic and response validation. Demonstrates complex conversation flow management.

**Key Features**:
- YAML-based form configuration
- Conditional question logic
- Multiple question types (string, number, boolean, select, date)
- Response validation
- Context clearing between questions
- Structured data collection

**Architecture Components**:
- **FormManager**: Handles form logic and validation
- **FormFillingNode**: Manages conversation flow
- **RecordAnswerTool**: Captures structured responses
- **Form Configuration**: YAML-based question definitions

**Use Cases**: Customer surveys, medical intake forms, registration processes, interview questionnaires, research data collection, onboarding workflows

**Prerequisites**: Cartesia account, Google Gemini API key

---

### 6. Personal Banking Handoffs (`examples/personal_banking_handoffs/`)
**Type**: Multi-agent customer service system  
**LLM Provider**: Google Gemini  
**Complexity**: Advanced  

A sophisticated customer support system using multiple specialized AI agents with intelligent handoffs and routing. Demonstrates enterprise-grade multi-agent architecture.

**System Architecture**:
```
👤 User → 👋 Welcome Agent → {Verification Check} → 💰 Transaction Agent
                          ↓                           ↕
                        ❓ FAQ Agent ←→ 🔐 Verification Agent
```

**Specialized Agents**:
- **Welcome Agent**: Entry point and request routing
- **Verification Agent**: Identity verification for secure access
- **Transaction Agent**: Banking operations (balances, transfers, fraud reporting)
- **FAQ Agent**: General information and web search capabilities

**Key Features**:
- Hub-and-spoke architecture with smart routing
- Identity verification system
- Secure banking operations
- Real-time web search integration
- Context-aware handoffs
- Comprehensive testing framework

**Use Cases**: Banking customer service, financial support systems, secure account management

**Prerequisites**: Cartesia account, Google Gemini API key

---

### 7. Sales with Leads (`examples/sales_with_leads/`)
**Type**: Multi-node sales system with background processing  
**LLM Provider**: Google Gemini + Gemini Live  
**Complexity**: Advanced  

A sophisticated sales representative agent with automated lead extraction and company research capabilities running in parallel background processes.

**System Architecture**:
- **ChatNode**: Low-latency conversation management
- **LeadsExtractionNode**: Automated contact information extraction
- **ResearchNode**: Background company research with Google Search

**Key Features**:
- Real-time lead extraction from conversations
- Concurrent background company research
- Custom event generation and handling
- Structured data collection
- Google Search integration via Gemini Live
- Event-driven architecture

**Advanced Capabilities**:
1. **Custom Event Generation**: Automatically extracts structured lead data
2. **Event Handlers**: Converts custom events to conversation context
3. **Concurrent Processing**: Background research while maintaining conversation

**Use Cases**: Sales automation, lead generation, customer research, business development

**Prerequisites**: Cartesia account, Google Gemini API key

---

## Text-to-Agent Templates

The text-to-agent examples are used in Cartesia's [text-to-agent](https://play.cartesia.ai/agents/new/text-to-agent) feature for creating text-based conversational agents.

### Basic Chat Templates (`examples/text_to_agent/basic_chat/`)

#### Gemini (`basic_chat/gemini/`)
**API**: Google Gemini API  
**Mode**: Text-based chat  
**Features**: Single system prompt with end_call tool

**Use Cases**: Text-based customer service, virtual assistants, educational tutoring, business chat support

#### Gemini Live (`basic_chat/gemini_live/`)
**API**: Google Gemini Live API  
**Mode**: Real-time streaming text  
**Features**: Streaming responses with real-time capabilities

**Use Cases**: Real-time text conversations, live customer service, interactive educational platforms

#### OpenAI (`basic_chat/openai/`)
**API**: OpenAI API  
**Mode**: Text-based chat  
**Features**: Single system prompt using OpenAI models

**Use Cases**: Text-based customer service, virtual assistants, educational tutoring, business chat support

#### OpenAI Realtime (`basic_chat/openai_realtime/`)
**API**: OpenAI Realtime API  
**Mode**: Real-time streaming text  
**Features**: Low-latency streaming with `gpt-4o-mini-realtime-preview-2024-12-17`

**Use Cases**: Real-time streaming conversations, low-latency chat support, live customer service

---

### Web Search Templates (`examples/text_to_agent/web_search/`)

#### Gemini Live (`web_search/gemini_live/`)
**API**: Google Gemini Live API with Google Search  
**Mode**: Single agent with web search  
**Features**: Integrated Google Search tool, real-time information retrieval

**Use Cases**: Real-time research assistants, live fact-checking, current events chatbots

#### Gemini Background (`web_search/gemini_background/`)
**API**: Google Gemini API + Gemini Live API  
**Mode**: Multi-agent system with background processing  
**Features**: Chat agent provides partial responses while background search agent completes them with web results

**Architecture**:
- **Chat Agent**: Provides immediate partial responses
- **Search Agent**: Performs background web searches
- **Coordinated Response**: Combines partial and search results

**Use Cases**: Research assistants with reduced latency, fact-checking agents, information retrieval services

---

## Getting Started

### Prerequisites
- [Cartesia account](https://play.cartesia.ai)
- API keys for your chosen LLM provider:
  - [Google Gemini API key](https://aistudio.google.com/app/apikey) (for Gemini examples)
  - [OpenAI API key](https://platform.openai.com/api-keys) (for OpenAI examples)

### Installation
1. Install the Cartesia CLI:
   ```zsh
   curl -fsSL https://cartesia.sh | sh
   cartesia auth login
   cartesia auth status
   ```

2. Navigate to any example directory and follow its specific README instructions

### Running Examples
Each example includes multiple setup options:
- **uv (recommended)**: `PORT=8000 uv run python main.py`
- **pip**: Standard virtual environment setup
- **conda**: Conda environment setup

### Local Testing
Most voice examples can be tested locally using:
```zsh
cartesia chat 8000
```

### Deployment
All examples can be deployed to the Cartesia Line platform. Read the [Cartesia docs](https://docs.cartesia.ai/line/) for deployment instructions.

---

## Example Complexity Guide

**Beginner**: Basic Chat, Counter, Echo  
**Intermediate**: Outbound Call Info, Text-to-Agent templates  
**Advanced**: Form Filling, Personal Banking Handoffs, Sales with Leads

Choose examples based on your experience level and specific use case requirements. Start with simpler examples and gradually explore more complex multi-agent systems as you become familiar with the Cartesia platform.