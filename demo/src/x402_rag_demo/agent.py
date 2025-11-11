from __future__ import annotations

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.state import CompiledStateGraph
from x402_rag_langchain import make_x402_rag_tools
from x402_rag_sdk import ClientConfig, X402RagClient


def create_rag_agent(
    base_url: str,
    x402_keypair_hex: str,
    google_api_key: str,
    model_name: str = "gemini-2.0-flash",
) -> CompiledStateGraph:
    """
    Create a LangChain agent with X402 RAG tools and Gemini.
    """
    config = ClientConfig(
        base_url=base_url,
        x402_keypair_hex=x402_keypair_hex,
    )
    client = X402RagClient(config)
    tools = make_x402_rag_tools(client)

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=google_api_key,
        temperature=0.7,
    )

    system_prompt = """You are a helpful AI assistant with access to a RAG (Retrieval-Augmented Generation) system.

You have two tools available:
1. x402_rag_search - Search the knowledge base for relevant information
2. x402_rag_get_chunks - Retrieve specific chunks from a document

When a user asks a question:
- Use x402_rag_search to find relevant information
- If you need more context from a specific document, use x402_rag_get_chunks
- Always cite the source metadata when providing information
- Be concise but informative in your responses

If no relevant information is found, say so honestly."""

    return create_agent(llm, tools, system_prompt=system_prompt, debug=True)
