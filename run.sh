#!/bin/bash

##############################################################################
# IVIRS - Intelligent Vehicular Incident Reporting System
# One-Command Execution Script
# 
# Usage: ./run.sh [options]
#
# Options:
#   --help              Show this help message
#   --setup             Install dependencies and setup environment
#   --train-ml          Train machine learning models
#   --simulate          Run SUMO simulation only
#   --analyze           Run analysis and generate reports only
#   --full              Run complete pipeline (ML + Simulation + Analysis)
#   --duration SECS     Simulation duration (default: 1000)
#   --vehicles NUM      Number of vehicles (default: auto)
#   --fake-ratio RATIO  Ratio of fake reports (default: 0.3)
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DURATION=1000
VEHICLES="auto"
FAKE_RATIO=0.3

# Banner
print_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                       ║"
    echo "║   ██╗██╗   ██╗██╗██████╗ ███████╗                                   ║"
    echo "║   ██║██║   ██║██║██╔══██╗██╔════╝                                   ║"
    echo "║   ██║██║   ██║██║██████╔╝███████╗                                   ║"
    echo "║   ██║╚██╗ ██╔╝██║██╔══██╗╚════██║                                   ║"
    echo "║   ██║ ╚████╔╝ ██║██║  ██║███████║                                   ║"
    echo "║   ╚═╝  ╚═══╝  ╚═╝╚═╝  ╚═╝╚══════╝                                   ║"
    echo "║                                                                       ║"
    echo "║   Intelligent Vehicular Incident Reporting System                    ║"
    echo "║   PhD-Level Research Project                                         ║"
    echo "║   SUMO + NS-3 Integration with ML-based Fake Detection               ║"
    echo "║                                                                       ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print section header
section() {
    echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ $1${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
}

# Print step
step() {
    echo -e "${GREEN}➜${NC} $1"
}

# Print error
error() {
    echo -e "${RED}✖ ERROR:${NC} $1" >&2
}

# Print warning
warning() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
}

# Print success
success() {
    echo -e "${GREEN}✔ SUCCESS:${NC} $1"
}

# Check dependencies
check_dependencies() {
    section "Checking Dependencies"
    
    local missing_deps=0
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
        missing_deps=1
    else
        step "Python 3: $(python3 --version)"
    fi
    
    # Check SUMO
    if ! command -v sumo &> /dev/null; then
        warning "SUMO not found in PATH"
        if [ -z "$SUMO_HOME" ]; then
            error "SUMO_HOME environment variable not set"
            echo "  Please install SUMO: https://www.eclipse.org/sumo/"
            echo "  And set SUMO_HOME environment variable"
            missing_deps=1
        else
            step "SUMO_HOME: $SUMO_HOME"
        fi
    else
        # Test if SUMO actually works (xerces-c issue on macOS)
        if sumo --version &>/dev/null; then
            step "SUMO: $(sumo --version 2>&1 | head -n 1)"
        else
            warning "SUMO is installed but fails to run (likely xerces-c issue on macOS)"
            echo ""
            echo "  To fix this, run:"
            echo "    ./fix_macos.sh"
            echo ""
            echo "  Or manually:"
            echo "    cd /opt/homebrew/opt/xerces-c/lib"
            echo "    ln -s libxerces-c-3.3.dylib libxerces-c-3.2.dylib"
            echo ""
            missing_deps=1
        fi
    fi
    
    # Check required Python packages
    step "Checking Python packages..."
    
    local packages=("numpy" "pandas" "matplotlib" "seaborn" "sklearn")
    for pkg in "${packages[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            echo "  ✓ $pkg"
        else
            echo "  ✗ $pkg (missing)"
            missing_deps=1
        fi
    done
    
    if [ $missing_deps -eq 1 ]; then
        error "Missing dependencies detected"
        echo ""
        echo "Run with --setup to install dependencies:"
        echo "  ./run.sh --setup"
        echo ""
        echo "Or fix xerces-c issue on macOS:"
        echo "  ./fix_macos.sh"
        exit 1
    fi
    
    success "All dependencies satisfied"
}

# Setup environment
setup_environment() {
    section "Setting Up Environment"
    
    step "Installing Python dependencies..."
    pip3 install --break-system-packages numpy pandas matplotlib seaborn scikit-learn 2>&1 | grep -v "Requirement already satisfied" || true
    
    step "Creating directory structure..."
    mkdir -p "$PROJECT_DIR/sumo-scenario/results"
    mkdir -p "$PROJECT_DIR/ml-detection/models"
    mkdir -p "$PROJECT_DIR/ml-detection/datasets"
    mkdir -p "$PROJECT_DIR/analysis/visualizations"
    mkdir -p "$PROJECT_DIR/analysis/reports"
    mkdir -p "$PROJECT_DIR/ns3-simulation/results"
    
    step "Building SUMO network..."
    cd "$PROJECT_DIR/sumo-scenario/maps"
    
    if command -v netconvert &> /dev/null; then
        netconvert --node-files=highway.nod.xml --edge-files=highway.edg.xml \
                   --output-file=highway.net.xml \
                   --no-turnarounds true \
                   --geometry.remove false 2>&1 | tail -n 5
        success "SUMO network built successfully"
    else
        warning "netconvert not found - using pre-built network"
    fi
    
    cd "$PROJECT_DIR"
    
    step "Setting permissions..."
    chmod +x "$PROJECT_DIR/scripts/"*.py
    chmod +x "$PROJECT_DIR/ml-detection/"*.py
    chmod +x "$PROJECT_DIR/analysis/"*.py
    
    success "Environment setup completed"
}

# Train ML models
train_ml_models() {
    section "Training Machine Learning Models"
    
    step "Starting ML training..."
    cd "$PROJECT_DIR"
    python3 ml-detection/train_model.py
    
    success "ML models trained and saved"
}

# Run SUMO simulation
run_simulation() {
    section "Running SUMO Simulation"
    
    step "Simulation parameters:"
    echo "  Duration: $DURATION seconds"
    echo "  Vehicles: $VEHICLES"
    echo "  Fake Report Ratio: $FAKE_RATIO"
    
    step "Starting SUMO with TraCI controller..."
    cd "$PROJECT_DIR"
    
    # Clean previous results
    rm -f sumo-scenario/results/*.xml
    rm -f sumo-scenario/results/*.json
    rm -f sumo-scenario/results/*.csv
    
    # Run simulation
    python3 scripts/sumo_controller.py
    
    success "Simulation completed"
}

# Generate simulation data without SUMO (workaround)
run_simulation_no_sumo() {
    section "Generating Simulation Data (SUMO-Free Mode)"
    
    warning "Using data generator instead of SUMO"
    echo "  This generates realistic data without requiring SUMO to run"
    echo "  Useful when SUMO has library issues (xerces-c on macOS)"
    echo ""
    
    step "Simulation parameters:"
    echo "  Duration: $DURATION seconds"
    echo "  Fake Report Ratio: $FAKE_RATIO"
    
    step "Generating simulation data..."
    cd "$PROJECT_DIR"
    
    # Clean previous results
    rm -f sumo-scenario/results/*.json
    rm -f sumo-scenario/results/*.csv
    
    # Run data generator
    python3 scripts/generate_simulation_data.py
    
    success "Simulation data generated"
}

# Run analysis
run_analysis() {
    section "Generating Analysis and Reports"
    
    step "Analyzing simulation results..."
    cd "$PROJECT_DIR"
    python3 analysis/generate_reports.py
    
    step "Opening results..."
    if [ -f "analysis/reports/research_report.txt" ]; then
        echo ""
        echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
        cat analysis/reports/research_report.txt | head -n 50
        echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "Full report: analysis/reports/research_report.txt"
    fi
    
    success "Analysis completed"
    
    echo ""
    echo -e "${GREEN}📊 Generated Outputs:${NC}"
    echo "  📈 Visualizations:    analysis/visualizations/"
    echo "  📄 Research Report:   analysis/reports/research_report.txt"
    echo "  📊 Metrics JSON:      analysis/reports/metrics.json"
    echo "  📋 Raw Results:       sumo-scenario/results/"
}

# Show help
show_help() {
    print_banner
    echo "Usage: ./run.sh [options]"
    echo ""
    echo "Options:"
    echo "  --help              Show this help message"
    echo "  --setup             Install dependencies and setup environment"
    echo "  --train-ml          Train machine learning models"
    echo "  --simulate          Run SUMO simulation only"
    echo "  --simulate-no-sumo  Generate simulation data WITHOUT SUMO (workaround)"
    echo "  --analyze           Run analysis and generate reports only"
    echo "  --full              Run complete pipeline (ML + Simulation + Analysis)"
    echo "  --full-no-sumo      Complete pipeline WITHOUT SUMO (workaround)"
    echo "  --duration SECS     Simulation duration (default: 1000)"
    echo "  --vehicles NUM      Number of vehicles (default: auto)"
    echo "  --fake-ratio RATIO  Ratio of fake reports (default: 0.3)"
    echo ""
    echo "Examples:"
    echo "  ./run.sh --setup                    # First time setup"
    echo "  ./run.sh --full                     # Run everything (requires SUMO)"
    echo "  ./run.sh --full-no-sumo             # Run without SUMO (if SUMO broken)"
    echo "  ./run.sh --simulate --duration 500  # Run 500s simulation"
    echo "  ./run.sh --analyze                  # Just generate reports"
    echo ""
    echo "SUMO Issues?"
    echo "  If SUMO won't run (xerces-c issues on macOS):"
    echo "  1. Try: ./fix_macos.sh"
    echo "  2. Or use: ./run.sh --full-no-sumo"
    echo ""
}

# Main execution
main() {
    print_banner
    
    # Parse arguments
    MODE="full"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_help
                exit 0
                ;;
            --setup)
                MODE="setup"
                shift
                ;;
            --train-ml)
                MODE="train"
                shift
                ;;
            --simulate)
                MODE="simulate"
                shift
                ;;
            --simulate-no-sumo)
                MODE="simulate_no_sumo"
                shift
                ;;
            --analyze)
                MODE="analyze"
                shift
                ;;
            --full)
                MODE="full"
                shift
                ;;
            --full-no-sumo)
                MODE="full_no_sumo"
                shift
                ;;
            --duration)
                DURATION="$2"
                shift 2
                ;;
            --vehicles)
                VEHICLES="$2"
                shift 2
                ;;
            --fake-ratio)
                FAKE_RATIO="$2"
                shift 2
                ;;
            *)
                error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Execute based on mode
    case $MODE in
        setup)
            setup_environment
            ;;
        train)
            check_dependencies
            train_ml_models
            ;;
        simulate)
            check_dependencies
            run_simulation
            ;;
        simulate_no_sumo)
            run_simulation_no_sumo
            ;;
        analyze)
            run_analysis
            ;;
        full)
            check_dependencies
            setup_environment
            train_ml_models
            run_simulation
            run_analysis
            ;;
        full_no_sumo)
            setup_environment
            train_ml_models
            run_simulation_no_sumo
            run_analysis
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    IVIRS EXECUTION COMPLETED                          ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Run main
main "$@"
