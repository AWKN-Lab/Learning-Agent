from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    app_env: str
    session_ttl_seconds: int
    max_body_bytes: int
    rate_window_seconds: int
    start_rate_limit: int
    step_rate_limit: int
    trusted_hosts: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "AppSettings":
        app_env = os.getenv("APP_ENV", "demo").strip().lower()
        trusted_raw = os.getenv(
            "TRUSTED_HOSTS",
            "localhost,127.0.0.1,testserver",
        )
        trusted_hosts = tuple(
            host.strip()
            for host in trusted_raw.split(",")
            if host.strip()
        )
        settings = cls(
            app_env=app_env,
            session_ttl_seconds=int(
                os.getenv("SESSION_TTL_SECONDS", "7200")
            ),
            max_body_bytes=int(os.getenv("MAX_BODY_BYTES", "8192")),
            rate_window_seconds=int(
                os.getenv("RATE_WINDOW_SECONDS", "60")
            ),
            start_rate_limit=int(os.getenv("START_RATE_LIMIT", "30")),
            step_rate_limit=int(os.getenv("STEP_RATE_LIMIT", "120")),
            trusted_hosts=trusted_hosts,
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.app_env not in {
            "development",
            "demo",
            "test",
            "production",
        }:
            raise RuntimeError("invalid_APP_ENV")
        if self.session_ttl_seconds < 60:
            raise RuntimeError("SESSION_TTL_SECONDS_must_be_at_least_60")
        if self.max_body_bytes < 1024:
            raise RuntimeError("MAX_BODY_BYTES_must_be_at_least_1024")
        if self.rate_window_seconds < 1:
            raise RuntimeError("RATE_WINDOW_SECONDS_must_be_positive")
        if self.start_rate_limit < 1 or self.step_rate_limit < 1:
            raise RuntimeError("rate_limits_must_be_positive")
        if self.app_env == "production":
            raw = os.getenv("TRUSTED_HOSTS", "").strip()
            if not raw or not self.trusted_hosts:
                raise RuntimeError("TRUSTED_HOSTS_required_in_production")
            if "*" in self.trusted_hosts:
                raise RuntimeError("wildcard_TRUSTED_HOSTS_forbidden")
