# Use Python 3.14.6 slim image as base
FROM python:3.14.6-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy nginx configuration
COPY config/nginx.conf /etc/nginx/nginx.conf

# Expose port 80 for nginx
EXPOSE 80

# Create startup script
RUN echo '#!/bin/bash\nset -e\n\n# Start FastAPI application in background\nuvicorn main:app --host 127.0.0.1 --port 8000 &\n\n# Start nginx\nnginx -g "daemon off;"' > /app/start.sh && chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Run startup script
CMD ["/app/start.sh"]
