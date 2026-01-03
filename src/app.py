"""FastAPI application for image-optimizer service."""
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile

from .config import get_settings
from .constants import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    APP_NAME,
    APP_VERSION,
    MAX_FILE_SIZE_BYTES,
    OUTPUT_PATH,
)
from .models import (
    BatchProcessResponse,
    HealthResponse,
    ImageProcessError,
    ImageProcessResponse,
)
from .ops import process_image

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size.
    
    Args:
        file: The uploaded file to validate
        
    Raises:
        HTTPException: If validation fails
    """
    # Check content type
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )
    
    # Check file extension
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file extension: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )


async def validate_file_size(file: UploadFile) -> bytes:
    """Read and validate file size.
    
    Args:
        file: The uploaded file to read
        
    Returns:
        The file contents as bytes
        
    Raises:
        HTTPException: If file is too large
    """
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(contents)} bytes. Maximum: {MAX_FILE_SIZE_BYTES} bytes ({MAX_FILE_SIZE_BYTES // 1024 // 1024}MB)",
        )
    return contents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info(f"{APP_NAME} v{APP_VERSION} starting")
    logger.info(f"Output path: {OUTPUT_PATH}")
    logger.info(f"Output path exists: {os.path.exists(OUTPUT_PATH)}")
    logger.info(f"Target dimensions: {settings.target_width}x{settings.target_height}")
    
    if not os.path.exists(OUTPUT_PATH):
        logger.warning(f"Output path {OUTPUT_PATH} does not exist - will be created on first write")
    
    yield
    
    # Shutdown
    logger.info(f"{APP_NAME} shutting down")


app = FastAPI(
    title="Image Optimizer",
    description="HTTP API that resizes/composites images to 2560x1440 and saves to storage",
    version=APP_VERSION,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version=APP_VERSION)


@app.post("/optimize", response_model=ImageProcessResponse)
async def optimize_image(
    file: UploadFile = File(..., description="Image file to optimize"),
    filename: Optional[str] = None,
) -> ImageProcessResponse:
    """
    Optimize a single image.

    Resizes and composites the image to target dimensions, saves to storage,
    and returns the path to the processed image.
    """
    # Validate file
    validate_file(file)
    image_data = await validate_file_size(file)

    # Determine output filename
    output_filename = filename
    if output_filename is None and file.filename:
        base_name = os.path.splitext(file.filename)[0]
        output_filename = f"{base_name}_optimized.jpg"

    try:
        path, width, height = process_image(image_data, filename=output_filename)
        logger.info(f"Processed image: {file.filename} -> {path}")
        return ImageProcessResponse(path=path, width=width, height=height)
    except Exception as e:
        logger.error(f"Failed to process image {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")


@app.post("/optimize/batch", response_model=BatchProcessResponse)
async def optimize_images_batch(
    files: List[UploadFile] = File(..., description="Image files to optimize"),
) -> BatchProcessResponse:
    """
    Optimize multiple images in batch.

    Resizes and composites each image to target dimensions, saves to storage,
    and returns the paths to all processed images. Continues processing
    remaining files if one fails.
    """
    results = []
    errors = []

    for file in files:
        try:
            # Validate file
            validate_file(file)
            image_data = await validate_file_size(file)

            # Determine output filename
            output_filename = None
            if file.filename:
                base_name = os.path.splitext(file.filename)[0]
                output_filename = f"{base_name}_optimized.jpg"

            path, width, height = process_image(image_data, filename=output_filename)
            logger.info(f"Processed image: {file.filename} -> {path}")
            results.append(ImageProcessResponse(path=path, width=width, height=height))

        except HTTPException as e:
            errors.append(
                ImageProcessError(filename=file.filename or "unknown", error=e.detail)
            )
        except Exception as e:
            logger.error(f"Failed to process image {file.filename}: {e}")
            errors.append(
                ImageProcessError(filename=file.filename or "unknown", error=str(e))
            )

    return BatchProcessResponse(
        images=results,
        errors=errors,
        total_processed=len(results),
        total_failed=len(errors),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
