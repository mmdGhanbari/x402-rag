"""Utility functions for RAG services."""

import hashlib
import re
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter

from x402_rag.core import Settings


def sha256_hex(s: str) -> str:
    """Generate SHA256 hash of a string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def stable_chunk_uuid(doc_id: str, chunk_idx: int) -> str:
    """
    Generate a deterministic UUID derived from (doc_id, chunk_idx).
    Uses SHA1 (hex[:32]) -> UUID, which is stable and compact.
    """
    h = hashlib.sha1(f"{doc_id}:{chunk_idx}".encode()).hexdigest()[:32]
    return str(uuid.UUID(h))


def build_doc_id(source: str) -> str:
    """Generate robust doc_id from canonical source string (path or URL)."""
    return sha256_hex(source)


def looks_like_spa(html_text: str) -> bool:
    """
    Heuristic to detect if HTML looks like a Single Page App
    that needs JavaScript rendering.
    """
    h = (html_text or "").lower()
    patterns = [
        r'<div[^>]+id=["\']root["\']',
        r'<div[^>]+id=["\']__next["\']',
        r'<div[^>]+id=["\']app["\']',
        r"data-reactroot",
    ]
    score = sum(bool(re.search(p, h)) for p in patterns)
    many_scripts = h.count("<script") >= 8
    return score >= 1 or many_scripts


def build_text_splitter(settings: Settings) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )
