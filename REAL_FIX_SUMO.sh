#!/bin/bash
# IVIRS - Complete SUMO Fix for macOS
# This script ACTUALLY fixes the xerces-c issue

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           FIXING SUMO - Complete Solution                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Fix 1: Reinstall xerces-c with correct version
echo "Step 1: Reinstalling xerces-c..."
brew uninstall xerces-c --ignore-dependencies 2>/dev/null || true
brew install xerces-c

# Fix 2: Reinstall SUMO to relink against new xerces-c
echo ""
echo "Step 2: Reinstalling SUMO..."
brew uninstall sumo --ignore-dependencies 2>/dev/null || true
brew install sumo

# Fix 3: Create symlinks if needed
echo ""
echo "Step 3: Creating compatibility symlinks..."
XERCES_DIR="/opt/homebrew/opt/xerces-c/lib"

if [ -d "$XERCES_DIR" ]; then
    cd "$XERCES_DIR"
    
    # Find the actual version
    ACTUAL_LIB=$(ls -1 libxerces-c-*.dylib 2>/dev/null | head -n 1)
    
    if [ -n "$ACTUAL_LIB" ]; then
        echo "Found: $ACTUAL_LIB"
        
        # Create 3.2 symlink if it doesn't exist
        if [ ! -e "libxerces-c-3.2.dylib" ]; then
            ln -sf "$ACTUAL_LIB" libxerces-c-3.2.dylib
            echo "Created: libxerces-c-3.2.dylib -> $ACTUAL_LIB"
        fi
        
        # Create 3.3 symlink if it doesn't exist  
        if [ ! -e "libxerces-c-3.3.dylib" ]; then
            ln -sf "$ACTUAL_LIB" libxerces-c-3.3.dylib
            echo "Created: libxerces-c-3.3.dylib -> $ACTUAL_LIB"
        fi
    fi
fi

# Fix 4: Set DYLD_LIBRARY_PATH
echo ""
echo "Step 4: Setting library paths..."
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/xerces-c/lib:$DYLD_LIBRARY_PATH"
echo "export DYLD_LIBRARY_PATH=\"/opt/homebrew/opt/xerces-c/lib:\$DYLD_LIBRARY_PATH\"" >> ~/.zshrc

# Fix 5: Set SUMO_HOME
echo ""
echo "Step 5: Setting SUMO_HOME..."
export SUMO_HOME="/opt/homebrew/opt/sumo/share/sumo"
if ! grep -q "SUMO_HOME" ~/.zshrc 2>/dev/null; then
    echo "export SUMO_HOME=\"/opt/homebrew/opt/sumo/share/sumo\"" >> ~/.zshrc
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Testing SUMO                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Test SUMO
if command -v sumo &>/dev/null; then
    if sumo --version 2>&1 | grep -q "Eclipse SUMO"; then
        echo "✅ SUMO WORKS!"
        sumo --version | head -n 1
    else
        echo "❌ sumo still fails"
        echo ""
        echo "ERROR OUTPUT:"
        sumo --version 2>&1 | head -n 5
    fi
else
    echo "❌ sumo command not found"
fi

echo ""

# Test SUMO-GUI
if command -v sumo-gui &>/dev/null; then
    if sumo-gui --version 2>&1 | grep -q "Eclipse SUMO"; then
        echo "✅ SUMO-GUI WORKS!"
        sumo-gui --version | head -n 1
    else
        echo "❌ sumo-gui still fails"
        echo ""
        echo "ERROR OUTPUT:"
        sumo-gui --version 2>&1 | head -n 5
    fi
else
    echo "❌ sumo-gui command not found"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                         IMPORTANT                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Close this terminal and open a NEW terminal"
echo "2. OR run: source ~/.zshrc"
echo "3. Then try: sumo --version"
echo "4. If it works, run: ./run.sh --full"
echo ""
