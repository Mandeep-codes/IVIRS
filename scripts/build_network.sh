#!/bin/bash
# Build SUMO Network
# This script creates the highway.net.xml file from node and edge definitions

echo "Building SUMO network from XML definitions..."

cd "$(dirname "$0")/../sumo-scenario/maps"

# Check if netconvert is available
if ! command -v netconvert &> /dev/null; then
    echo "ERROR: netconvert not found"
    echo "Please install SUMO tools or set SUMO_HOME"
    exit 1
fi

# Build the network
netconvert \
    --node-files=highway.nod.xml \
    --edge-files=highway.edg.xml \
    --output-file=highway.net.xml \
    --no-turnarounds=true \
    --geometry.remove=false \
    --junctions.corner-detail=5 \
    --ramps.guess=true \
    --tls.guess=false \
    --default.speed=33.33 \
    --default.priority=5

if [ $? -eq 0 ]; then
    echo "✓ Network built successfully: highway.net.xml"
    echo "  Nodes: $(grep -c '<junction' highway.net.xml)"
    echo "  Edges: $(grep -c '<edge ' highway.net.xml)"
else
    echo "✗ Network build failed"
    exit 1
fi
