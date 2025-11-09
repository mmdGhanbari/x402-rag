"""Exceptions for X402 RAG client."""


class X402RagError(Exception):
    """Base exception for X402 RAG client errors."""

    pass


class X402RagHTTPError(X402RagError):
    """Exception raised when an HTTP error occurs."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class X402RagConnectionError(X402RagError):
    """Exception raised when a connection error occurs."""

    pass


class X402RagTimeoutError(X402RagError):
    """Exception raised when a request times out."""

    pass
