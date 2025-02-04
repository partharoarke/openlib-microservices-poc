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

# Run the app
#CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
CMD ["gunicorn", "app:app", "--workers", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5000"]



