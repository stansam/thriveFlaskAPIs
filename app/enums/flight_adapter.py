# app/enums/flight_adapter.py
"""
Flight search enums.
"""
from __future__ import annotations

from enum import Enum

class PassengerType(str, Enum):
    ADT = "ADT"  # Adult 18-64
    SNR = "SNR"  # Senior over 65
    STD = "STD"  # Student over 18
    YTH = "YTH"  # Youth 12-17
    CHD = "CHD"  # Child 2-11
    INS = "INS"  # Toddler in own seat under 2
    INL = "INL"  # Infant on lap under 2


class CabinClass(str, Enum):
    ECONOMY = "e"
    PREMIUM_ECONOMY = "p"
    BUSINESS = "b"
    FIRST = "f"


class SortMode(str, Enum):
    PRICE_ASC = "price_a"
    DURATION_ASC = "duration_a"
    BEST = "bestflight_a"
    DEPARTURE_ASC = "departure_a"
    ARRIVAL_ASC = "arrival_a"
