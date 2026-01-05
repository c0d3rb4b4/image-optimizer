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
        logger.warning("Invalid file content type: filename=%s, content_type=%s, allowed=%s", 
                      file.filename, file.content_type, ALLOWED_CONTENT_TYPES)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )
    
    # Check file extension
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext and ext not in ALLOWED_EXTENSIONS:
            logger.warning("Invalid file extension: filename=%s, extension=%s, allowed=%s", 
                          file.filename, ext, ALLOWED_EXTENSIONS)
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
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE_BYTES:
        logger.warning("File too large: filename=%s, size=%d bytes (%.1f MB), max=%d bytes (%.1f MB)", 
                      file.filename, file_size, file_size / 1024 / 1024, 
                      MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_BYTES / 1024 / 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size} bytes. Maximum: {MAX_FILE_SIZE_BYTES} bytes ({MAX_FILE_SIZE_BYTES // 1024 // 1024}MB)",
        )
    logger.debug("File size validated: filename=%s, size=%d bytes (%.1f KB)", 
                file.filename, file_size, file_size / 1024)
    return contents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("%s v%s starting", APP_NAME, APP_VERSION)
    logger.info("Output path: %s", OUTPUT_PATH)
    logger.info("Output path exists: %s", os.path.exists(OUTPUT_PATH))
    logger.info("Target dimensions: %dx%d", settings.target_width, settings.target_height)
    logger.info("JPEG quality: %d", settings.jpeg_quality)
    logger.info("Max file size: %d bytes (%.1f MB)", MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_BYTES / 1024 / 1024)
    logger.info("Allowed content types: %s", ALLOWED_CONTENT_TYPES)
    logger.info("Allowed extensions: %s", ALLOWED_EXTENSIONS)
    
    if not os.path.exists(OUTPUT_PATH):
        logger.warning("Output path does not exist: %s - will be created on first write", OUTPUT_PATH)
    
    yield
    
    # Shutdown
    logger.info("%s v%s shutting down", APP_NAME, APP_VERSION)


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
    logger.debug("Received optimization request: filename=%s, content_type=%s, custom_filename=%s", 
                file.filename, file.content_type, filename or 'auto-generated')
    
    # Validate file
    validate_file(file)
    image_data = await validate_file_size(file)

    # Determine output filename
    output_filename = filename
    if output_filename is None and file.filename:
        base_name = os.path.splitext(file.filename)[0]
        output_filename = f"{base_name}_optimized.jpg"

    try:
        logger.debug("Processing image: filename=%s, size=%d bytes (%.1f KB), output=%s", 
                    file.filename, len(image_data), len(image_data) / 1024, output_filename)
        path, width, height = process_image(image_data, filename=output_filename)
        logger.info("Image processed successfully: input=%s, output=%s, dimensions=%dx%d, input_size=%d bytes", 
                   file.filename, path, width, height, len(image_data))
        return ImageProcessResponse(path=path, width=width, height=height)
    except Exception as e:
        logger.error("Failed to process image: filename=%s, size=%d bytes, error=%s", 
                    file.filename, len(image_data), str(e), exc_info=True)
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
    logger.info("Batch optimization request: %d files", len(files))
    results = []
    errors = []

    for idx, file in enumerate(files, 1):
        try:
            logger.debug("Processing batch file %d/%d: filename=%s, content_type=%s", 
                        idx, len(files), file.filename, file.content_type)
            
            # Validate file
            validate_file(file)
            image_data = await validate_file_size(file)

            # Determine output filename
            output_filename = None
            if file.filename:
                base_name = os.path.splitext(file.filename)[0]
                output_filename = f"{base_name}_optimized.jpg"

            path, width, height = process_image(image_data, filename=output_filename)
            logger.info("Batch file %d/%d processed: input=%s, output=%s, dimensions=%dx%d", 
                       idx, len(files), file.filename, path, width, height)
            results.append(ImageProcessResponse(path=path, width=width, height=height))

        except HTTPException as e:
            logger.warning("Batch file %d/%d validation failed: filename=%s, error=%s", 
                          idx, len(files), file.filename or "unknown", e.detail)
            errors.append(
                ImageProcessError(filename=file.filename or "unknown", error=e.detail)
            )
        except Exception as e:
            logger.error("Batch file %d/%d processing failed: filename=%s, error=%s", 
                        idx, len(files), file.filename or "unknown", str(e), exc_info=True)
            errors.append(
                ImageProcessError(filename=file.filename or "unknown", error=str(e))
            )

    logger.info("Batch processing complete: total=%d, successful=%d, failed=%d", 
               len(files), len(results), len(errors))
    
    return BatchProcessResponse(
        images=results,
        errors=errors,
        total_processed=len(results),
        total_failed=len(errors),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
