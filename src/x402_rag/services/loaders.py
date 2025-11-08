"""Document loaders for PDFs and web pages."""

import asyncio

import pymupdf4llm
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_loaders.chromium import AsyncChromiumLoader
from langchain_core.documents import Document

from x402_rag.core import Settings

from .utils import looks_like_spa


async def parse_pdf_to_markdown(path: str) -> str:
    """
    Parse a PDF file to markdown format.
    CPU-bound operation run in a worker thread.
    """
    return await asyncio.to_thread(pymupdf4llm.to_markdown, path)


async def load_url_static(url: str) -> list[Document]:
    """Load URL content using static HTML parsing."""
    loader = AsyncHtmlLoader(web_path=[url])
    docs = await loader.aload()
    return docs or []


async def load_url_js(url: str) -> list[Document]:
    """Load URL content using JavaScript rendering (Playwright/Chromium)."""
    loader = AsyncChromiumLoader(urls=[url])
    docs = await loader.aload()
    for d in docs:
        d.page_content = (d.page_content or "").strip()
    return docs or []


async def load_url_auto(url: str, settings: Settings) -> list[Document]:
    """
    Automatically choose between static and JS loading.
    Falls back to JS rendering if content is insufficient or looks like SPA.
    """
    static_docs = await load_url_static(url)
    baseline = static_docs[0].page_content.strip() if static_docs else ""

    if not settings.use_playwright_fallback:
        return static_docs

    need_js = (len(baseline) < settings.min_text_len) or looks_like_spa(baseline)

    if need_js:
        try:
            js_docs = await load_url_js(url)
            js_text = js_docs[0].page_content.strip() if js_docs else ""
            if len(js_text) > len(baseline):
                return js_docs
        except Exception:
            # Fall back to static if JS loading fails
            pass

    return static_docs
