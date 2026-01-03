"""Internal constants for image-optimizer service."""

# Application metadata
APP_NAME = "image-optimizer"
APP_VERSION = "1.0.0"

# Internal container paths (not configurable)
OUTPUT_PATH = "/data/images"

# Image processing defaults
DEFAULT_TARGET_WIDTH = 2560
DEFAULT_TARGET_HEIGHT = 1440
DEFAULT_JPEG_QUALITY = 95
DEFAULT_BACKGROUND_COLOR = (0, 0, 0)

# File validation
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}
