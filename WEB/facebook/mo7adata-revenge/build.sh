#!/bin/bash

# Build the Podman/Docker image
podman build -t bloog-app .

# Create a logs directory on the host machine (if it doesn't exist)
mkdir -p ./logs

# Run the Podman/Docker container with a volume mount
podman run -d -p 5000:5000 --name bloog-container -v ./logs:/app/logs bloog-app

# Print the container status
podman ps -a | grep bloog-container