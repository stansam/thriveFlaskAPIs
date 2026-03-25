from enum import Enum

class AssetType(str, Enum):
    IMAGE_JPEG   = "image/jpeg"
    IMAGE_PNG    = "image/png"
    IMAGE_WEBP   = "image/webp"
    IMAGE_GIF    = "image/gif"
    DOCUMENT_PDF = "application/pdf"
    RECEIPT      = "receipt"       # payment proof; any image/pdf
    AVATAR       = "avatar"        # profile photo


class AssetOwnerType(str, Enum):
    """
    Discriminator for the polymorphic owner reference.
    One value per model that can own an asset directly.
    """
    TRAVEL_PACKAGE        = "travel_package"
    PACKAGE_ITINERARY_DAY = "package_itinerary_day"
    USER                  = "user"
    CLIENT                = "client"
    PAYMENT               = "payment"       # payment proof uploads


class StorageBackend(str, Enum):
    """
    Where the file is physically stored.
    Extend when switching CDN providers without touching application code.
    """
    LOCAL    = "local"       # local filesystem (dev / test only)
    S3       = "s3"          # AWS S3 / compatible (Backblaze, MinIO)
    GCS      = "gcs"         # Google Cloud Storage
    CLOUDFLARE = "cloudflare" # Cloudflare R2 / Images
