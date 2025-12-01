"""FastAPI application for image-optimizer service."""
import os
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile

from .config import get_settings
from .models import BatchProcessResponse, HealthResponse, ImageProcessResponse
from .ops import process_image

app = FastAPI(
    title="Image Optimizer",
    description="HTTP API that resizes/composites images to 2560x1440 and saves to Samba share",
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/optimize", response_model=ImageProcessResponse)
async def optimize_image(
    file: UploadFile = File(..., description="Image file to optimize"),
    filename: str = None,
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
    and returns the paths to all processed images.
    """
    results = []

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
            raise HTTPException(
                status_code=500,
                detail=f"Image processing failed for {file.filename}: {str(e)}",
            )

    return BatchProcessResponse(images=results, total_processed=len(results))


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
