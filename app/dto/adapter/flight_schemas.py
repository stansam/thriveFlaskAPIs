from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

# ------------------------------------------------------------------------
# 1. Airport Search DTOs
# ------------------------------------------------------------------------

class AirportSearchResultDTO(BaseModel):
    id: str
    airportname: str
    cityname: str
    displayname: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    countrycode: Optional[str] = None
    lat: float
    lng: float
    timezone: str

class AirportSearchResponseDTO(BaseModel):
    success: bool
    error: Optional[str] = None
    data: Dict[str, Any] # Contains 'query', 'count', and 'results'
    
    @property
    def results(self) -> List[AirportSearchResultDTO]:
        return [AirportSearchResultDTO(**r) for r in self.data.get('results', [])]

# ------------------------------------------------------------------------
# 2. Flight Details (Live Tracking) DTOs
# ------------------------------------------------------------------------

class FlightLiveSegmentDTO(BaseModel):
    aircraftTypeName: Optional[str] = None
    airlineCode: str
    airlineDispName: str
    airlineLogoURL: Optional[str] = None
    altitude: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    speed: Optional[float] = None
    
    departureAirport: str
    departureAirportName: str
    departureAirportCity: Optional[str] = None
    departureCity: Optional[str] = None
    departureGateTime: Optional[int] = None
    departureGateScheduled: Optional[int] = None
    
    arrivalAirport: str
    arrivalAirportName: str
    arrivalAirportCity: Optional[str] = None
    arrivalCity: Optional[str] = None
    arrivalGateTime: Optional[int] = None
    arrivalGateScheduled: Optional[int] = None
    
    flightDuration: Optional[int] = None
    flightNumber: int
    flightNumberString: str
    statusCode: str

class FlightDetailsDataDTO(BaseModel):
    error: bool
    flights: List[FlightLiveSegmentDTO]
    query_info: Dict[str, Any]
    total_flights: int

class FlightDetailsResponseDTO(BaseModel):
    success: bool
    error: Optional[str] = None
    data: FlightDetailsDataDTO

# ------------------------------------------------------------------------
# 3. Flight Search Mapping DTOs (Live Inventory)
# ------------------------------------------------------------------------

class GDSPriceDTO(BaseModel):
    currency: str
    localizedPrice: str
    price: float

class GDSAirlineFeeUrlDTO(BaseModel):
    url: str
    urlType: str

class GDSAirlineDTO(BaseModel):
    name: str
    airlineFeeUrl: Optional[GDSAirlineFeeUrlDTO] = None
    logoUrl: Optional[GDSAirlineFeeUrlDTO] = None

class GDSCityAirportDTO(BaseModel):
    cityCode: str
    cityName: str
    displayName: str
    fullDisplayName: str

class GDSSegmentDTO(BaseModel):
    # Depending heavily on dynamic physical layouts, these hold physical string-bound values natively.
    # Ex: "1771574400000NK16930320" -> Contains timestamps and airline tags encoded.
    pass

class GDSLegDTO(BaseModel):
    # Legs map segment blocks inherently together.
    pass

class GDSProviderDTO(BaseModel):
    pass

class GDSFlightResultsDTO(BaseModel):
    pass

class GDSFlightSearchDataDTO(BaseModel):
    airlines: Dict[str, GDSAirlineDTO] = {}
    airports: Dict[str, GDSCityAirportDTO] = {}
    isUserInitiated: bool = True
    pageNumber: int = 1
    pageSize: int = 50
    totalCount: int = 0
    filteredCount: int = 0
    priceMode: str = ""
    status: str = ""
    sortMode: str = ""
    # Heavy graph mappings safely bound into Any to permit targeted extraction downstream
    legs: Dict[str, Any] = {}
    segments: Dict[str, Any] = {}
    providers: Dict[str, Any] = {}
    results: List[Any] = []

class GDSFlightSearchResponseDTO(BaseModel):
    success: bool
    error: Optional[str] = None
    data: GDSFlightSearchDataDTO
