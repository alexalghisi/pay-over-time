from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite+pysqlite:///./paylater.db"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> Settings:
        origins = env.get("PAYLATER_CORS_ORIGINS", ",".join(cls.cors_origins))
        return cls(
            database_url=env.get("PAYLATER_DATABASE_URL", cls.database_url),
            cors_origins=tuple(origin.strip() for origin in origins.split(",") if origin.strip()),
        )
