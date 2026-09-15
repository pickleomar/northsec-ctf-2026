#!/bin/bash

docker build -t escape-the-matrix .

# Run the container
docker run -p 8080:8080 escape-the-matrix escape-matrix-diagonalhh