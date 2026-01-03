# image-optimizer

Image optimization microservice: accepts one or more images, resizes/center-crops them into a 2560×1440 frame, and writes results to mounted storage.

## Features

- **Batch image processing** - Process single or multiple images in one request
- **Center-crop with resize** - Intelligent resizing and centering to target dimensions
- **Input validation** - File type and size validation (max 50MB, common image formats)
- **Health checks** - Built-in health monitoring
- FastAPI REST API
- Structured logging (compatible with Loki/Promtail)
- Docker containerized

## Configuration

Only tuneable settings are exposed as environment variables. Internal paths are hardcoded.

### Environment Variables

```bash
# Image processing settings
TARGET_WIDTH=2560
TARGET_HEIGHT=1440
JPEG_QUALITY=95

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/optimize` | POST | Optimize single image |
| `/optimize/batch` | POST | Optimize multiple images in batch |

### Supported File Types

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)
- BMP (.bmp)
- TIFF (.tiff, .tif)

Maximum file size: 50MB

### Request Examples

**Single image optimization:**
```bash
curl -F "file=@image.jpg" http://localhost:8004/optimize
```

**Batch optimization:**
```bash
curl -F "files=@image1.jpg" -F "files=@image2.png" http://localhost:8004/optimize/batch
```

### Response Format

```json
{
  "path": "/data/images/image_optimized.jpg",
  "width": 2560,
  "height": 1440
}
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn src.app:app --reload --port 8000
```

## Docker

```bash
# Build
docker build -t image-optimizer .

# Run with volume mount
docker run -p 8004:8000 \
  -v /path/to/storage:/data/images \
  image-optimizer
```

## Dependencies

- **FastAPI** - Web framework
- **Pillow** - Image processing
- **python-multipart** - Multipart form data handling
- **pydantic** - Data validation
- **pydantic-settings** - Environment configuration

## Service Port

The service runs on port **8004** in the mediawall cluster.
