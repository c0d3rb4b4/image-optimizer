"""Image operations for resize and composite."""
import logging
import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

from .config import get_settings

# Set up logging
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
    output_dir: Optional[str] = None,
    filename: Optional[str] = None,
    format: str = "JPEG",
    quality: int = 95,
) -> str:
    """
    Save processed image to the output directory.

    Args:
        image: PIL Image to save
        output_dir: Directory to save to (default: from settings)
        filename: Output filename (default: generated UUID)
        format: Image format (default: JPEG)
        quality: JPEG quality (default: 95)

    Returns:
        Full path to the saved image
    """
    settings = get_settings()
    
    logger.info("=== save_image called ===")
    logger.info(f"settings.output_path from config: {settings.output_path}")
    logger.info(f"output_dir parameter: {output_dir}")
    logger.info(f"filename parameter: {filename}")

    if output_dir is None:
        output_dir = settings.output_path
        logger.info(f"output_dir was None, using settings.output_path: {output_dir}")

    if filename is None:
        ext = "jpg" if format.upper() == "JPEG" else format.lower()
        filename = f"{uuid.uuid4()}.{ext}"
        logger.info(f"filename was None, generated: {filename}")

    # Ensure output directory exists
    logger.info(f"Creating directory if not exists: {output_dir}")
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory exists/created: {Path(output_dir).exists()}")
    except Exception as e:
        logger.error(f"Failed to create directory {output_dir}: {e}")
        raise

    # Build full path
    output_path = os.path.join(output_dir, filename)
    logger.info(f"Full output path: {output_path}")

    # Save image
    save_kwargs = {}
    if format.upper() == "JPEG":
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True

    logger.info(f"Saving image to: {output_path}")
    try:
        image.save(output_path, format=format, **save_kwargs)
        logger.info(f"Image saved successfully")
        
        # Verify file exists after save
        file_exists = os.path.exists(output_path)
        logger.info(f"File exists after save: {file_exists}")
        if file_exists:
            file_size = os.path.getsize(output_path)
            logger.info(f"File size: {file_size} bytes")
        
        # List directory contents
        logger.info(f"Directory contents of {output_dir}:")
        try:
            for item in os.listdir(output_dir):
                logger.info(f"  - {item}")
        except Exception as e:
            logger.error(f"Failed to list directory: {e}")
            
    except Exception as e:
        logger.error(f"Failed to save image to {output_path}: {e}")
        raise

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
    )

    # Save to samba mount
    output_path = save_image(processed, filename=filename)

    return output_path, processed.width, processed.height
