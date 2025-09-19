import httpx
import asyncio
import logging
import random
import time
from typing import Optional

class AsyncSharedHttpClient:
    def __init__(self, timeout: float = 30.0, max_retries: int = 3, backoff_base: float = 0.2):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "world-spending-perspective/0.1"})

    async def get(self, url: str, **kwargs) -> httpx.Response:
        for attempt in range(self.max_retries):
            start = time.time()
            try:
                response = await self.client.get(url, **kwargs)
                duration = int((time.time() - start) * 1000)
                logging.info({
                    "event": "http_get",
                    "url": url,
                    "status_code": response.status_code,
                    "duration_ms": duration,
                    "attempt": attempt + 1
                })
                if response.status_code < 400:
                    return response
                if response.status_code in {429, 500, 502, 503, 504}:
                    # Retryable error
                    await asyncio.sleep(self.backoff_base * (2 ** attempt) + random.uniform(0, 0.1))
                else:
                    response.raise_for_status()
            except httpx.RequestError as e:
                duration = int((time.time() - start) * 1000)
                logging.error({
                    "event": "http_error",
                    "url": url,
                    "error": str(e),
                    "duration_ms": duration,
                    "attempt": attempt + 1
                })
                await asyncio.sleep(self.backoff_base * (2 ** attempt) + random.uniform(0, 0.1))
        raise RuntimeError(f"Max retries exceeded for {url}")
