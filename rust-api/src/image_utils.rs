use crate::types::{AppError, ImageFormat, ImageInfo, format_file_size};
use image::{DynamicImage, ImageFormat as ImageFormatEnum, GenericImageView};
use std::fs;
use uuid::Uuid;

pub fn load_image_from_bytes(data: &[u8]) -> Result<DynamicImage, AppError> {
    image::load_from_memory(data)
        .map_err(|e| AppError::ImageProcessingError(format!("Failed to load image: {}", e)))
}

pub fn create_temp_file(extension: &str) -> String {
    let filename = format!("{}.{}", Uuid::new_v4(), extension);
    format!("/tmp/{}", filename)
}

pub fn save_image(img: &DynamicImage, path: &str, format: ImageFormat) -> Result<(), AppError> {
    let image_format = match format {
        ImageFormat::Jpeg => ImageFormatEnum::Jpeg,
        ImageFormat::Png => ImageFormatEnum::Png,
        ImageFormat::Webp => ImageFormatEnum::WebP,
        ImageFormat::Bmp => ImageFormatEnum::Bmp,
        ImageFormat::Tiff => ImageFormatEnum::Tiff,
        ImageFormat::Gif => ImageFormatEnum::Gif,
    };

    img.save_with_format(path, image_format)
        .map_err(|e| AppError::ImageProcessingError(format!("Failed to save image: {}", e)))
}

pub fn get_image_info(img: &DynamicImage, original_path: &str, original_size: usize) -> ImageInfo {
    let (width, height) = img.dimensions();
    let color_type = img.color();
    
    let format = match img {
        DynamicImage::ImageRgb8(_) => "RGB",
        DynamicImage::ImageRgba8(_) => "RGBA", 
        DynamicImage::ImageLuma8(_) => "L",
        DynamicImage::ImageLumaA8(_) => "LA",
        _ => "Unknown",
    };

    let detected_format = if original_path.ends_with(".jpg") || original_path.ends_with(".jpeg") {
        "JPEG"
    } else if original_path.ends_with(".png") {
        "PNG"
    } else if original_path.ends_with(".webp") {
        "WEBP"
    } else if original_path.ends_with(".bmp") {
        "BMP"
    } else if original_path.ends_with(".tiff") || original_path.ends_with(".tif") {
        "TIFF"
    } else if original_path.ends_with(".gif") {
        "GIF"
    } else {
        "Unknown"
    };

    ImageInfo {
        file: original_path.split('/').last().unwrap_or("unknown").to_string(),
        format: detected_format.to_string(),
        dimensions: format!("{}x{}", width, height),
        width,
        height,
        mode: format.to_string(),
        file_size: original_size as u64,
        file_size_human: format_file_size(original_size as u64),
    }
}

pub fn read_file_bytes(path: &str) -> Result<Vec<u8>, AppError> {
    fs::read(path).map_err(|e| AppError::IoError(format!("Failed to read file: {}", e)))
}

pub fn delete_temp_file(path: &str) {
    let _ = fs::remove_file(path);
}

// Resize using the standard image crate for now (TODO: optimize with fast_image_resize)
pub fn resize_image_fast(
    img: &DynamicImage,
    new_width: u32,
    new_height: u32,
) -> Result<DynamicImage, AppError> {
    // Use the standard image crate resize with Lanczos3 filtering
    Ok(img.resize(new_width, new_height, image::imageops::FilterType::Lanczos3))
}

// Color parsing utility
pub fn parse_color(color_str: &str) -> Result<image::Rgba<u8>, AppError> {
    match color_str.to_lowercase().as_str() {
        "white" => Ok(image::Rgba([255, 255, 255, 255])),
        "black" => Ok(image::Rgba([0, 0, 0, 255])),
        "red" => Ok(image::Rgba([255, 0, 0, 255])),
        "green" => Ok(image::Rgba([0, 255, 0, 255])),
        "blue" => Ok(image::Rgba([0, 0, 255, 255])),
        "yellow" => Ok(image::Rgba([255, 255, 0, 255])),
        "cyan" => Ok(image::Rgba([0, 255, 255, 255])),
        "magenta" => Ok(image::Rgba([255, 0, 255, 255])),
        _ => {
            // Try to parse as hex color
            if color_str.starts_with('#') && color_str.len() == 7 {
                let hex = &color_str[1..];
                let r = u8::from_str_radix(&hex[0..2], 16)
                    .map_err(|_| AppError::InvalidFieldValue(format!("Invalid color: {}", color_str)))?;
                let g = u8::from_str_radix(&hex[2..4], 16)
                    .map_err(|_| AppError::InvalidFieldValue(format!("Invalid color: {}", color_str)))?;
                let b = u8::from_str_radix(&hex[4..6], 16)
                    .map_err(|_| AppError::InvalidFieldValue(format!("Invalid color: {}", color_str)))?;
                Ok(image::Rgba([r, g, b, 255]))
            } else {
                Err(AppError::InvalidFieldValue(format!("Unsupported color: {}", color_str)))
            }
        }
    }
}