from app.interface.adapter.flight import KayakFlightSearchAdapter
from app.interface.adapter.flight_details import KayakFlightDetailsAdapter
from app.interface.adapter.locations import KayakLocationsAdapter

class KayakAdapter:
    def __init__(self):
        self._flight_search: KayakFlightSearchAdapter | None = None
        self._location_search: KayakLocationsAdapter | None = None
        self._flight_details: KayakFlightDetailsAdapter | None = None

    @property
    def flight_search(self) -> KayakFlightSearchAdapter:
        if self._flight_search is None:
            self._flight_search = KayakFlightSearchAdapter()
        return self._flight_search

    @property
    def flight_details(self) -> KayakFlightDetailsAdapter:
        if self._flight_details is None:
            self._flight_details = KayakFlightDetailsAdapter()
        return self._flight_details

    @property
    def location_search(self) -> KayakLocationsAdapter:
        if self._location_search is None:
            self._location_search = KayakLocationsAdapter()
        return self._location_search

adapter = KayakAdapter()

__all__ = ["adapter"]