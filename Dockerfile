# Multi-stage Dockerfile for Railway deployment — Rust API
FROM rust:1.85-bookworm as builder

WORKDIR /usr/src/app

# Copy manifests first for dependency caching
COPY rust-api/Cargo.toml rust-api/Cargo.lock ./

# Create dummy main to cache dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release 2>/dev/null || true
RUN rm -rf src

# Copy real source + assets
COPY rust-api/src ./src
COPY rust-api/assets ./assets

# Build the actual application
RUN cargo build --release

# Runtime stage — minimal image
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1001 appuser

COPY --from=builder /usr/src/app/target/release/gimg-rust-api /usr/local/bin/gimg-rust-api

RUN mkdir -p /tmp && chmod 1777 /tmp

USER appuser

ENV PORT=8787
EXPOSE 8787

CMD ["gimg-rust-api"]
