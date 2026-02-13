use crate::types::{AppError, ImageFormat};

const MAX_UPLOAD_SIZE: usize = 20 * 1024 * 1024; // 20MB

pub fn validate_upload(data: &[u8]) -> Result<ImageFormat, AppError> {
    // Check file size
    if data.len() > MAX_UPLOAD_SIZE {
        return Err(AppError::FileTooLarge);
    }

    // Check magic bytes to determine format
    match ImageFormat::from_magic_bytes(data) {
        Some(format) => Ok(format),
        None => Err(AppError::UnsupportedImageFormat),
    }
}

pub fn parse_crop_ratio(ratio: &str) -> Result<(u32, u32), AppError> {
    let parts: Vec<&str> = ratio.split(':').collect();
    if parts.len() != 2 {
        return Err(AppError::InvalidFieldValue(format!(
            "Invalid ratio format. Expected 'width:height', got '{}'",
            ratio
        )));
    }

    let width = parts[0].parse::<u32>().map_err(|_| {
        AppError::InvalidFieldValue(format!("Invalid width in ratio: {}", parts[0]))
    })?;

    let height = parts[1].parse::<u32>().map_err(|_| {
        AppError::InvalidFieldValue(format!("Invalid height in ratio: {}", parts[1]))
    })?;

    if width == 0 || height == 0 {
        return Err(AppError::InvalidFieldValue(
            "Ratio dimensions must be greater than 0".to_string(),
        ));
    }

    Ok((width, height))
}

pub fn parse_region(region: &str) -> Result<(u32, u32, u32, u32), AppError> {
    let parts: Vec<&str> = region.split(',').collect();
    if parts.len() != 4 {
        return Err(AppError::InvalidFieldValue(format!(
            "Invalid region format. Expected 'x,y,w,h', got '{}'",
            region
        )));
    }

    let x = parts[0].parse::<u32>().map_err(|_| {
        AppError::InvalidFieldValue(format!("Invalid x coordinate: {}", parts[0]))
    })?;

    let y = parts[1].parse::<u32>().map_err(|_| {
        AppError::InvalidFieldValue(format!("Invalid y coordinate: {}", parts[1]))
    })?;

    let w = parts[2].parse::<u32>().map_err(|_| {
        AppError::InvalidFieldValue(format!("Invalid width: {}", parts[2]))
    })?;

    let h = parts[3].parse::<u32>().map_err(|_| {
        AppError::InvalidFieldValue(format!("Invalid height: {}", parts[3]))
    })?;

    if w == 0 || h == 0 {
        return Err(AppError::InvalidFieldValue(
            "Region dimensions must be greater than 0".to_string(),
        ));
    }

    Ok((x, y, w, h))
}