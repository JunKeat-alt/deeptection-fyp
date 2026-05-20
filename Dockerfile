# Dockerfile for Hugging Face Spaces (Docker SDK).
# Builds the Flask backend and serves the pre-built React frontend as static files.

FROM python:3.11-slim

# System deps: ffmpeg (audio extraction) + build tools for some wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgl1 \
        libglib2.0-0 \
        git \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend
COPY backend/ /app/backend/

# Copy pre-built frontend (built separately with `npm run build`)
# On HF Spaces you push the built output as `frontend/dist/`.
COPY frontend/dist/ /app/frontend/dist/

ENV PYTHONPATH=/app/backend
ENV HF_HOME=/app/backend/storage/hf_cache
ENV DEEPTECTION_SERVE_STATIC=1
ENV PORT=7860

EXPOSE 7860

# Use gunicorn with a single worker (models are loaded in-process) and
# threaded workers so multiple requests can share the server.
CMD ["gunicorn", "-w", "1", "-k", "gthread", "--threads", "4", \
     "-t", "300", "-b", "0.0.0.0:7860", \
     "--chdir", "/app/backend", "app:app"]
