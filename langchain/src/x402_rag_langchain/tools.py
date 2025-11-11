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
        raise NotImplementedError("X402Rag tools are async-only. Use `ainvoke`/`_arun` with an async agent or loop.")


class X402RagSearchTool(_X402RagBaseTool):
    """LangChain tool: Search the RAG index."""

    name: str = "search"
    description: str = (
        "Search the RAG index.\n"
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

    name: str = "get_chunks"
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


def make_x402_rag_tools(
    client: X402RagClient,
    *,
    prefix: str = "",
    context_description: str = "",
    search_description: str | None = None,
    get_chunks_description: str | None = None,
) -> list[BaseTool]:
    """Create both LangChain tools with a pre-initialized X402RagClient.

    Args:
        client: X402RagClient instance to use for the tools.
        prefix: Optional prefix to add to tool names (e.g., 'company_docs' -> 'company_docs_search').
        context_description: Optional context description prepended to all tool descriptions
            to help agents distinguish between multiple tool sets.
        search_description: Optional custom description for the search tool.
            If not provided, uses default description with context_description prepended.
        get_chunks_description: Optional custom description for the get_chunks tool.
            If not provided, uses default description with context_description prepended.

    Returns:
        List of configured LangChain tools.

    Example:
        >>> tools = make_x402_rag_tools(
        ...     client=client,
        ...     prefix="company_docs",
        ...     context_description="Search through internal company documentation and policies.",
        ... )
        >>> # Creates tools: 'company_docs_search' and 'company_docs_get_chunks'
    """
    search_tool = X402RagSearchTool(client=client)
    get_chunks_tool = X402RagGetChunksTool(client=client)

    # Apply prefix to tool names
    if prefix:
        search_tool.name = f"{prefix}_search"
        get_chunks_tool.name = f"{prefix}_get_chunks"

    # Apply context and custom descriptions
    if context_description or search_description:
        if search_description:
            search_tool.description = search_description
        elif context_description:
            search_tool.description = f"{context_description}\n\n{search_tool.description}"

    if context_description or get_chunks_description:
        if get_chunks_description:
            get_chunks_tool.description = get_chunks_description
        elif context_description:
            get_chunks_tool.description = f"{context_description}\n\n{get_chunks_tool.description}"

    return [search_tool, get_chunks_tool]
