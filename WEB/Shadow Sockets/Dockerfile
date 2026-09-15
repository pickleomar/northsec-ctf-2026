# Use a lightweight Python image
FROM python:3.9-slim

# Prevent python from buffering stdout/stderr (better logs)
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user for security (standard CTF practice)
RUN useradd -m ctfuser
USER ctfuser

# Expose the port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]