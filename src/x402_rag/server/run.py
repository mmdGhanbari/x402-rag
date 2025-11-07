import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import get_settings
from .logging import setup_logging
from .routers import docs

app = FastAPI(
    title="X402 RAG Server",
    description="FastAPI server exposing the X402 RAG API",
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docs.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def bootstrap():
    """Main entry point for running the server."""
    settings = get_settings()
    setup_logging(settings)

    uvicorn.run(
        "x402_rag.server.run:app",
        host=settings.server_host,
        port=settings.server_port,
    )


if __name__ == "__main__":
    bootstrap()
