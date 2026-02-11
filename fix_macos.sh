#!/bin/bash
# IVIRS - macOS xerces-c Library Fix
# This script fixes the xerces-c library dependency issue on macOS

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        IVIRS - macOS xerces-c Library Fix                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "This script is for macOS only."
    echo "On Linux, xerces-c should work out of the box."
    exit 0
fi

echo "Checking xerces-c installation..."

# Check if xerces-c is installed
if ! brew list xerces-c &>/dev/null; then
    echo "❌ xerces-c not found. Installing..."
    brew install xerces-c
else
    echo "✓ xerces-c is installed"
fi

# Find xerces-c lib directory
XERCES_LIB_DIR=$(brew --prefix xerces-c)/lib

if [ ! -d "$XERCES_LIB_DIR" ]; then
    echo "❌ xerces-c lib directory not found at $XERCES_LIB_DIR"
    echo "Trying to reinstall xerces-c..."
    brew reinstall xerces-c
    XERCES_LIB_DIR=$(brew --prefix xerces-c)/lib
fi

echo "xerces-c lib directory: $XERCES_LIB_DIR"

# Check for version 3.3
if [ -f "$XERCES_LIB_DIR/libxerces-c-3.3.dylib" ]; then
    echo "✓ Found libxerces-c-3.3.dylib"
    
    # Check if 3.2 symlink already exists
    if [ -L "$XERCES_LIB_DIR/libxerces-c-3.2.dylib" ]; then
        echo "✓ Symlink libxerces-c-3.2.dylib already exists"
    elif [ -f "$XERCES_LIB_DIR/libxerces-c-3.2.dylib" ]; then
        echo "✓ libxerces-c-3.2.dylib already exists (real file)"
    else
        echo "Creating symlink: libxerces-c-3.2.dylib -> libxerces-c-3.3.dylib"
        cd "$XERCES_LIB_DIR"
        ln -s libxerces-c-3.3.dylib libxerces-c-3.2.dylib
        echo "✓ Symlink created successfully"
    fi
else
    echo "❌ libxerces-c-3.3.dylib not found"
    echo "Attempting to reinstall xerces-c..."
    brew reinstall xerces-c
fi

echo ""
echo "Testing SUMO binaries..."
echo ""

# Test sumo (headless)
if command -v sumo &>/dev/null; then
    if sumo --version &>/dev/null; then
        echo "✓ sumo (headless) works!"
        SUMO_VERSION=$(sumo --version 2>&1 | head -n 1)
        echo "  $SUMO_VERSION"
    else
        echo "❌ sumo command fails (xerces-c issue persists)"
    fi
else
    echo "⚠ sumo command not found (SUMO may not be installed)"
fi

# Test sumo-gui
if command -v sumo-gui &>/dev/null; then
    if sumo-gui --version &>/dev/null; then
        echo "✓ sumo-gui works!"
    else
        echo "❌ sumo-gui fails (xerces-c issue persists)"
        echo "  Don't worry - the project uses 'sumo' (headless) by default"
    fi
else
    echo "⚠ sumo-gui command not found"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                     Fix Complete!                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Run: ./run.sh --full"
echo "  2. The simulation will use 'sumo' (headless, faster)"
echo "  3. Results will be in analysis/reports/"
echo ""
