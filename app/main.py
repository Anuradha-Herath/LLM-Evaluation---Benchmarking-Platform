from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router_v1
from app.api.v1.health import health_check
from app.core.config import settings


def create_app() -> FastAPI:
    """
    FastAPI Application Factory.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="A platform to systematically evaluate, benchmark, and track LLM models and prompt configurations.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include root /health endpoint for basic container probes
    app.add_api_route(
        "/health",
        endpoint=health_check,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        tags=["Health"],
        include_in_schema=True,
    )

    # Include API Routers
    app.include_router(router_v1, prefix="/api")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
