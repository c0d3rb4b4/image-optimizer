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
    logger.debug("Resizing image: input=%dx%d (mode=%s), target=%dx%d, background=%s", 
                image.width, image.height, image.mode, target_width, target_height, background_color)
    
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

    logger.debug("Calculated resize dimensions: %dx%d -> %dx%d (ratio=%.2f)", 
                image.width, image.height, new_width, new_height, img_ratio)
    
    # Resize image
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create background canvas
    canvas = Image.new("RGB", (target_width, target_height), background_color)

    # Calculate position to center the image
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2

    logger.debug("Compositing image: position=(%d, %d), has_alpha=%s", 
                x_offset, y_offset, resized.mode == "RGBA")
    
    # Handle images with transparency
    if resized.mode == "RGBA":
        canvas.paste(resized, (x_offset, y_offset), resized)
    else:
        # Convert to RGB if necessary
        if resized.mode != "RGB":
            logger.debug("Converting image mode: %s -> RGB", resized.mode)
            resized = resized.convert("RGB")
        canvas.paste(resized, (x_offset, y_offset))

    logger.debug("Image resize and composite complete: output=%dx%d", canvas.width, canvas.height)
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
        logger.debug("Generated filename: %s", filename)

    # Ensure output directory exists
    output_dir_created = not os.path.exists(OUTPUT_PATH)
    Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)
    if output_dir_created:
        logger.info("Created output directory: %s", OUTPUT_PATH)

    # Build full path
    output_path = os.path.join(OUTPUT_PATH, filename)

    logger.debug("Saving image: path=%s, dimensions=%dx%d, quality=%d, format=JPEG", 
                output_path, image.width, image.height, quality)
    
    # Save image
    image.save(output_path, format="JPEG", quality=quality, optimize=True)
    
    file_size = os.path.getsize(output_path)
    logger.debug("Image saved: path=%s, size=%d bytes (%.1f KB)", output_path, file_size, file_size / 1024)

    return output_path


def process_image(
    image_data: bytes,
    filename: Optional[str] = None,
) -> tuple[str, int, int]:
    """
    Process an image: resize, composite, and save.
    
    Automatically detects image orientation:
    - Landscape images: processed for full canvas (target_width x target_height)
    - Portrait images: processed for half canvas (target_width/2 x target_height)

    Args:
        image_data: Raw image bytes
        filename: Optional output filename

    Returns:
        Tuple of (output_path, width, height)
    """
    settings = get_settings()
    input_size = len(image_data)

    logger.debug("Processing image: input_size=%d bytes (%.1f KB), output_filename=%s", 
                input_size, input_size / 1024, filename or 'auto-generated')
    
    # Open image from bytes
    try:
        image = Image.open(BytesIO(image_data))
        logger.debug("Opened image: format=%s, mode=%s, size=%dx%d", 
                    image.format, image.mode, image.width, image.height)
    except Exception as e:
        logger.error("Failed to open image: input_size=%d bytes, error=%s", input_size, str(e))
        raise

    # Detect orientation and determine target dimensions
    is_portrait = image.height > image.width
    if is_portrait:
        # Portrait: use half the canvas width, same height
        target_width = settings.target_width // 2
        target_height = settings.target_height
        logger.debug("Detected portrait orientation: using half-canvas dimensions %dx%d", 
                    target_width, target_height)
    else:
        # Landscape: use full canvas dimensions
        target_width = settings.target_width
        target_height = settings.target_height
        logger.debug("Detected landscape orientation: using full-canvas dimensions %dx%d", 
                    target_width, target_height)

    # Resize and composite
    try:
        processed = resize_and_composite(
            image,
            target_width=target_width,
            target_height=target_height,
            background_color=DEFAULT_BACKGROUND_COLOR,
        )
    except Exception as e:
        logger.error("Failed to resize/composite image: input=%dx%d, target=%dx%d, error=%s", 
                    image.width, image.height, target_width, target_height, str(e))
        raise

    # Save to storage mount
    try:
        output_path = save_image(processed, filename=filename)
    except Exception as e:
        logger.error("Failed to save image: dimensions=%dx%d, filename=%s, error=%s", 
                    processed.width, processed.height, filename or 'auto', str(e))
        raise

    logger.info("Image processing complete: input_size=%d bytes, orientation=%s, output=%s, dimensions=%dx%d", 
               input_size, "portrait" if is_portrait else "landscape", output_path, processed.width, processed.height)
    
    return output_path, processed.width, processed.height
