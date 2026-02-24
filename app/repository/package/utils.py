from slugify import slugify

def build_package_search_filters(model_class, filters: dict) -> list:
    """
    Parses an untrusted dictionary of incoming search filters and maps them
    strictly to SQLAlchemy query binary expressions against the Package model.
    """
    conditions = []
    
    if filters.get('country'):
        # ILIKE equivalent for robust SQL cross-compatibility pattern matching
        conditions.append(model_class.country.ilike(f"%{filters['country']}%"))
        
    if filters.get('city'):
        conditions.append(model_class.city.ilike(f"%{filters['city']}%"))
        
    if filters.get('duration_min'):
        conditions.append(model_class.duration_days >= int(filters['duration_min']))
        
    if filters.get('duration_max'):
        conditions.append(model_class.duration_days <= int(filters['duration_max']))
        
    return conditions

def generate_package_slug(title: str) -> str:
    """Cleanly slugifies raw titles strictly lower-cased."""
    return slugify(title, separator='-').lower()
