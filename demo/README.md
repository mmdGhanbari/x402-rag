# X402 RAG Demo

A demo LangChain agent that uses X402 RAG tools to answer questions by retrieving relevant documents.

## Features

- Interactive chat interface
- Uses Google Gemini Flash 2.5 model
- Leverages X402 RAG search and chunk retrieval tools
- Async agent execution

## Setup

1. Install dependencies:

```bash
cd demo
poetry install
```

2. Configure environment variables in `.env`:

```
X402_RAG_BASE_URL=http://localhost:8000
X402_KEYPAIR_HEX=your_64_byte_solana_keypair_hex
GOOGLE_API_KEY=your_gemini_api_key_here
```

**Note:** The `X402_KEYPAIR_HEX` should be a 64-byte (128 character) hexadecimal string representing your Solana keypair. This is used for both authentication and X402 payments.

## Usage

Run the interactive chat:

```bash
poetry run x402-demo
```

Or run directly with Python:

```bash
poetry run python -m x402_rag_demo.chat
```

## How it Works

The agent uses two main tools:

1. **x402_rag_search** - Searches the RAG index for relevant chunks
2. **x402_rag_get_chunks** - Retrieves specific chunk ranges from documents

The agent intelligently decides when to use these tools based on your questions.
