FROM python:3.10

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Skip apt-get if possible or use a base image that has most libs
# Standard 'python:3.10' (non-slim) usually has build-essential and common libs

# Install only absolutely necessary runtime libs if they are missing
# For now, let's try just pip installing and see what's missing

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p uploads processed_uploads

# Expose port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
