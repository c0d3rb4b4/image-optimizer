"""Image operations for resize and composite."""
import logging
import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

from .config import get_settings
from .constants import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_JPEG_QUALITY,
    OUTPUT_PATH,
)

logger = logging.getLogger(__name__)


def resize_and_composite(
    image: Image.Image,
    target_width: int = 2560,
    target_height: int = 1440,
    background_color: tuple = (0, 0, 0),
) -> Image.Image:
    """
    Resize and composite an image to fit within target dimensions.

    The image is resized to fit within the target dimensions while maintaining
    aspect ratio, then centered on a background of the specified color.

    Args:
        image: PIL Image to process
        target_width: Target width in pixels (default: 2560)
        target_height: Target height in pixels (default: 1440)
        background_color: RGB tuple for background color (default: black)

    Returns:
        Processed PIL Image with exact target dimensions
    """
    # Calculate aspect ratios
    img_ratio = image.width / image.height
    target_ratio = target_width / target_height

    # Determine new dimensions maintaining aspect ratio
    if img_ratio > target_ratio:
        # Image is wider than target ratio
        new_width = target_width
        new_height = int(target_width / img_ratio)
    else:
        # Image is taller than target ratio
        new_height = target_height
        new_width = int(target_height * img_ratio)

    # Resize image
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create background canvas
    canvas = Image.new("RGB", (target_width, target_height), background_color)

    # Calculate position to center the image
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2

    # Handle images with transparency
    if resized.mode == "RGBA":
        canvas.paste(resized, (x_offset, y_offset), resized)
    else:
        # Convert to RGB if necessary
        if resized.mode != "RGB":
            resized = resized.convert("RGB")
        canvas.paste(resized, (x_offset, y_offset))

    return canvas


def save_image(
    image: Image.Image,
    filename: Optional[str] = None,
    quality: Optional[int] = None,
) -> str:
    """
    Save processed image to the output directory.

    Args:
        image: PIL Image to save
        filename: Output filename (default: generated UUID)
        quality: JPEG quality (default: from settings or DEFAULT_JPEG_QUALITY)

    Returns:
        Full path to the saved image
    """
    settings = get_settings()
    
    if quality is None:
        quality = settings.jpeg_quality

    if filename is None:
        filename = f"{uuid.uuid4()}.jpg"

    # Ensure output directory exists
    Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

    # Build full path
    output_path = os.path.join(OUTPUT_PATH, filename)

    # Save image
    image.save(output_path, format="JPEG", quality=quality, optimize=True)

    return output_path


def process_image(
    image_data: bytes,
    filename: Optional[str] = None,
) -> tuple[str, int, int]:
    """
    Process an image: resize, composite, and save.

    Args:
        image_data: Raw image bytes
        filename: Optional output filename

    Returns:
        Tuple of (output_path, width, height)
    """
    settings = get_settings()

    # Open image from bytes
    image = Image.open(BytesIO(image_data))

    # Resize and composite
    processed = resize_and_composite(
        image,
        target_width=settings.target_width,
        target_height=settings.target_height,
        background_color=DEFAULT_BACKGROUND_COLOR,
    )

    # Save to storage mount
    output_path = save_image(processed, filename=filename)

    return output_path, processed.width, processed.height
