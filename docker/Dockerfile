# Use the official Python image as the base image
FROM python:3.14.4-slim

ENV APP_HOME=/app \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/app \
  UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy \
  UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  curl \
  git \
  python3-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install uv
RUN pip install --upgrade pip \
  && pip install uv --no-cache-dir

# Copy the dependencies files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv
RUN uv sync --no-dev

# Copy the rest of the application code
COPY . .

# Run the application
CMD ["fastapi", "run", "src/main.py"]
