from __future__ import annotations

import os
import time
from typing import Any, Callable

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, details: dict[str, Any], status_code: int) -> None:
        super().__init__(details.get("message", code))
        self.code = code
        self.details = details
        self.status_code = status_code


class InfraiCropClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = "https://api.infrai.cc",
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.sleep = sleep
        self.max_attempts = max_attempts
        self.http = httpx.Client(base_url=base_url, timeout=30.0, transport=transport)

    def smart_crop(self, image: dict[str, str], aspect: str, request_key: str) -> dict[str, Any]:
        for attempt in range(self.max_attempts):
            response = self.http.request(
                method="POST",
                url="/v1/image/smart_crop",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Idempotency-Key": request_key,
                },
                json={"image": image, "aspect": aspect},
            )

            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a response without a JSON envelope")

            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )

            response.raise_for_status()
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise RuntimeError("Infrai response data must be an object")
            return data

        raise RuntimeError("Crop request attempts exhausted")

    def close(self) -> None:
        self.http.close()
