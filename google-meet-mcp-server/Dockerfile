FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package.json bun.lock ./

# Install dependencies
RUN npm install

# Copy source code
COPY src/ ./src/

# Keep container alive - the MCP server will be run via docker exec
# This allows the backend to call: docker exec -i google-meet-mcp node src/index.js
CMD ["tail", "-f", "/dev/null"]
