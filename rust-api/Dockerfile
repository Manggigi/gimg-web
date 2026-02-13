# Multi-stage Dockerfile for Railway deployment
FROM rust:1.87-bookworm as builder

WORKDIR /usr/src/app

# Copy manifests first for dependency caching
COPY Cargo.toml Cargo.lock ./

# Create dummy main to cache dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release 2>/dev/null || true
RUN rm -rf src

# Copy real source + assets
COPY src ./src
COPY assets ./assets

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