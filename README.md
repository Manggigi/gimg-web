# GIMG Web 🖼️

A free, open-source web-based image processing toolkit. Local [iLoveIMG](https://www.iloveimg.com/) alternative — no uploads to third-party servers.

## 🛠️ 14 Tools

| Category | Tools |
|----------|-------|
| **Optimize** | Compress, Upscale, Remove Background |
| **Modify** | Resize, Crop, Rotate |
| **Create** | Meme Generator, Photo Editor |
| **Convert** | Format Converter (JPG/PNG/WebP/BMP/TIFF) |
| **Analyze** | Image Info, EXIF Metadata Viewer/Stripper |
| **Security** | Watermark, Face Blur |

## 🚀 Quick Start

### Backend (FastAPI)

```bash
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8787
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8787 npm run dev
```

## 🏗️ Architecture

- **Backend**: FastAPI + Pillow + OpenCV (headless) + rembg
- **Frontend**: React 19 + Vite 7 + react-router-dom
- **Rate Limiting**: 30 requests/minute per IP
- **Max Upload**: 20MB per file
- **Security**: Magic bytes validation, file size limits, CORS

## 📦 Deploy

### Railway (Backend)
Procfile and runtime.txt included. Set `PORT` env var (Railway does this automatically).

### Vercel (Frontend)
Set `VITE_API_URL` to your Railway backend URL.

```bash
cd frontend
VITE_API_URL=https://your-railway-app.up.railway.app npx vercel --prod
```

## 📄 License

MIT
