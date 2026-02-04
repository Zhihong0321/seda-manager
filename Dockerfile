# Use a slim Python image for efficiency
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure storage directory exists (though it should be mounted as a volume in Railway)
RUN mkdir -p /storage

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the port FastAPI will run on
EXPOSE 8000

# Create storage directory at runtime (in case volume mount hasn't created it yet)
# and run the application
CMD ["sh", "-c", "mkdir -p /storage && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
