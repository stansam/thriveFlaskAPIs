import pytest
from app.repository.package.services import PackageService
from app.models.enums import ActivityType

def test_create_package(db_session):
    service = PackageService(db_session)
    package_data = {
        "title": "Summer Escape",
        "description": "A wonderful trip",
        "base_price": 1200.00,
        "duration_days": 5,
        "itinerary": [
            {
                "day_number": 1,
                "title": "Arrival",
                "activity_type": "transfer"
            },
            {
                "day_number": 2,
                "title": "City Tour",
                "activity_type": "sightseeing"
            }
        ],
        "inclusions": [
             {"description": "Breakfast"},
             {"description": "Airport Transfer"}
        ]
    }
    
    package = service.create_package(package_data)
    assert package.id is not None
    assert package.title == "Summer Escape"
    assert package.slug.startswith("summer-escape")
    
    # Check assertions on relationships
    assert package.itinerary.count() == 2
    assert package.inclusions.count() == 2

def test_get_package(db_session):
    service = PackageService(db_session)
    # create a package first
    package_data = {
        "title": "Test Package",
        "base_price": 100.00,
        "duration_days": 1
    }
    created = service.create_package(package_data)
    
    fetched = service.get_package_by_id(created.id)
    assert fetched.id == created.id
    assert fetched.title == "Test Package"

def test_search_packages(db_session):
    service = PackageService(db_session)
    # Create sample packages
    service.create_package({"title": "Cheap Trip", "base_price": 500.0, "duration_days": 3})
    service.create_package({"title": "Expensive Trip", "base_price": 5000.0, "duration_days": 10})
    
    # Test filters
    results = service.search_packages({"max_price": 1000.0})
    assert len(results) >= 1
    assert any(p.title == "Cheap Trip" for p in results)
    assert not any(p.title == "Expensive Trip" for p in results)

def test_update_package(db_session):
    service = PackageService(db_session)
    created = service.create_package({"title": "Old Title", "base_price": 100.00, "duration_days": 1})
    
    updated = service.update_package(created.id, {"title": "New Title", "base_price": 150.00})
    assert updated.title == "New Title"
    assert updated.base_price == 150.00
