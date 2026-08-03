# DomOS Cashier MVP - Frontend Dockerfile

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for API URL configuration
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

# Cache bust to force rebuild when commit changes
ARG CACHEBUST=1

# Build the application
RUN echo "Building with VITE_API_URL=$VITE_API_URL (cache: $CACHEBUST)" && npm run build

# Production stage with nginx
FROM nginx:alpine AS production

# Remove default nginx configs to avoid conflicts
RUN rm -f /etc/nginx/conf.d/default.conf /etc/nginx/nginx.conf

# Copy nginx.cloudrun.conf as template (uses ${PORT} variable)
COPY nginx.cloudrun.conf /etc/nginx/nginx.conf.template

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port (Cloud Run uses PORT env variable, default 8080)
EXPOSE 8080

# Note: Cloud Run has its own health check probes
# Use envsubst to replace ${PORT} in nginx config at runtime
# Default PORT to 8080 if not set
CMD ["sh", "-c", "export PORT=${PORT:-8080} && envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"]
