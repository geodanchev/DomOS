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

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine AS production

# Copy nginx.cloudrun.conf as template
COPY nginx.cloudrun.conf /etc/nginx/nginx.conf.template

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port (Cloud Run uses PORT env variable, default 8080)
EXPOSE 8080

# Note: Cloud Run has its own health check probes
# Use envsubst to replace ${PORT} in nginx config at runtime
# Default PORT to 8080 if not set
CMD ["sh", "-c", "export PORT=${PORT:-8080} && envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"]
