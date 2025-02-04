# Use Python image
FROM python:3.12.8-slim

# Set working directory
WORKDIR /app

# Install dependencies and utilities
RUN apt-get update && \
    apt-get install curl netcat-openbsd -y && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Run the ingestion script
CMD ["python", "ingestion.py"]
