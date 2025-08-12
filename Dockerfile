FROM ghcr.io/astral-sh/uv:0.8-python3.12-bookworm-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy workspace files for dependency resolution
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --locked

# Copy application code
COPY src/ src/

# Create cache directory and change ownership
RUN mkdir -p /home/appuser/.cache/uv && \
    chown -R appuser:appuser /app /home/appuser/.cache

# Switch to non-root user
USER appuser

# Expose port (updated to match our config default)
EXPOSE 8080

# Run the application using our new package structure
CMD ["uv", "run", "python", "-m", "src"]