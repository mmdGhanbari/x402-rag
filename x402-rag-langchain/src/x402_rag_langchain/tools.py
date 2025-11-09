from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel
from x402_rag_sdk import X402RagClient

from .schemas import X402RagGetChunksArgs, X402RagSearchArgs


class _X402RagBaseTool(BaseTool):
    """Base class holding the injected X402RagClient; async-only execution."""

    client: X402RagClient

    # Prevent accidental sync use; LangChain agents should call `ainvoke`/`_arun`.
    def _run(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        raise NotImplementedError(
            "X402Rag tools are async-only. Use `ainvoke`/`_arun` with an async agent or loop."
        )


class X402RagSearchTool(_X402RagBaseTool):
    """LangChain tool: Search the X402 RAG index."""

    name: str = "x402_rag_search"
    description: str = (
        "Search the X402 RAG index.\n"
        "Inputs: { query: str, k?: int=5, filters?: Record[str, str] }\n"
        "Returns a JSON object with total and a list of chunks."
    )
    args_schema: type[BaseModel] = X402RagSearchArgs  # type: ignore[assignment]

    async def _arun(
        self,
        query: str,
        k: int = 5,
        filters: dict[str, str] | None = None,
    ) -> dict[str, Any]:  # type: ignore[override]
        try:
            result = await self.client.search(query=query, k=k, filters=filters)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {
            "ok": True,
            "total": result.total,
            "chunks": [
                {
                    "text": c.text,
                    "metadata": c.metadata.model_dump(),
                }
                for c in result.chunks
            ],
        }


class X402RagGetChunksTool(_X402RagBaseTool):
    """LangChain tool: Fetch a range of chunks for a specific document."""

    name: str = "x402_rag_get_chunks"
    description: str = (
        "Fetch a chunk range for a specific document.\n"
        "Inputs: { doc_id: str, start_chunk: int, end_chunk?: int }\n"
        "Returns a JSON object with doc_id, total, and the selected chunks."
    )
    args_schema: type[BaseModel] = X402RagGetChunksArgs  # type: ignore[assignment]

    async def _arun(
        self,
        doc_id: str,
        start_chunk: int,
        end_chunk: int | None = None,
    ) -> dict[str, Any]:  # type: ignore[override]
        try:
            result = await self.client.get_chunk_range(
                doc_id=doc_id,
                start_chunk=start_chunk,
                end_chunk=end_chunk,
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {
            "ok": True,
            "doc_id": result.doc_id,
            "total": result.total,
            "chunks": [
                {
                    "text": c.text,
                    "metadata": c.metadata.model_dump(),
                }
                for c in result.chunks
            ],
        }


def make_x402_rag_tools(client: X402RagClient) -> list[BaseTool]:
    """Create both LangChain tools with a pre-initialized X402RagClient."""
    return [
        X402RagSearchTool(client=client),
        X402RagGetChunksTool(client=client),
    ]
