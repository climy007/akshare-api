# Dockerfile for AKShare MCP Server
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application files
COPY akshare_api.py ./akshare_api.py
COPY akshare-api.py ./akshare-api.py
COPY akshare_client.py ./akshare_client.py
COPY stock_*.py ./
COPY config.py ./config.py
COPY mcp_server.py ./mcp_server.py
COPY mcp_utils.py ./mcp_utils.py
COPY ops ./ops

# Create directory for AKTools if needed
RUN mkdir -p /var/log/aktools

# Expose MCP port
EXPOSE 3115

# Set environment variables for MCP server
ENV MCP_SERVER_PORT=3115
ENV MCP_SERVER_HOST=0.0.0.0
ENV AKTOOLS_BASE_URL=http://aktools:8080

# Run the MCP server
CMD ["python", "mcp_server.py"]
