"""
Simulated time-of-use electricity pricing.

Loosely based on California's TOU-D-PRIME rate structure (PG&E).
Real-time pricing data can be fetched from CAISO OASIS API if desired.

Source: https://www.pge.com/tariffs/electric.shtml
"""

# $/kWh by hour of day (0 = midnight)
_HOURLY_PRICES = [
    0.078,  # 12 AM
    0.072,  # 1 AM
    0.070,  # 2 AM
    0.068,  # 3 AM
    0.070,  # 4 AM
    0.075,  # 5 AM
    0.090,  # 6 AM
    0.110,  # 7 AM
    0.130,  # 8 AM
    0.140,  # 9 AM
    0.145,  # 10 AM
    0.148,  # 11 AM
    0.150,  # 12 PM
    0.155,  # 1 PM
    0.158,  # 2 PM
    0.165,  # 3 PM
    0.175,  # 4 PM
    0.210,  # 5 PM — peak begins
    0.240,  # 6 PM — peak
    0.250,  # 7 PM — peak
    0.235,  # 8 PM — peak ends
    0.180,  # 9 PM
    0.130,  # 10 PM
    0.095,  # 11 PM
]


def get_grid_price(hour: int) -> float:
    """Return the simulated grid electricity price ($/kWh) for a given hour."""
    return _HOURLY_PRICES[hour % 24]
