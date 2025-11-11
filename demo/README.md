# X402 RAG Demo

A demo LangChain agent that uses X402 RAG tools to answer questions by retrieving relevant documents.

## Features

- Interactive chat interface
- Support for both OpenAI (GPT-4o) and Google Gemini models
- Leverages X402 RAG search and chunk retrieval tools
- Async agent execution
- Automatic provider selection based on available API keys

## Setup

1. Install dependencies:

```bash
cd demo
poetry install
```

2. Configure environment variables in `.env`:

**For OpenAI:**

```
X402_RAG_BASE_URL=http://localhost:8000
X402_KEYPAIR_HEX=your_64_byte_solana_keypair_hex
OPENAI_API_KEY=your_openai_api_key_here
```

**For Google Gemini:**

```
X402_RAG_BASE_URL=http://localhost:8000
X402_KEYPAIR_HEX=your_64_byte_solana_keypair_hex
GOOGLE_API_KEY=your_gemini_api_key_here
```

**Note:** The `X402_KEYPAIR_HEX` should be a 64-byte (128 character) hexadecimal string representing your Solana keypair. This is used for both authentication and X402 payments.

The demo will automatically detect which LLM provider to use based on which API key is present. If both are present, OpenAI takes precedence.

## Usage

Run the interactive chat:

```bash
poetry run python -m x402_rag_demo.chat
```

## How it Works

The agent uses two main tools:

1. **search** - Searches the RAG index for relevant chunks
2. **get_chunks** - Retrieves specific chunk ranges from documents

The agent intelligently decides when to use these tools based on your questions.
