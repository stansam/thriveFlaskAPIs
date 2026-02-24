from app.repository.subscription.repository import SubscriptionRepository
from app.repository.package.repository import PackageRepository
from app.repository.package_departure.repository import PackageDepartureRepository

print("Imports successful.")
repo1 = SubscriptionRepository()
repo2 = PackageRepository()
repo3 = PackageDepartureRepository()
print("Initialization successful.")
