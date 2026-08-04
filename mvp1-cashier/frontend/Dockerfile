# Multi-stage build for optimized frontend image

# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build argument for API URL
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Build argument for cache busting
ARG CACHEBUST=1

# Build the application
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Remove default nginx configs to avoid conflicts
RUN rm -f /etc/nginx/conf.d/default.conf /etc/nginx/nginx.conf

# Copy nginx.cloudrun.conf as template (uses ${PORT} variable)
COPY nginx.cloudrun.conf /etc/nginx/nginx.conf.template

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port (Cloud Run uses PORT env variable, default 8080)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:${PORT:-8080}/health || exit 1

# Use envsubst to replace ${PORT} in nginx config at runtime
# Default PORT to 8080 if not set
CMD ["sh", "-c", "export PORT=${PORT:-8080} && envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"]
