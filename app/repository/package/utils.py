from slugify import slugify

def generate_package_slug(title: str) -> str:
    """Cleanly slugifies raw titles strictly lower-cased."""
    return slugify(title, separator='-').lower()
