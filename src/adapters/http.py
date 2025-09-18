import httpx
from typing import Optional

class SharedHttpClient:
    def __init__(self, timeout: float = 10.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(timeout=timeout)

    def get(self, url: str, **kwargs) -> httpx.Response:
        for attempt in range(self.max_retries):
            try:
                return self.client.get(url, **kwargs)
            except httpx.RequestError as e:
                if attempt == self.max_retries - 1:
                    raise
        raise RuntimeError("Max retries exceeded")
