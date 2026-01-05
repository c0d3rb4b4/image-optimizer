# image-optimizer Bruno API Collection

This directory contains [Bruno](https://www.usebruno.com/) API collection files for testing the image-optimizer service.

## Installation

1. Download Bruno from [usebruno.com](https://www.usebruno.com/)
2. Install and launch Bruno
3. Click "Open Collection"
4. Navigate to this directory (`image-optimizer/bruno`)

## Environment

The environment file is configured for local development:
- **Base URL**: `http://localhost:8004`

For production testing, update the environment to use `http://192.168.68.84:8004`.

## Available Requests

### Health Check
- **GET health** - Service health check (`/health`)

### Image Optimization
- **POST optimize** - Optimize a single image (`/optimize`)
- **POST optimize batch** - Optimize multiple images in batch (`/optimize/batch`)

## Request Examples

### Optimize Single Image (URL)
```json
{
  "image_url": "https://example.com/image.jpg",
  "target_width": 800,
  "target_height": 600,
  "quality": 85,
  "output_filename": "optimized_image"
}
```

### Optimize Single Image (Base64)
```json
{
  "image_base64": "<base64-encoded-image-data>",
  "target_width": 800,
  "quality": 85
}
```

### Optimize Batch
```json
{
  "images": [
    {
      "image_url": "https://example.com/image1.jpg",
      "target_width": 800
    },
    {
      "image_url": "https://example.com/image2.jpg",
      "target_width": 800
    }
  ]
}
```

## Response Format

### Single Optimization Success
```json
{
  "success": true,
  "message": "Image optimized successfully",
  "output_path": "/data/images/optimized_image.jpg",
  "filename": "optimized_image.jpg",
  "original_size": 1024000,
  "optimized_size": 512000,
  "compression_ratio": 0.5
}
```

### Batch Optimization Success
```json
{
  "success": true,
  "processed": 2,
  "failed": 0,
  "results": [
    {
      "success": true,
      "filename": "image1.jpg",
      "output_path": "/data/images/image1.jpg"
    },
    {
      "success": true,
      "filename": "image2.jpg",
      "output_path": "/data/images/image2.jpg"
    }
  ]
}
```

## See Also

- [image-optimizer README](../README.md)
- [Deployment Guide](../../mediawall-documents/installation/image-optimizer-deployment.md)
