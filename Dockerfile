# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY . .

# Install dependencies using uv
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Start command
CMD ["uv", "run", "granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "8000", "src.ai_classifier.main:app"]