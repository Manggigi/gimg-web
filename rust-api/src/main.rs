use axum::{
    http::StatusCode,
    response::{IntoResponse, Json},
    routing::{get, post},
    Router,
};
use serde::Serialize;
use std::{env, net::SocketAddr};
use tower::ServiceBuilder;
use tower_http::{
    cors::CorsLayer,
    limit::RequestBodyLimitLayer,
};
use tracing::info;

mod handlers;
mod image_utils;
mod types;
mod validation;

use handlers::*;

#[derive(Serialize)]
struct HealthResponse {
    status: String,
}

#[derive(Serialize)]
struct Tool {
    name: String,
    description: String,
}

fn get_tools() -> Vec<Tool> {
    vec![
        Tool { name: "compress".to_string(), description: "Compress images by reducing quality".to_string() },
        Tool { name: "resize".to_string(), description: "Resize images by dimensions or percentage".to_string() },
        Tool { name: "crop".to_string(), description: "Crop images by coordinates or aspect ratio".to_string() },
        Tool { name: "rotate".to_string(), description: "Rotate images by degrees or auto-orient".to_string() },
        Tool { name: "convert".to_string(), description: "Convert images between formats".to_string() },
        Tool { name: "info".to_string(), description: "Get image info (dimensions, format, size, mode)".to_string() },
        Tool { name: "metadata".to_string(), description: "View or strip EXIF metadata".to_string() },
        Tool { name: "watermark".to_string(), description: "Add text or image watermarks".to_string() },
        Tool { name: "blur-face".to_string(), description: "Detect and blur faces".to_string() },
        Tool { name: "remove-bg".to_string(), description: "Remove image background".to_string() },
        Tool { name: "upscale".to_string(), description: "Upscale images with LANCZOS resampling".to_string() },
        Tool { name: "meme".to_string(), description: "Add meme text (top/bottom)".to_string() },
        Tool { name: "edit".to_string(), description: "Photo editor: brightness, contrast, filters, borders, etc.".to_string() },
        Tool { name: "html-to-img".to_string(), description: "Screenshot a URL (not available in web mode)".to_string() },
    ]
}

async fn health() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".to_string(),
    })
}

async fn tools() -> Json<Vec<Tool>> {
    Json(get_tools())
}

async fn not_implemented() -> impl IntoResponse {
    (StatusCode::NOT_IMPLEMENTED, "Not Implemented")
}

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    // Build the API routes
    let api_router = Router::new()
        .route("/health", get(health))
        .route("/tools", get(tools))
        .route("/compress", post(compress_handler))
        .route("/resize", post(resize_handler))
        .route("/crop", post(crop_handler))
        .route("/rotate", post(rotate_handler))
        .route("/convert", post(convert_handler))
        .route("/info", post(info_handler))
        .route("/metadata", post(metadata_handler))
        .route("/watermark", post(watermark_handler))
        .route("/blur-face", post(blur_face_handler))
        .route("/remove-bg", post(not_implemented))
        .route("/upscale", post(upscale_handler))
        .route("/meme", post(meme_handler))
        .route("/edit", post(edit_handler))
        .route("/html-to-img", post(not_implemented))
        .layer(
            ServiceBuilder::new()
                .layer(RequestBodyLimitLayer::new(20 * 1024 * 1024)) // 20MB limit
                .layer(CorsLayer::permissive()) // Allow all origins
        );

    // Main app router
    let app = Router::new()
        .nest("/api", api_router);

    // Get port from environment or default to 8787
    let port = env::var("PORT")
        .unwrap_or_else(|_| "8787".to_string())
        .parse::<u16>()
        .expect("PORT must be a valid number");

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    
    info!("GIMG Rust API server starting on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("Failed to bind to address");

    axum::serve(listener, app)
        .await
        .expect("Failed to start server");
}