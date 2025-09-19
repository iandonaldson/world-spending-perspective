import pytest
from cofogviz.routing.choose_source import choose_source, ProviderCaps, NoDataError

def test_choose_source():
    coverage = {
        ("EUROSTAT", "NO"): ProviderCaps(min_year=2000, max_year=2023, max_level=3, units=["MIO_EUR", "PC_TOT"]),
        ("OECD", "NO"): ProviderCaps(min_year=1995, max_year=2023, max_level=2, units=["MIO_NAC"]),
        ("IMF", "NO"): ProviderCaps(min_year=1980, max_year=2023, max_level=1, units=["MIO_NAC"]),
    }

    provider, level = choose_source("NO", 2023, 2, ["EUROSTAT", "OECD", "IMF"], coverage)
    assert provider == "EUROSTAT"
    assert level == 2

    provider, level = choose_source("NO", 1990, 1, ["EUROSTAT", "OECD", "IMF"], coverage)
    assert provider == "IMF"
    assert level == 1

    with pytest.raises(NoDataError):
        choose_source("NO", 2025, 3, ["EUROSTAT", "OECD", "IMF"], coverage)