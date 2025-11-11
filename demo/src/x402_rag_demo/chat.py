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
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not base_url or not x402_keypair_hex or not google_api_key:
        print("Error: Missing required environment variables.", file=sys.stderr)
        print("Please set: X402_RAG_BASE_URL, X402_KEYPAIR_HEX, GOOGLE_API_KEY", file=sys.stderr)
        sys.exit(1)

    return {
        "base_url": base_url,
        "x402_keypair_hex": x402_keypair_hex,
        "google_api_key": google_api_key,
    }


async def chat_loop() -> None:
    """Run the interactive chat loop."""
    env = load_env()

    print("=" * 60)
    print("X402 RAG Demo Agent")
    print("Powered by Gemini Flash 2.5 and X402 RAG")
    print("=" * 60)
    print("Type your questions and press Enter.")
    print("Type 'exit' or 'quit' to end the session.")
    print("=" * 60)
    print()

    agent = create_rag_agent(
        base_url=env["base_url"],
        x402_keypair_hex=env["x402_keypair_hex"],
        google_api_key=env["google_api_key"],
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
