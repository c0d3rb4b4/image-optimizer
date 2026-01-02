"""FastAPI application for image-optimizer service."""
import logging
import os
import sys
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile

from .config import get_settings
from .models import (
    BatchProcessResponse,
    HealthResponse,
    ImageProcessError,
    ImageProcessResponse,
)
from .ops import process_image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image Optimizer",
    description="HTTP API that resizes/composites images to 2560x1440 and saves to Samba share",
    version="1.0.0",
)

# Log settings on startup
@app.on_event("startup")
async def startup_event():
    logger.info("=== Image Optimizer Starting ===")
    settings = get_settings()
    logger.info(f"Output path configured: {settings.output_path}")
    logger.info(f"Checking if output path exists: {os.path.exists(settings.output_path)}")
    logger.info(f"Checking if output path is writable: {os.access(settings.output_path, os.W_OK) if os.path.exists(settings.output_path) else 'N/A - path does not exist'}")
    
    # List mount points
    logger.info("=== Mount points ===")
    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                if '/data' in line or '/mnt' in line:
                    logger.info(line.strip())
    except Exception as e:
        logger.info(f"Could not read mounts: {e}")


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/optimize", response_model=ImageProcessResponse)
async def optimize_image(
    file: UploadFile = File(..., description="Image file to optimize"),
    filename: Optional[str] = None,
) -> ImageProcessResponse:
    """
    Optimize a single image.

    Resizes and composites the image to 2560x1440, saves to Samba share,
    and returns the path to the processed image.
    """
    try:
        # Read uploaded file
        image_data = await file.read()

        # Determine output filename
        output_filename = filename
        if output_filename is None and file.filename:
            # Use original filename with modified extension
            base_name = os.path.splitext(file.filename)[0]
            output_filename = f"{base_name}_optimized.jpg"

        # Process the image
        path, width, height = process_image(image_data, filename=output_filename)

        return ImageProcessResponse(path=path, width=width, height=height)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")


@app.post("/optimize/batch", response_model=BatchProcessResponse)
async def optimize_images_batch(
    files: List[UploadFile] = File(..., description="Image files to optimize"),
) -> BatchProcessResponse:
    """
    Optimize multiple images in batch.

    Resizes and composites each image to 2560x1440, saves to Samba share,
    and returns the paths to all processed images. Continues processing
    remaining files if one fails.
    """
    results = []
    errors = []

    for file in files:
        try:
            # Read uploaded file
            image_data = await file.read()

            # Determine output filename
            output_filename = None
            if file.filename:
                base_name = os.path.splitext(file.filename)[0]
                output_filename = f"{base_name}_optimized.jpg"

            # Process the image
            path, width, height = process_image(image_data, filename=output_filename)

            results.append(ImageProcessResponse(path=path, width=width, height=height))

        except Exception as e:
            errors.append(
                ImageProcessError(
                    filename=file.filename or "unknown",
                    error=str(e),
                )
            )

    return BatchProcessResponse(
        images=results,
        errors=errors,
        total_processed=len(results),
        total_failed=len(errors),
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
