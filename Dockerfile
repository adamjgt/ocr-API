FROM python:3.11-slim

# Install Tesseract
RUN apt-get update && \
    apt-get install -y tesseract-ocr && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirement list first (cache-friendly)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Expose port (optional)
EXPOSE 8000

# Run the app
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"

