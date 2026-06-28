# Copyright (c) 2026 Clove Twilight
# Licensed under the ESAL-1.3 Licence.
# See LICENCE.md in the project root for full licence information.

# Option 1: Use Ubuntu base instead of Alpine (most reliable)
FROM node:25-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with corrected npm configuration for Docker
RUN npm install --ignore-scripts && npm rebuild

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 5001

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5001/ || exit 1

# Start the preview server
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5001"]
