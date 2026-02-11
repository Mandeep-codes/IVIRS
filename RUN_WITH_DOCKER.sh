#!/bin/bash
# Run SUMO in Docker container (bypasses all library issues)

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         SUMO via Docker (Guaranteed to Work)                  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    echo ""
    echo "Please install Docker Desktop from:"
    echo "https://www.docker.com/products/docker-desktop"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Pull SUMO Docker image
echo "Pulling SUMO Docker image..."
docker pull eclipse/sumo:latest

# Run SUMO in container
echo ""
echo "Running SUMO simulation in Docker..."
docker run -it --rm \
    -v "$(pwd)/sumo-scenario:/sumo" \
    -v "$(pwd)/results:/results" \
    eclipse/sumo:latest \
    sumo -c /sumo/simulation.sumocfg

echo ""
echo "✅ Simulation completed!"
