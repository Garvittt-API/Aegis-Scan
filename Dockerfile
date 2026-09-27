# ==============================================================================
# AegisScan Multi-Stage Production Dockerfile
# Stage 1: Build React Vite Frontend
# Stage 2: Hardened Python 3.12 Backend with Security Scanners & Reverse Proxy Setup
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Frontend
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Python Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

# Security: Install minimal OS dependencies and security scanner binaries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend/ ./backend/

# Copy built frontend static files
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Security: Create non-root user and assign permissions
RUN useradd -u 1001 -m -s /bin/bash aegis && \
    mkdir -p /app/backend/reports /app/backend/artifacts && \
    chown -R aegis:aegis /app

USER aegis
WORKDIR /app/backend

# Environment variables
ENV APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Start production uvicorn server with worker threads
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
