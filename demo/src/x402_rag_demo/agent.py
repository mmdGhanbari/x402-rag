from __future__ import annotations

import os
from typing import Literal

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from x402_rag_langchain import make_x402_rag_tools
from x402_rag_sdk import ClientConfig, X402RagClient


def create_rag_agent(
    base_url: str,
    x402_keypair_hex: str,
    api_key: str,
    provider: Literal["openai", "google"] = "google",
    model_name: str | None = None,
    temperature: float = 0.7,
) -> CompiledStateGraph:
    """
    Create a LangChain agent with X402 RAG tools and your choice of LLM provider.

    Args:
        base_url: X402 RAG server URL
        x402_keypair_hex: Solana keypair for x402 payments
        api_key: API key for the LLM provider (OpenAI or Google)
        provider: LLM provider - "openai" or "google"
        model_name: Model name (defaults: gpt-4o-mini for openai, gemini-2.0-flash for google)
        temperature: LLM temperature (0.0 to 1.0)

    Returns:
        Compiled LangGraph agent ready to use
    """
    config = ClientConfig(
        base_url=base_url,
        x402_keypair_hex=x402_keypair_hex,
    )
    client = X402RagClient(config)
    tools = make_x402_rag_tools(client)

    # Create LLM based on provider
    llm: BaseChatModel
    if provider == "openai":
        llm = ChatOpenAI(
            model=model_name or "gpt-4o-mini",
            api_key=api_key,
            temperature=temperature,
            base_url=os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        )
    elif provider == "google":
        llm = ChatGoogleGenerativeAI(
            model=model_name or "gemini-2.0-flash",
            google_api_key=api_key,
            temperature=temperature,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'google'")

    system_prompt = """You are a helpful AI assistant with access to a RAG (Retrieval-Augmented Generation) system.

You have two tools available:
1. search - Search the knowledge base for relevant information
2. get_chunks - Retrieve specific chunks from a document

When a user asks a question:
- Use search to find relevant information
- If you need more context from a specific document, use get_chunks
- Always cite the source metadata when providing information
- Be concise but informative in your responses

If payment information is provided in the tool calling response, inform it to the user.

If no relevant information is found, say so honestly."""

    return create_agent(llm, tools, system_prompt=system_prompt)
