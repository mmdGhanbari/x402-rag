"""X402 RAG client implementation."""

import httpx
from solders.keypair import Keypair

from .auth import build_solana_authorization_header
from .config import ClientConfig
from .exceptions import (
    X402RagConnectionError,
    X402RagHTTPError,
    X402RagTimeoutError,
)
from .schemas import (
    DocumentToIndex,
    FetchChunksByRangeRequest,
    FetchChunksByRangeResult,
    IndexDocsRequest,
    IndexResult,
    IndexWebPagesRequest,
    PaymentInfo,
    SearchRequest,
    SearchResult,
    WebPageToIndex,
)
from .x402 import X402SolanaConfig, X402SolanaPayer, build_x_payment_from_402_json


class X402RagClient:
    """Client for interacting with the X402 RAG server.

    Example:
        >>> from x402_rag_sdk import X402RagClient, ClientConfig
        >>> config = ClientConfig(
        ...     base_url="http://localhost:8000",
        ...     x402_keypair_hex="YOUR_64_BYTE_KEYPAIR_HEX"
        ... )
        >>> client = X402RagClient(config)
        >>>
        >>> # Index documents
        >>> result = await client.index_docs([
        ...     {"path": "/path/to/doc.pdf", "price_usd": 0.01}
        ... ])
        >>>
        >>> # Search documents
        >>> results = await client.search("machine learning", k=5)
    """

    def __init__(self, config: ClientConfig):
        """Initialize the X402 RAG client.

        Args:
            config: Client configuration containing base_url and other settings
        """
        self.config = config
        self._client: httpx.AsyncClient | None = None
        self._x402_payer: X402SolanaPayer | None = None
        self._auth_keypair: Keypair | None = None

        # Initialize keypair for auth and x402 if config is provided
        if config.x402_keypair_hex:
            self._auth_keypair = Keypair.from_bytes(bytes.fromhex(config.x402_keypair_hex))
            x402_config = X402SolanaConfig(
                rpc_by_network=config.x402_rpc_by_network,
            )
            self._x402_payer = X402SolanaPayer(self._auth_keypair, x402_config)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self):
        """Ensure the HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )

    async def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict | None = None,
    ) -> tuple[dict, PaymentInfo | None]:
        """Make an HTTP request to the server.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            json_data: JSON data to send in the request body

        Returns:
            Tuple of (response JSON, payment info if payment was made)

        Raises:
            X402RagHTTPError: If the request returns an HTTP error
            X402RagConnectionError: If a connection error occurs
            X402RagTimeoutError: If the request times out
        """
        await self._ensure_client()

        # Build headers
        headers = {}
        if self._auth_keypair:
            full_uri = f"{self.config.base_url}{path}"
            headers["Authorization"] = build_solana_authorization_header(
                keypair=self._auth_keypair,
                uri=full_uri,
            )

        payment_info: PaymentInfo | None = None

        try:
            response = await self._client.request(
                method=method,
                url=path,
                json=json_data,
                headers=headers,
            )

            # Handle 402 Payment Required if x402 payer is configured
            if response.status_code == 402 and self._x402_payer:
                # Parse the 402 body and build payment
                body = response.json()

                # Build payment and extract payment info
                x_payment, paid_amount, pay_to = await build_x_payment_from_402_json(
                    payer=self._x402_payer,
                    x402_body=body,
                    asset_decimals=self.config.x402_asset_decimals,
                )

                # Retry with X-PAYMENT header (keep Authorization header)
                headers["X-PAYMENT"] = x_payment
                response = await self._client.request(
                    method=method,
                    url=path,
                    json=json_data,
                    headers=headers,
                )

                # Create payment info after successful payment
                payment_info = PaymentInfo(paid_amount=paid_amount, pay_to=pay_to)

            response.raise_for_status()
            return response.json(), payment_info
        except httpx.HTTPStatusError as e:
            detail = "Unknown error"
            try:
                detail = e.response.json().get("detail", detail)
            except Exception:
                pass
            raise X402RagHTTPError(e.response.status_code, detail) from e
        except httpx.TimeoutException as e:
            raise X402RagTimeoutError("Request timed out") from e
        except httpx.ConnectError as e:
            raise X402RagConnectionError(f"Connection error: {str(e)}") from e
        except Exception as e:
            raise X402RagConnectionError(f"Unexpected error: {str(e)}") from e

    async def index_docs(
        self,
        documents: list[DocumentToIndex] | list[dict],
    ) -> IndexResult:
        """Index documents from file paths.

        Args:
            documents: List of documents to index with their prices.
                Each document should have 'path' and 'price_usd' fields.

        Returns:
            IndexResult containing information about indexed documents

        Example:
            >>> result = await client.index_docs([
            ...     {"path": "/path/to/doc1.pdf", "price_usd": 0.01},
            ...     {"path": "/path/to/doc2.txt", "price_usd": 0.005},
            ... ])
        """
        # Convert dicts to DocumentToIndex if needed
        doc_list = [doc if isinstance(doc, DocumentToIndex) else DocumentToIndex(**doc) for doc in documents]

        request = IndexDocsRequest(documents=doc_list)
        response, _ = await self._request("POST", "/docs/index", request.model_dump())
        return IndexResult(**response)

    async def index_web_pages(
        self,
        pages: list[WebPageToIndex] | list[dict],
    ) -> IndexResult:
        """Index web pages from URLs.

        Args:
            pages: List of web pages to index with their prices.
                Each page should have 'url' and 'price_usd' fields.

        Returns:
            IndexResult containing information about indexed web pages

        Example:
            >>> result = await client.index_web_pages([
            ...     {"url": "https://example.com/page1", "price_usd": 0.01},
            ...     {"url": "https://example.com/page2", "price_usd": 0.01},
            ... ])
        """
        # Convert dicts to WebPageToIndex if needed
        page_list = [page if isinstance(page, WebPageToIndex) else WebPageToIndex(**page) for page in pages]

        request = IndexWebPagesRequest(pages=page_list)
        response, _ = await self._request("POST", "/docs/index/web", request.model_dump())
        return IndexResult(**response)

    async def search(
        self,
        query: str,
        k: int = 5,
        filters: dict[str, str] | None = None,
    ) -> SearchResult:
        """Search for documents similar to the query text.

        Args:
            query: Search query text
            k: Number of results to return (default: 5)
            filters: Optional metadata filters to apply

        Returns:
            SearchResult containing matching document chunks

        Example:
            >>> result = await client.search("machine learning", k=10)
            >>> for chunk in result.chunks:
            ...     print(chunk.text)
        """
        request = SearchRequest(query=query, k=k, filters=filters)
        response, payment_info = await self._request("POST", "/docs/search", request.model_dump())
        result = SearchResult(**response)
        if payment_info:
            result.payment = payment_info
        return result

    async def get_chunk_range(
        self,
        doc_id: str,
        start_chunk: int,
        end_chunk: int | None = None,
    ) -> FetchChunksByRangeResult:
        """Fetch a range of chunks for a specific document.

        Args:
            doc_id: Document ID
            start_chunk: Starting chunk index (inclusive)
            end_chunk: Ending chunk index (inclusive, optional)

        Returns:
            FetchChunksByRangeResult containing the requested chunks

        Example:
            >>> result = await client.get_chunk_range("doc123", 0, 10)
            >>> print(f"Retrieved {result.total} chunks")
        """
        request = FetchChunksByRangeRequest(
            doc_id=doc_id,
            start_chunk=start_chunk,
            end_chunk=end_chunk,
        )
        response, payment_info = await self._request("POST", "/docs/chunks", request.model_dump())
        result = FetchChunksByRangeResult(**response)
        if payment_info:
            result.payment = payment_info
        return result
