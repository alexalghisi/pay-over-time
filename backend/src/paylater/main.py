from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from paylater.api.routes import router
from paylater.api.schemas import ErrorOut
from paylater.db.models import Base
from paylater.domain.errors import DomainError
from paylater.service import Clock, PayLaterService, utc_now
from paylater.settings import Settings


def build_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite") and ":memory:" in database_url:
        return create_engine(
            database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    return create_engine(database_url, pool_pre_ping=True)


async def _domain_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    body = ErrorOut(code=exc.code, message=str(exc))
    return JSONResponse(status_code=exc.status_code, content={"error": body.model_dump()})


def create_app(settings: Settings | None = None, clock: Clock = utc_now) -> FastAPI:
    resolved = settings or Settings.from_env()
    engine = build_engine(resolved.database_url)
    Base.metadata.create_all(engine)

    app = FastAPI(
        title="Pay over time",
        version="0.1.0",
        summary="Quotes, plans and repayments for UK and Canadian customers.",
    )
    app.state.service = PayLaterService(sessionmaker(engine, expire_on_commit=False), clock)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )
    app.add_exception_handler(DomainError, _domain_error)
    app.include_router(router)

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
