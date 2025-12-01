"""Pydantic models for image-optimizer API."""
from typing import List, Optional

from pydantic import BaseModel, Field


class ImageProcessRequest(BaseModel):
    """Request model for image processing."""

    filename: Optional[str] = Field(
        default=None,
        description="Optional output filename. If not provided, a UUID will be generated.",
    )


class ImageProcessResponse(BaseModel):
    """Response model for processed image."""

    path: str = Field(description="Path to the processed image on the samba share")
    width: int = Field(description="Width of the processed image")
    height: int = Field(description="Height of the processed image")


class BatchProcessResponse(BaseModel):
    """Response model for batch image processing."""

    images: List[ImageProcessResponse] = Field(
        description="List of processed image results"
    )
    total_processed: int = Field(description="Total number of images processed")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(description="Health status of the service")
    version: str = Field(description="API version")
