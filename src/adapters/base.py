from dataclasses import dataclass
from typing import Iterable, Literal, List

Level = Literal[1, 2, 3]

@dataclass(frozen=True)
class ProviderCaps:
    min_year: int
    max_year: int
    max_level: Level
    units: List[str]

class ProviderAdapter:
    name: str
    dataset_id_functions: str
    dataset_id_totals: str

    async def capabilities(self, geo: str) -> ProviderCaps:
        raise NotImplementedError()

    async def fetch_functions(self, geo: str, year: int, level: Level) -> Iterable[dict]:
        raise NotImplementedError()

    async def fetch_totals(self, geo: str, year: int) -> Iterable[dict]:
        raise NotImplementedError()
