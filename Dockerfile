# Use Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for webhook or healthcheck
EXPOSE 8080

# Run the main hunter script
CMD ["python", "main_hunter.py"]
