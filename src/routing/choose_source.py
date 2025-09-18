from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass(frozen=True)
class ProviderCaps:
    min_year: int
    max_year: int
    max_level: int
    units: List[str]

class NoDataError(Exception):
    pass

def choose_source(geo: str, year: int, desired_level: int, order: List[str], coverage: Dict[Tuple[str, str], ProviderCaps]) -> Tuple[str, int]:
    if geo in {"UK", "GB", "GBR"}:
        if year >= 2021:
            order = ["OECD", "IMF", "EUROSTAT"]

    for provider in order:
        caps = coverage.get((provider, geo))
        if caps and caps.min_year <= year <= caps.max_year:
            level = min(desired_level, caps.max_level)
            if level is not None:
                return provider, level

    raise NoDataError(f"No provider for {geo} {year} at level {desired_level}")
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass(frozen=True)
class ProviderCaps:
    min_year: int
    max_year: int
    max_level: int
    units: List[str]

class NoDataError(Exception):
    pass

def choose_source(geo: str, year: int, desired_level: int, order: List[str], coverage: Dict[Tuple[str, str], ProviderCaps]) -> Tuple[str, int]:
    if geo in {"UK", "GB", "GBR"}:
        if year >= 2021:
            order = ["OECD", "IMF", "EUROSTAT"]

    for provider in order:
        caps = coverage.get((provider, geo))
        if caps and caps.min_year <= year <= caps.max_year:
            level = min(desired_level, caps.max_level)
            if level is not None:
                return provider, level

    raise NoDataError(f"No provider for {geo} {year} at level {desired_level}")