# Use Python 3.13 slim image for smaller size
FROM python:3.13-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including build tools for numpy
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 streamlit && \
    useradd --uid 1000 --gid streamlit --shell /bin/bash --create-home streamlit

# Set working directory
WORKDIR /app

# Copy pyproject.toml for dependency installation
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir \
    streamlit==1.31.0 \
    pyyaml==6.0.1 \
    pandas \
    pillow

# Copy application files
COPY app.py ./
COPY config.yaml ./
COPY event_logo.png ./
COPY assets/ ./assets/

# Change ownership of application files to non-root user
RUN chown -R streamlit:streamlit /app

# Expose Streamlit port
EXPOSE 8501

# Add health check for Streamlit endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Switch to non-root user
USER streamlit

# Run Streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]