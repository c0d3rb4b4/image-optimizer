# image-optimizer

Image optimization microservice: accepts one or more images, resizes/center-crops them into a 2560×1440 frame, and writes results to a Samba-backed storage path.

## Features

- **Batch image processing** - Process single or multiple images in one request
- **Center-crop with resize** - Intelligent resizing and centering to target dimensions
- **Samba storage backend** - Direct integration with network-attached storage
- **Health checks** - Built-in health monitoring
- FastAPI REST API
- Structured JSON logging (compatible with Loki/Promtail)
- Docker containerized

## Configuration

### Environment Variables

```bash
# Service settings
APP_NAME=image-optimizer
APP_VERSION=0.1.0
DEBUG=false

# Message queue
RABBITMQ_HOST=192.168.68.83
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/optimize` | POST | Optimize single image |
| `/optimize/batch` | POST | Optimize multiple images in batch |

### Request Examples

**Single image optimization:**
```json
POST /optimize
Content-Type: multipart/form-data

image: <binary image data>
```

**Batch optimization:**
```json
POST /optimize/batch
Content-Type: multipart/form-data

images: [<binary image data>, <binary image data>, ...]
```

### Response Format

```json
{
  "status": "success",
  "image_path": "/mnt/mediawall/mediawall/image-optimizer/images/optimized_image.jpg",
  "dimensions": [2560, 1440]
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

# Run
docker run -p 8004:8000 \
  -v /path/to/samba:/mnt/mediawall/mediawall/image-optimizer/images \
  image-optimizer
```

## Dependencies

- **FastAPI** - Web framework
- **Pillow** - Image processing
- **python-multipart** - Multipart form data handling
- **pydantic** - Data validation

## Service Port

The service runs on port **8004** in the mediawall cluster.
