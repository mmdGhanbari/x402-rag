"""Interactive chat interface for the X402 RAG agent."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

from .agent import create_rag_agent


def load_env() -> dict[str, str]:
    """Load environment variables from .env file."""
    demo_dir = Path(__file__).parent.parent.parent
    env_file = demo_dir / ".env"

    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()

    base_url = os.getenv("X402_RAG_BASE_URL") or "http://localhost:8000"
    x402_keypair_hex = os.getenv("X402_KEYPAIR_HEX")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not x402_keypair_hex:
        print("Error: Missing required environment variables.", file=sys.stderr)
        print("Please set: X402_KEYPAIR_HEX", file=sys.stderr)
        sys.exit(1)

    # Determine provider based on available API keys
    if openai_api_key:
        provider = "openai"
        api_key = openai_api_key
        model_display = "GPT-4o"
        model_name = "gpt-4o-mini"
    elif google_api_key:
        provider = "google"
        api_key = google_api_key
        model_display = "Gemini Flash 2.5"
        model_name = "gemini-2.5-flash"
    else:
        print("Error: No LLM API key found.", file=sys.stderr)
        print("Please set either OPENAI_API_KEY or GOOGLE_API_KEY", file=sys.stderr)
        sys.exit(1)

    return {
        "base_url": base_url,
        "x402_keypair_hex": x402_keypair_hex,
        "api_key": api_key,
        "provider": provider,
        "model_display": model_display,
        "model_name": model_name,
    }


async def chat_loop() -> None:
    """Run the interactive chat loop."""
    env = load_env()

    print("=" * 60)
    print("X402 RAG Demo Agent")
    print(f"Powered by {env['model_display']} and X402 RAG")
    print("=" * 60)
    print("Type your questions and press Enter.")
    print("Type 'exit' or 'quit' to end the session.")
    print("=" * 60)
    print()

    agent = create_rag_agent(
        base_url=env["base_url"],
        x402_keypair_hex=env["x402_keypair_hex"],
        api_key=env["api_key"],
        provider=env["provider"],
        model_name=env["model_name"],
    )

    chat_history: list[HumanMessage | AIMessage] = []

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("\nGoodbye!")
                break

            print()

            chat_history.append(HumanMessage(content=user_input))

            result = await agent.ainvoke({"messages": chat_history})

            response = result["messages"][-1].content

            print(f"\nAssistant: {response}\n")
            print("-" * 60)
            print()

            chat_history = result["messages"]

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n", file=sys.stderr)


def main() -> None:
    """Entry point for the chat CLI."""
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        print("\n\nGoodbye!")


if __name__ == "__main__":
    main()
