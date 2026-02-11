#!/bin/bash
# Build SUMO from source to fix xerces-c compatibility

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     Building SUMO from Source (This will take 30+ min)       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "This is necessary because Homebrew's SUMO is incompatible with"
echo "the current xerces-c version. We'll build SUMO ourselves."
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Install build dependencies
echo ""
echo "Installing build dependencies..."
brew install cmake gcc fox xerces-c proj gdal gl2ps eigen

# Create build directory
BUILD_DIR="$HOME/sumo-build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Clone SUMO if not already there
if [ ! -d "sumo" ]; then
    echo ""
    echo "Cloning SUMO repository..."
    git clone --depth 1 --branch v1_20_0 https://github.com/eclipse/sumo.git
fi

cd sumo

# Create build directory
mkdir -p build
cd build

# Configure with CMake
echo ""
echo "Configuring SUMO build..."
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DFOX_CONFIG=/opt/homebrew/bin/fox-config

# Build (using all CPU cores)
echo ""
echo "Building SUMO (this takes 20-40 minutes)..."
make -j$(sysctl -n hw.ncpu)

# Install
echo ""
echo "Installing SUMO..."
sudo make install

# Set environment
echo ""
echo "Setting environment variables..."
export SUMO_HOME="/usr/local/share/sumo"
if ! grep -q "SUMO_HOME" ~/.zshrc 2>/dev/null; then
    echo 'export SUMO_HOME="/usr/local/share/sumo"' >> ~/.zshrc
    echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  Build Complete!                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Testing SUMO..."
/usr/local/bin/sumo --version

echo ""
echo "✅ SUMO is now working!"
echo ""
echo "Next steps:"
echo "  1. Close this terminal"
echo "  2. Open a NEW terminal"
echo "  3. cd IVIRS-Project"
echo "  4. ./run.sh --full"
echo ""
