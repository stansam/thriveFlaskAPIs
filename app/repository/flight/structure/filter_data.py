from app.repository.flight.structure.filter_groups import (
    FilterAirlinesDTO, FilterAirportsDTO, FilterAlliance,
    FilterBaditin, FilterBfcDTO, FilterCabinDTO,
    FilterCfcDTO, FilterCurrencyDTO, FilterEqModelDTO,
    FilterEquipmentDTO, FilterHideBasicDTO, FilterLandingDTO,
    FilterLayoverAirDTO, FilterLayoverDurDTO, FilterLegDurDTO,
    FilterPfcDTO, FilterPriceDTO, FilterProvidersDTO,
    FilterRedeyeDTO, FilterSameAirDTO, FilterSpecificLegDTO,
    FilterSplitDTO, FilterStopsDTO, FilterTakeOffDTO,
    FilterWifiDTO
    )
from typing import List 

class FilterDataDTO(BaseModel):
    airlines: List[FilterAirlinesDTO] = []
    airports: List[FilterAirportsDTO] = []
    alliance: List[FilterAllianceDTO] = []
    baditin: List[FilterBaditinDTO] = []
    bfc: List[FilterBfcDTO] = []
    cabin: List[FilterCabinDTO] = []
    cfc: List[FilterCfcDTO] = []
    currency: List[FilterCurrencyDTO] = []
    eqmodel: List[FilterEqModelDTO] = []
    equipment: List[FilterEquipmentDTO] = []
    hidebasic: List[FilterHideBasicDTO] = []
    landing: List[FilterLandingDTO] = []
    layoverair: List[FilterLayoverAirDTO] = []
    layiverdur: List[FilterLayoverDurDTO] = []
    legdur: List[FilterLegDurDTO] = []
    pfc: List[FilterPfcDTO] = []
    price: List[FilterPriceDTO] = []
    providers: List[FilterProvidersDTO] = []
    redeye: List[FilterRedeyeDTO] = []
    sameair: List[FilterSameAirDTO] = []
    specificleg: List[FilterSpecificLegDTO] = []
    split: List[FilterSplitDTO] = []
    stops: List[FilterStopsDTO] = []
    takeoff: List[FilterTakeOffDTO] = []
    wifi: List[FilterWifiDTO] = []
    # filtered_count: int
    # filtered_results_recommendation: 


