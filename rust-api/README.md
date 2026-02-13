# GIMG Rust API

A high-performance Rust backend for GIMG Web - a web-based image processing toolkit.

## Features

- **14 Image Processing Tools**:
  - Compress - Reduce image quality/size
  - Resize - Scale images by dimensions or percentage
  - Crop - Cut images by coordinates or aspect ratio
  - Rotate - Rotate images by degrees or auto-orient
  - Convert - Change image formats (JPEG, PNG, WebP, BMP, TIFF)
  - Info - Get image metadata (dimensions, format, size)
  - Metadata - View or strip EXIF data
  - Watermark - Add text overlays
  - Blur Face - Blur faces or regions
  - Upscale - Enlarge images with quality enhancement
  - Meme - Add top/bottom text
  - Edit - Brightness, contrast, filters, effects
  - Remove Background - (Phase 2 - not implemented)
  - HTML to Image - (Not available in web mode)

## Tech Stack

- **axum** - High-performance async web framework
- **image** + **imageproc** - Image processing with SIMD optimization
- **tokio** - Async runtime
- **tower-http** - CORS, rate limiting, file serving
- **rayon** - Data parallelism

## API Contract

### GET Endpoints
- `GET /api/health` → `{"status":"ok"}`
- `GET /api/tools` → JSON array of 14 tool objects

### POST Endpoints (multipart/form-data with `file` field)
All endpoints return processed images or JSON responses.

## Security & Performance

- Magic bytes validation for image formats
- 20MB upload limit
- Rate limiting: 30 requests/minute per IP
- CORS: allows all origins
- SIMD-optimized image operations
- Zero-copy operations where possible

## Development

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build and run
cargo run

# Build for production
cargo build --release

# Docker build
docker build -t gimg-rust-api .
```

## Deployment

Ready for Railway deployment with included `Dockerfile`.

Environment variable:
- `PORT` - Server port (default: 8787)

The server binds to `0.0.0.0:$PORT` for containerized deployment.