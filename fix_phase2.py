import re

def inplace_change(filename, old_string, new_string):
    with open(filename) as f:
        s = f.read()
        if old_string not in s:
            return
    with open(filename, 'w') as f:
        s = s.replace(old_string, new_string)
        f.write(s)

# 1. DTOs
inplace_change("app/dto/package_items.py",
"""class PackageItemResponse(BaseModel):""",
"""from app.dto.package_media import PackageMediaBriefResponse
class PackageItemResponse(BaseModel):""")

inplace_change("app/dto/hotel_booking.py",
"""class HotelBookingResponse(BookingResponse):""",
"""from app.dto.booking import BookingPassengerResponse
class HotelBookingResponse(BookingResponse):""")

# 2. booking.py
inplace_change("app/models/booking.py",
"""from app.models.fee import ServiceFeeSnapshot""",
"""from app.models.fee_snapshot import ServiceFeeSnapshot""")
inplace_change("app/models/booking.py",
"""from app.models.payment import Payment""",
"""from app.models.payment import Payment
    from app.models.booking_passenger import BookingPassenger""")

# 3. media.py
inplace_change("app/models/media.py",
"""from app.models.media_asset import MediaAsset""",
"""""") # Remove the circular/double import

inplace_change("app/models/media.py",
"""    from app.models.package_itinerary_days import PackageItineraryDay""",
"""    from app.models.package_itinerary_days import PackageItineraryDay
    from app.models.package_media import PackageMedia""")

# 4. package.py
inplace_change("app/models/package.py",
"""from app.models.booking import PackageBooking""",
"""from app.models.package_booking import PackageBooking""")

inplace_change("app/models/package.py",
"""from app.models.booking import PackageBooking""",
"""from app.models.package_booking import PackageBooking""") # In case it didn't hit

inplace_change("app/models/package.py",
"""if TYPE_CHECKING:
    from app.models.package_booking import PackageBooking""",
"""if TYPE_CHECKING:
    from app.models.package_booking import PackageBooking
    from app.models.package_items import PackageHighlight, PackageInclusion, PackageItineraryDay
    from app.models.package_price_tier import PackagePriceTier""")

# 5. fee.py, fee_snapshot.py, fee_schedule.py
inplace_change("app/models/fee.py",
"""if TYPE_CHECKING:""",
"""if TYPE_CHECKING:
    from app.models.fee_schedule import ServiceFeeSchedule""")

inplace_change("app/models/fee_snapshot.py",
"""if TYPE_CHECKING:""",
"""if TYPE_CHECKING:
    from app.models.booking import Booking""")

inplace_change("app/models/fee_schedule.py",
"""if TYPE_CHECKING:""",
"""if TYPE_CHECKING:
    from app.models.fee import ServiceFee""")

# 6. booking_passenger.py
inplace_change("app/models/booking_passenger.py",
"""if TYPE_CHECKING:""",
"""if TYPE_CHECKING:
    from app.models.booking import Booking""")
# Add type checking to booking_passenger if not present
with open("app/models/booking_passenger.py") as f:
    s = f.read()
    if "if TYPE_CHECKING:" not in s:
        s = s.replace("from app.models.base import AuditMixin, db", "from typing import TYPE_CHECKING\nfrom app.models.base import AuditMixin, db\n\nif TYPE_CHECKING:\n    from app.models.booking import Booking")
        with open("app/models/booking_passenger.py", "w") as fw: fw.write(s)

# 7. notification_template.py, notification_delivery.py, notification.py
with open("app/models/notification_template.py") as f:
    s = f.read()
    if "if TYPE_CHECKING:" not in s:
        s = s.replace("from app.models.base import AuditMixin, db", "from typing import TYPE_CHECKING\nfrom app.models.base import AuditMixin, db\n\nif TYPE_CHECKING:\n    from app.models.notification import Notification")
        with open("app/models/notification_template.py", "w") as fw: fw.write(s)

with open("app/models/notification_delivery.py") as f:
    s = f.read()
    if "if TYPE_CHECKING:" not in s:
        s = s.replace("from app.models.base import AuditMixin, db", "from typing import TYPE_CHECKING\nfrom app.models.base import AuditMixin, db\n\nif TYPE_CHECKING:\n    from app.models.notification import Notification")
        with open("app/models/notification_delivery.py", "w") as fw: fw.write(s)

inplace_change("app/models/notification.py",
"""from typing import TYPE_CHECKING""",
"""from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.notification_template import NotificationTemplate
    from app.models.notification_delivery import NotificationDelivery""")

# 8. client_preference.py, corporate.py, client.py
with open("app/models/client_preference.py") as f:
    s = f.read()
    if "if TYPE_CHECKING:" not in s:
        s = s.replace("from app.models.base import AuditMixin, db", "from typing import TYPE_CHECKING\nfrom app.models.base import AuditMixin, db\n\nif TYPE_CHECKING:\n    from app.models.client import Client")
        with open("app/models/client_preference.py", "w") as fw: fw.write(s)

with open("app/models/corporate.py") as f:
    s = f.read()
    if "if TYPE_CHECKING:" not in s:
        s = s.replace("from app.models.base import AuditMixin, db", "from typing import TYPE_CHECKING\nfrom app.models.base import AuditMixin, db\n\nif TYPE_CHECKING:\n    from app.models.client import Client")
        with open("app/models/corporate.py", "w") as fw: fw.write(s)

inplace_change("app/models/client.py",
"""if TYPE_CHECKING:""",
"""if TYPE_CHECKING:
    from app.models.corporate import CorporateAccount""")


# 9. conftest.py
inplace_change("tests/conftest.py",
"""def app() -> Flask:""",
"""from typing import Generator\n\n@pytest.fixture(scope="session")\ndef app() -> Generator[Flask, None, None]:""")

print("Phase 2 complete")
