use axum::{
    http::{header, HeaderMap, StatusCode},
    response::{IntoResponse, Response},
    Json,
};
use axum_extra::extract::Multipart;
use image::{DynamicImage, GenericImageView};
use serde_json::json;

use crate::{
    image_utils::*,
    types::*,
    validation::*,
};

// Font data for future text rendering implementation
// const FONT_DATA: &[u8] = include_bytes!("../assets/DejaVuSans.ttf");

pub async fn compress_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut quality = 80;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "quality" => {
                if let Ok(text) = field.text().await {
                    quality = text.parse().unwrap_or(80).clamp(1, 100);
                }
            }
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let img = load_image_from_bytes(&data)?;
    
    // For compression, we'll save as JPEG with the specified quality
    let temp_path = create_temp_file("jpg");
    
    // Convert to RGB if it has alpha channel
    let img = if img.color().has_alpha() {
        DynamicImage::ImageRgb8(img.to_rgb8())
    } else {
        img
    };

    // Save with quality (this is a simplified approach)
    save_image(&img, &temp_path, ImageFormat::Jpeg)?;
    
    let compressed_data = read_file_bytes(&temp_path)?;
    delete_temp_file(&temp_path);

    Ok((
        StatusCode::OK,
        [
            (header::CONTENT_TYPE, "image/jpeg"),
            (header::CONTENT_DISPOSITION, "attachment; filename=\"compressed.jpg\""),
        ],
        compressed_data,
    ))
}

pub async fn resize_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut width: Option<u32> = None;
    let mut height: Option<u32> = None;
    let mut percentage: Option<f32> = None;
    let mut max_size: Option<u32> = None;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "width" => {
                if let Ok(text) = field.text().await {
                    width = text.parse().ok();
                }
            }
            "height" => {
                if let Ok(text) = field.text().await {
                    height = text.parse().ok();
                }
            }
            "percentage" => {
                if let Ok(text) = field.text().await {
                    percentage = text.parse().ok();
                }
            }
            "max_size" => {
                if let Ok(text) = field.text().await {
                    max_size = text.parse().ok();
                }
            }
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let img = load_image_from_bytes(&data)?;
    let (orig_width, orig_height) = img.dimensions();

    let (new_width, new_height) = if let Some(pct) = percentage {
        ((orig_width as f32 * pct / 100.0) as u32, (orig_height as f32 * pct / 100.0) as u32)
    } else if let Some(max) = max_size {
        let scale = (max as f32) / (orig_width.max(orig_height) as f32);
        if scale < 1.0 {
            ((orig_width as f32 * scale) as u32, (orig_height as f32 * scale) as u32)
        } else {
            (orig_width, orig_height)
        }
    } else {
        let w = width.unwrap_or(orig_width);
        let h = height.unwrap_or(orig_height);
        
        // Maintain aspect ratio if only one dimension is specified
        if width.is_some() && height.is_none() {
            let ratio = orig_height as f32 / orig_width as f32;
            (w, (w as f32 * ratio) as u32)
        } else if height.is_some() && width.is_none() {
            let ratio = orig_width as f32 / orig_height as f32;
            ((h as f32 * ratio) as u32, h)
        } else {
            (w, h)
        }
    };

    let resized_img = resize_image_fast(&img, new_width, new_height)?;
    
    let temp_path = create_temp_file("png");
    save_image(&resized_img, &temp_path, ImageFormat::Png)?;
    
    let result_data = read_file_bytes(&temp_path)?;
    delete_temp_file(&temp_path);

    Ok((
        StatusCode::OK,
        [
            (header::CONTENT_TYPE, "image/png"),
            (header::CONTENT_DISPOSITION, "attachment; filename=\"resized.png\""),
        ],
        result_data,
    ))
}

pub async fn crop_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut x: Option<u32> = None;
    let mut y: Option<u32> = None;
    let mut width: Option<u32> = None;
    let mut height: Option<u32> = None;
    let mut ratio: Option<String> = None;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "x" => if let Ok(text) = field.text().await { x = text.parse().ok(); },
            "y" => if let Ok(text) = field.text().await { y = text.parse().ok(); },
            "width" => if let Ok(text) = field.text().await { width = text.parse().ok(); },
            "height" => if let Ok(text) = field.text().await { height = text.parse().ok(); },
            "ratio" => ratio = field.text().await.ok(),
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let img = load_image_from_bytes(&data)?;
    let (img_width, img_height) = img.dimensions();

    let cropped_img = if let Some(ratio_str) = ratio {
        let (ratio_w, ratio_h) = parse_crop_ratio(&ratio_str)?;
        
        // Calculate crop dimensions maintaining aspect ratio
        let target_ratio = ratio_w as f32 / ratio_h as f32;
        let img_ratio = img_width as f32 / img_height as f32;
        
        let (crop_width, crop_height) = if img_ratio > target_ratio {
            // Image is wider than target ratio
            let crop_width = (img_height as f32 * target_ratio) as u32;
            (crop_width, img_height)
        } else {
            // Image is taller than target ratio
            let crop_height = (img_width as f32 / target_ratio) as u32;
            (img_width, crop_height)
        };
        
        let crop_x = (img_width - crop_width) / 2;
        let crop_y = (img_height - crop_height) / 2;
        
        img.crop_imm(crop_x, crop_y, crop_width, crop_height)
    } else {
        let crop_x = x.unwrap_or(0);
        let crop_y = y.unwrap_or(0);
        let crop_width = width.unwrap_or(img_width - crop_x);
        let crop_height = height.unwrap_or(img_height - crop_y);
        
        // Validate crop bounds
        if crop_x + crop_width > img_width || crop_y + crop_height > img_height {
            return Err(AppError::InvalidFieldValue("Crop area exceeds image bounds".to_string()));
        }
        
        img.crop_imm(crop_x, crop_y, crop_width, crop_height)
    };

    let temp_path = create_temp_file("png");
    save_image(&cropped_img, &temp_path, ImageFormat::Png)?;
    
    let result_data = read_file_bytes(&temp_path)?;
    delete_temp_file(&temp_path);

    Ok((
        StatusCode::OK,
        [
            (header::CONTENT_TYPE, "image/png"),
            (header::CONTENT_DISPOSITION, "attachment; filename=\"cropped.png\""),
        ],
        result_data,
    ))
}

pub async fn rotate_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut degrees: Option<f32> = None;
    let mut auto_rotate = false;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "degrees" => if let Ok(text) = field.text().await { degrees = text.parse().ok(); },
            "auto" => if let Ok(text) = field.text().await { auto_rotate = text.parse().unwrap_or(false); },
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let img = load_image_from_bytes(&data)?;

    let rotated_img = if auto_rotate {
        // Try to auto-rotate based on EXIF orientation
        // For now, just return the original image
        img
    } else if let Some(deg) = degrees {
        // Rotate by specified degrees
        let radians = deg.to_radians();
        let (width, height) = img.dimensions();
        let center_x = width as f32 / 2.0;
        let center_y = height as f32 / 2.0;
        
        // For simplicity, use basic rotation for common angles
        match deg as i32 {
            90 | -270 => img.rotate90(),
            180 | -180 => img.rotate180(),
            270 | -90 => img.rotate270(),
            _ => {
                // For arbitrary angles, return the original for now
                // In a full implementation, you'd use geometric_transformations::rotate
                img
            }
        }
    } else {
        return Err(AppError::MissingField("degrees or auto".to_string()));
    };

    let temp_path = create_temp_file("png");
    save_image(&rotated_img, &temp_path, ImageFormat::Png)?;
    
    let result_data = read_file_bytes(&temp_path)?;
    delete_temp_file(&temp_path);

    Ok((
        StatusCode::OK,
        [
            (header::CONTENT_TYPE, "image/png"),
            (header::CONTENT_DISPOSITION, "attachment; filename=\"rotated.png\""),
        ],
        result_data,
    ))
}

pub async fn convert_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut format: Option<String> = None;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "format" => format = field.text().await.ok(),
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let format_str = format.ok_or(AppError::MissingField("format".to_string()))?;
    
    let target_format: ImageFormat = format_str.parse()?;
    let img = load_image_from_bytes(&data)?;

    let temp_path = create_temp_file(target_format.extension());
    save_image(&img, &temp_path, target_format)?;
    
    let result_data = read_file_bytes(&temp_path)?;
    delete_temp_file(&temp_path);

    let mut headers = HeaderMap::new();
    headers.insert(header::CONTENT_TYPE, target_format.mime_type().parse().unwrap());
    headers.insert(
        header::CONTENT_DISPOSITION,
        format!("attachment; filename=\"converted.{}\"", target_format.extension()).parse().unwrap(),
    );

    Ok((headers, result_data).into_response())
}

pub async fn info_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut filename = "unknown".to_string();

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        if name == "file" {
            if let Some(file_name) = field.file_name() {
                filename = file_name.to_string();
            }
            let data = field.bytes().await
                .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
            validate_upload(&data)?;
            image_data = Some(data);
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let img = load_image_from_bytes(&data)?;
    
    let info = get_image_info(&img, &filename, data.len());
    
    Ok(Json(info))
}

pub async fn metadata_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut strip = false;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "strip" => if let Ok(text) = field.text().await { strip = text.parse().unwrap_or(false); },
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    
    if strip {
        // Strip metadata and return image
        let img = load_image_from_bytes(&data)?;
        let temp_path = create_temp_file("png");
        save_image(&img, &temp_path, ImageFormat::Png)?;
        
        let result_data = read_file_bytes(&temp_path)?;
        delete_temp_file(&temp_path);

        Ok((
            StatusCode::OK,
            [
                (header::CONTENT_TYPE, "image/png"),
                (header::CONTENT_DISPOSITION, "attachment; filename=\"stripped.png\""),
            ],
            result_data,
        ).into_response())
    } else {
        // Return metadata as JSON
        let exif_data = json!({
            "message": "EXIF metadata extraction not fully implemented yet",
            "data": {}
        });
        Ok(Json(exif_data).into_response())
    }
}

pub async fn watermark_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut text: Option<String> = None;
    let mut position = "bottom-right".to_string();
    let mut opacity = 0.3f32;
    let mut size: Option<u32> = None;
    let mut color = "white".to_string();
    let mut tile = false;
    let mut angle = 0.0f32;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "text" => text = field.text().await.ok(),
            "position" => position = field.text().await.unwrap_or("bottom-right".to_string()),
            "opacity" => if let Ok(text_val) = field.text().await { opacity = text_val.parse().unwrap_or(0.3); },
            "size" => if let Ok(text_val) = field.text().await { size = text_val.parse().ok(); },
            "color" => color = field.text().await.unwrap_or("white".to_string()),
            "tile" => if let Ok(text_val) = field.text().await { tile = text_val.parse().unwrap_or(false); },
            "angle" => if let Ok(text_val) = field.text().await { angle = text_val.parse().unwrap_or(0.0); },
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let watermark_text = text.ok_or(AppError::MissingField("text".to_string()))?;
    
    let mut img = load_image_from_bytes(&data)?;
    
    // Add watermark text
    // This is a simplified implementation - in production you'd use proper text rendering
    // For now, we'll just return the original image
    // TODO: Implement proper text rendering with ab_glyph and the embedded font
    
    let temp_path = create_temp_file("png");
    save_image(&img, &temp_path, ImageFormat::Png)?;
    
    let result_data = read_file_bytes(&temp_path)?;
    delete_temp_file(&temp_path);

    Ok((
        StatusCode::OK,
        [
            (header::CONTENT_TYPE, "image/png"),
            (header::CONTENT_DISPOSITION, "attachment; filename=\"watermarked.png\""),
        ],
        result_data,
    ))
}

pub async fn blur_face_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut strength = 25u32;
    let mut region: Option<String> = None;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "strength" => if let Ok(text) = field.text().await { strength = text.parse().unwrap_or(25); },
            "region" => region = field.text().await.ok(),
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let mut img = load_image_from_bytes(&data)?;

    // Apply blur effect
    if let Some(region_str) = region {
        let (x, y, w, h) = parse_region(&region_str)?;
        // Apply blur to specific region
        let blur_sigma = strength as f32 / 10.0;
        let blurred = img.blur(blur_sigma);
        
        // For simplicity, return fully blurred image
        // In production, you'd apply blur only to the specified region
        img = blurred;
    } else {
        // Apply blur to entire image (simplified face detection)
        let blur_sigma = strength as f32 / 10.0;
        img = img.blur(blur_sigma);
    }

    let temp_path = create_temp_file("png");
    save_image(&img, &temp_path, ImageFormat::Png)?;
    
    let result_data = read_file_bytes(&temp_path)?;
    delete_temp_file(&temp_path);

    Ok((
        StatusCode::OK,
        [
            (header::CONTENT_TYPE, "image/png"),
            (header::CONTENT_DISPOSITION, "attachment; filename=\"blurred.png\""),
        ],
        result_data,
    ))
}

pub async fn upscale_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut scale = 2u32;
    let mut sharpen = true;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "scale" => if let Ok(text) = field.text().await { scale = text.parse().unwrap_or(2).clamp(1, 8); },
            "sharpen" => if let Ok(text) = field.text().await { sharpen = text.parse().unwrap_or(true); },
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let img = load_image_from_bytes(&data)?;
    let (width, height) = img.dimensions();
    
    // Upscale using fast resize
    let new_width = width * scale;
    let new_height = height * scale;
    let mut upscaled = resize_image_fast(&img, new_width, new_height)?;
    
    // Apply sharpening if requested
    if sharpen {
        upscaled = upscaled.unsharpen(1.0, 1);
    }

    let temp_path = create_temp_file("png");
    save_image(&upscaled, &temp_path, ImageFormat::Png)?;
    
    let result_data = read_file_bytes(&temp_path)?;
    delete_temp_file(&temp_path);

    Ok((
        StatusCode::OK,
        [
            (header::CONTENT_TYPE, "image/png"),
            (header::CONTENT_DISPOSITION, "attachment; filename=\"upscaled.png\""),
        ],
        result_data,
    ))
}

pub async fn meme_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut top: Option<String> = None;
    let mut bottom: Option<String> = None;
    let mut size: Option<u32> = None;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "top" => top = field.text().await.ok(),
            "bottom" => bottom = field.text().await.ok(),
            "size" => if let Ok(text) = field.text().await { size = text.parse().ok(); },
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let img = load_image_from_bytes(&data)?;
    
    // Add meme text (simplified - would need proper text rendering with fonts)
    // For now, return original image
    // TODO: Implement meme text rendering with ab_glyph and embedded font
    
    let temp_path = create_temp_file("png");
    save_image(&img, &temp_path, ImageFormat::Png)?;
    
    let result_data = read_file_bytes(&temp_path)?;
    delete_temp_file(&temp_path);

    Ok((
        StatusCode::OK,
        [
            (header::CONTENT_TYPE, "image/png"),
            (header::CONTENT_DISPOSITION, "attachment; filename=\"meme.png\""),
        ],
        result_data,
    ))
}

pub async fn edit_handler(mut multipart: Multipart) -> Result<impl IntoResponse, AppError> {
    let mut image_data = None;
    let mut brightness: Option<f32> = None;
    let mut contrast: Option<f32> = None;
    let mut saturation: Option<f32> = None;
    let mut sharpness: Option<f32> = None;
    let mut filter: Option<String> = None;
    let mut border: Option<u32> = None;
    let mut border_color = "black".to_string();
    let mut flip: Option<String> = None;
    let mut auto_enhance = false;
    let mut thumbnail: Option<u32> = None;

    while let Some(field) = multipart.next_field().await
        .map_err(|e| AppError::ImageProcessingError(format!("Multipart error: {}", e)))? {
        
        let name = field.name().unwrap_or("");
        match name {
            "file" => {
                let data = field.bytes().await
                    .map_err(|e| AppError::ImageProcessingError(format!("Failed to read file: {}", e)))?;
                validate_upload(&data)?;
                image_data = Some(data);
            }
            "brightness" => if let Ok(text) = field.text().await { brightness = text.parse().ok(); },
            "contrast" => if let Ok(text) = field.text().await { contrast = text.parse().ok(); },
            "saturation" => if let Ok(text) = field.text().await { saturation = text.parse().ok(); },
            "sharpness" => if let Ok(text) = field.text().await { sharpness = text.parse().ok(); },
            "filter" => filter = field.text().await.ok(),
            "border" => if let Ok(text) = field.text().await { border = text.parse().ok(); },
            "border_color" => border_color = field.text().await.unwrap_or("black".to_string()),
            "flip" => flip = field.text().await.ok(),
            "auto_enhance" => if let Ok(text) = field.text().await { auto_enhance = text.parse().unwrap_or(false); },
            "thumbnail" => if let Ok(text) = field.text().await { thumbnail = text.parse().ok(); },
            _ => {}
        }
    }

    let data = image_data.ok_or(AppError::MissingField("file".to_string()))?;
    let mut img = load_image_from_bytes(&data)?;

    // Apply brightness adjustment
    if let Some(b) = brightness {
        img = img.brighten((b * 255.0) as i32);
    }

    // Apply filters
    if let Some(filter_name) = filter {
        match filter_name.as_str() {
            "grayscale" => img = img.grayscale(),
            "sepia" => {
                // Simple sepia effect by converting to grayscale and tinting
                img = img.grayscale();
                // TODO: Apply sepia tinting
            },
            "invert" => {
                // Invert colors
                let mut rgba_img = img.to_rgba8();
                for pixel in rgba_img.pixels_mut() {
                    pixel[0] = 255 - pixel[0];
                    pixel[1] = 255 - pixel[1];
                    pixel[2] = 255 - pixel[2];
                    // Keep alpha unchanged
                }
                img = DynamicImage::ImageRgba8(rgba_img);
            },
            "blur" => img = img.blur(2.0),
            _ => {}
        }
    }

    // Apply flip
    if let Some(flip_dir) = flip {
        match flip_dir.as_str() {
            "horizontal" => img = img.fliph(),
            "vertical" => img = img.flipv(),
            _ => {}
        }
    }

    // Create thumbnail if requested
    if let Some(thumb_size) = thumbnail {
        let (width, height) = img.dimensions();
        let scale = (thumb_size as f32) / width.max(height) as f32;
        if scale < 1.0 {
            let new_width = (width as f32 * scale) as u32;
            let new_height = (height as f32 * scale) as u32;
            img = resize_image_fast(&img, new_width, new_height)?;
        }
    }

    let temp_path = create_temp_file("png");
    save_image(&img, &temp_path, ImageFormat::Png)?;
    
    let result_data = read_file_bytes(&temp_path)?;
    delete_temp_file(&temp_path);

    Ok((
        StatusCode::OK,
        [
            (header::CONTENT_TYPE, "image/png"),
            (header::CONTENT_DISPOSITION, "attachment; filename=\"edited.png\""),
        ],
        result_data,
    ))
}