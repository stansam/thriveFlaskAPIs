# app/api/v1/package/schemas/__init__.py
"""
Marshmallow validation schemas for Travel Packages.
"""
from marshmallow import Schema, fields, validate, RAISE
from app.enums import PackageStatus, InclusionType

class PackageListQuerySchema(Schema):
    status              = fields.Str(load_default=None, validate=validate.OneOf([e.value for e in PackageStatus]))
    destination_country = fields.Str(load_default=None, validate=validate.Length(max=100))
    region              = fields.Str(load_default=None, validate=validate.Length(max=100))
    is_featured         = fields.Bool(load_default=None)
    search              = fields.Str(load_default=None, validate=validate.Length(max=100))
    min_price           = fields.Decimal(load_default=None)
    max_price           = fields.Decimal(load_default=None)
    page                = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page            = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))

class PackageCreateSchema(Schema):
    class Meta:
        unknown = RAISE

    title                = fields.Str(required=True, validate=validate.Length(min=2, max=300))
    slug                 = fields.Str(load_default=None, validate=[validate.Length(max=320), validate.Regexp(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')])
    tagline              = fields.Str(load_default=None, validate=validate.Length(max=500))
    description          = fields.Str(load_default=None)
    destination_country  = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    destination_city     = fields.Str(load_default=None, validate=validate.Length(max=100))
    region               = fields.Str(load_default=None, validate=validate.Length(max=100))
    duration_days        = fields.Int(required=True, validate=validate.Range(min=1))
    duration_nights      = fields.Int(required=True, validate=validate.Range(min=0))
    base_price_usd       = fields.Decimal(required=True, validate=validate.Range(min=0.01))
    price_per            = fields.Str(load_default="person", validate=validate.Length(max=30))
    min_participants     = fields.Int(load_default=1, validate=validate.Range(min=1))
    max_participants     = fields.Int(load_default=None, validate=validate.Range(min=1))
    flights_includable   = fields.Bool(load_default=False)
    insurance_includable = fields.Bool(load_default=False)
    is_featured          = fields.Bool(load_default=False)
    
    highlights           = fields.List(fields.Dict(), load_default=[])
    inclusions           = fields.List(fields.Dict(), load_default=[])
    itinerary            = fields.List(fields.Dict(), load_default=[])
    price_tiers          = fields.List(fields.Dict(), load_default=[])

class PackageUpdateSchema(Schema):
    class Meta:
        unknown = RAISE

    title                = fields.Str(validate=validate.Length(min=2, max=300))
    slug                 = fields.Str(validate=[validate.Length(max=320), validate.Regexp(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')])
    tagline              = fields.Str(validate=validate.Length(max=500))
    description          = fields.Str()
    destination_country  = fields.Str(validate=validate.Length(min=2, max=100))
    destination_city     = fields.Str(validate=validate.Length(max=100))
    region               = fields.Str(validate=validate.Length(max=100))
    duration_days        = fields.Int(validate=validate.Range(min=1))
    duration_nights      = fields.Int(validate=validate.Range(min=0))
    base_price_usd       = fields.Decimal(validate=validate.Range(min=0.01))
    price_per            = fields.Str(validate=validate.Length(max=30))
    min_participants     = fields.Int(validate=validate.Range(min=1))
    max_participants     = fields.Int(validate=validate.Range(min=1))
    flights_includable   = fields.Bool()
    insurance_includable = fields.Bool()
    is_featured          = fields.Bool()

class HighlightCreateSchema(Schema):
    class Meta:
        unknown = RAISE

    text          = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    icon          = fields.Str(load_default=None, validate=validate.Length(max=50))
    display_order = fields.Int(load_default=0)

class HighlightUpdateSchema(Schema):
    class Meta:
        unknown = RAISE

    text          = fields.Str(validate=validate.Length(min=1, max=500))
    icon          = fields.Str(validate=validate.Length(max=50))
    display_order = fields.Int()

class HighlightReorderSchema(Schema):
    class Meta:
        unknown = RAISE

    ordered_ids = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))

class InclusionCreateSchema(Schema):
    class Meta:
        unknown = RAISE

    inclusion_type  = fields.Str(required=True, validate=validate.OneOf([e.value for e in InclusionType]))
    label           = fields.Str(required=True, validate=validate.Length(min=1, max=300))
    notes           = fields.Str(load_default=None, validate=validate.Length(max=500))
    extra_cost_usd  = fields.Decimal(load_default=None, validate=validate.Range(min=0))
    display_order   = fields.Int(load_default=0)

class InclusionUpdateSchema(Schema):
    class Meta:
        unknown = RAISE

    inclusion_type  = fields.Str(validate=validate.OneOf([e.value for e in InclusionType]))
    label           = fields.Str(validate=validate.Length(min=1, max=300))
    notes           = fields.Str(validate=validate.Length(max=500))
    extra_cost_usd  = fields.Decimal(validate=validate.Range(min=0))
    display_order   = fields.Int()

class ItineraryDayCreateSchema(Schema):
    class Meta:
        unknown = RAISE

    day_number     = fields.Int(required=True, validate=validate.Range(min=1))
    title          = fields.Str(required=True, validate=validate.Length(min=1, max=300))
    description    = fields.Str(load_default=None)
    activities     = fields.Str(load_default=None)
    meals_included = fields.Str(load_default=None, validate=validate.Length(max=100))
    accommodation  = fields.Str(load_default=None, validate=validate.Length(max=300))

class ItineraryDayUpdateSchema(Schema):
    class Meta:
        unknown = RAISE

    title          = fields.Str(validate=validate.Length(min=1, max=300))
    description    = fields.Str()
    activities     = fields.Str()
    meals_included = fields.Str(validate=validate.Length(max=100))
    accommodation  = fields.Str(validate=validate.Length(max=300))

class PriceTierCreateSchema(Schema):
    class Meta:
        unknown = RAISE

    label             = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    price_usd         = fields.Decimal(required=True, validate=validate.Range(min=0.01))
    price_per         = fields.Str(load_default="person", validate=validate.Length(max=30))
    min_participants  = fields.Int(load_default=1, validate=validate.Range(min=1))
    max_participants  = fields.Int(load_default=None, validate=validate.Range(min=1))
    is_add_on         = fields.Bool(load_default=False)
    is_active         = fields.Bool(load_default=True)

class PriceTierUpdateSchema(Schema):
    class Meta:
        unknown = RAISE

    label             = fields.Str(validate=validate.Length(min=1, max=100))
    price_usd         = fields.Decimal(validate=validate.Range(min=0.01))
    price_per         = fields.Str(validate=validate.Length(max=30))
    min_participants  = fields.Int(validate=validate.Range(min=1))
    max_participants  = fields.Int(validate=validate.Range(min=1))
    is_add_on         = fields.Bool()
    is_active         = fields.Bool()

class MediaAttachSchema(Schema):
    class Meta:
        unknown = RAISE

    asset_id         = fields.Str(required=True, validate=validate.Length(min=1))
    caption          = fields.Str(load_default=None, validate=validate.Length(max=500))
    itinerary_day_id = fields.Str(load_default=None)
    display_order    = fields.Int(load_default=0)
    is_cover         = fields.Bool(load_default=False)

class MediaSetCoverSchema(Schema):
    class Meta:
        unknown = RAISE

    asset_id = fields.Str(required=True)

class InsuranceCreateSchema(Schema):
    class Meta:
        unknown = RAISE

    provider_name    = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    policy_name      = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    coverage_details = fields.Str(load_default=None)
    premium_usd      = fields.Decimal(load_default=0.00, validate=validate.Range(min=0))
    per_person_rate  = fields.Decimal(load_default=0.00, validate=validate.Range(min=0))
    is_active        = fields.Bool(load_default=True)

class InsuranceUpdateSchema(Schema):
    class Meta:
        unknown = RAISE

    provider_name    = fields.Str(validate=validate.Length(min=1, max=150))
    policy_name      = fields.Str(validate=validate.Length(min=1, max=150))
    coverage_details = fields.Str()
    premium_usd      = fields.Decimal(validate=validate.Range(min=0))
    per_person_rate  = fields.Decimal(validate=validate.Range(min=0))
    is_active        = fields.Bool()
