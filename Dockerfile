# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose webhook port
EXPOSE 8080

# Start command
CMD ["sh", "-c", "uvicorn webhook_server:app --host 0.0.0.0 --port 8080 & python3 main_hunter.py"]