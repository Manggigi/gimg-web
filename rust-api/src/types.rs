use serde::Serialize;
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("Invalid image format")]
    InvalidImageFormat,
    
    #[error("File too large (max 20MB)")]
    FileTooLarge,
    
    #[error("Unsupported image format")]
    UnsupportedImageFormat,
    
    #[error("Missing required field: {0}")]
    MissingField(String),
    
    #[error("Invalid field value: {0}")]
    InvalidFieldValue(String),
    
    #[error("Image processing error: {0}")]
    ImageProcessingError(String),
    
    #[error("IO error: {0}")]
    IoError(String),
    
    #[error("Not implemented")]
    NotImplemented,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            AppError::InvalidImageFormat | AppError::UnsupportedImageFormat => {
                (StatusCode::UNSUPPORTED_MEDIA_TYPE, self.to_string())
            }
            AppError::FileTooLarge => (StatusCode::PAYLOAD_TOO_LARGE, self.to_string()),
            AppError::MissingField(_) | AppError::InvalidFieldValue(_) => {
                (StatusCode::BAD_REQUEST, self.to_string())
            }
            AppError::ImageProcessingError(_) | AppError::IoError(_) => {
                (StatusCode::INTERNAL_SERVER_ERROR, self.to_string())
            }
            AppError::NotImplemented => (StatusCode::NOT_IMPLEMENTED, self.to_string()),
        };

        (status, Json(serde_json::json!({ "error": message }))).into_response()
    }
}

#[derive(Debug, Serialize)]
pub struct ImageInfo {
    pub file: String,
    pub format: String,
    pub dimensions: String,
    pub width: u32,
    pub height: u32,
    pub mode: String,
    pub file_size: u64,
    pub file_size_human: String,
}

#[derive(Debug, Serialize)]
pub struct MetadataInfo {
    pub exif: serde_json::Value,
}

// Supported image formats
#[derive(Debug, Clone, Copy)]
pub enum ImageFormat {
    Jpeg,
    Png,
    Webp,
    Bmp,
    Tiff,
    Gif,
}

impl ImageFormat {
    pub fn from_magic_bytes(bytes: &[u8]) -> Option<Self> {
        if bytes.len() < 4 {
            return None;
        }

        match bytes {
            [0xFF, 0xD8, 0xFF, ..] => Some(ImageFormat::Jpeg),
            [0x89, 0x50, 0x4E, 0x47, ..] => Some(ImageFormat::Png),
            [0x52, 0x49, 0x46, 0x46, ..] if bytes.len() >= 12 && &bytes[8..12] == b"WEBP" => Some(ImageFormat::Webp),
            [0x42, 0x4D, ..] => Some(ImageFormat::Bmp),
            [0x49, 0x49, ..] | [0x4D, 0x4D, ..] => Some(ImageFormat::Tiff),
            [0x47, 0x49, 0x46, 0x38, ..] => Some(ImageFormat::Gif),
            _ => None,
        }
    }

    pub fn extension(&self) -> &'static str {
        match self {
            ImageFormat::Jpeg => "jpg",
            ImageFormat::Png => "png",
            ImageFormat::Webp => "webp",
            ImageFormat::Bmp => "bmp",
            ImageFormat::Tiff => "tiff",
            ImageFormat::Gif => "gif",
        }
    }

    pub fn mime_type(&self) -> &'static str {
        match self {
            ImageFormat::Jpeg => "image/jpeg",
            ImageFormat::Png => "image/png",
            ImageFormat::Webp => "image/webp",
            ImageFormat::Bmp => "image/bmp",
            ImageFormat::Tiff => "image/tiff",
            ImageFormat::Gif => "image/gif",
        }
    }
}

impl std::str::FromStr for ImageFormat {
    type Err = AppError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "jpg" | "jpeg" => Ok(ImageFormat::Jpeg),
            "png" => Ok(ImageFormat::Png),
            "webp" => Ok(ImageFormat::Webp),
            "bmp" => Ok(ImageFormat::Bmp),
            "tiff" | "tif" => Ok(ImageFormat::Tiff),
            "gif" => Ok(ImageFormat::Gif),
            _ => Err(AppError::UnsupportedImageFormat),
        }
    }
}

pub fn format_file_size(size: u64) -> String {
    const UNITS: &[&str] = &["B", "KB", "MB", "GB"];
    let mut size = size as f64;
    let mut unit_index = 0;

    while size >= 1024.0 && unit_index < UNITS.len() - 1 {
        size /= 1024.0;
        unit_index += 1;
    }

    if unit_index == 0 {
        format!("{} {}", size as u64, UNITS[unit_index])
    } else {
        format!("{:.1} {}", size, UNITS[unit_index])
    }
}