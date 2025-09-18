from typing import Any, Dict, List
from pydantic import BaseModel

class ProviderCaps(BaseModel):
    name: str
    supports_cofog_levels: List[int]
    # Add more capability fields as needed

class ProviderAdapter:
    def capabilities(self) -> ProviderCaps:
        raise NotImplementedError()

    def fetch_functions(self, *args, **kwargs) -> Any:
        raise NotImplementedError()

    def fetch_totals(self, *args, **kwargs) -> Any:
        raise NotImplementedError()
