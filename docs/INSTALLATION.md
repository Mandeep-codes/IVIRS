# IVIRS Installation & Troubleshooting Guide

## Complete Installation Guide

### Step 1: Install SUMO

#### On Ubuntu/Debian:
```bash
sudo add-apt-repository ppa:sumo/stable
sudo apt-get update
sudo apt-get install sumo sumo-tools sumo-doc
```

#### On macOS:
```bash
brew install sumo
```

#### On Windows (WSL recommended):
1. Install WSL2
2. Follow Ubuntu instructions above

### Step 2: Set Environment Variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export SUMO_HOME="/usr/share/sumo"
export PATH="$PATH:$SUMO_HOME/tools"
```

Then reload:
```bash
source ~/.bashrc
```

### Step 3: Install Python Dependencies

```bash
pip3 install --user numpy pandas matplotlib seaborn scikit-learn
```

Or with conda:
```bash
conda install numpy pandas matplotlib seaborn scikit-learn
```

### Step 4: Verify Installation

```bash
# Check SUMO
sumo --version

# Check Python packages
python3 -c "import numpy, pandas, sklearn; print('All packages OK')"

# Check SUMO_HOME
echo $SUMO_HOME
```

---

## Common Issues & Solutions

### Issue 1: "SUMO_HOME not set"

**Error:**
```
Please declare environment variable 'SUMO_HOME'
```

**Solution:**
```bash
# Find SUMO installation
which sumo

# Set SUMO_HOME (example for Ubuntu)
export SUMO_HOME=/usr/share/sumo

# Make permanent
echo 'export SUMO_HOME=/usr/share/sumo' >> ~/.bashrc
```

---

### Issue 2: "netconvert not found"

**Error:**
```
netconvert: command not found
```

**Solution:**
```bash
# Install SUMO tools
sudo apt-get install sumo-tools

# Or add to PATH
export PATH="$PATH:$SUMO_HOME/tools"
```

---

### Issue 3: "Module 'traci' not found"

**Error:**
```python
ModuleNotFoundError: No module named 'traci'
```

**Solution:**
```bash
# Add SUMO tools to Python path
export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"

# Or install via pip
pip3 install traci
```

---

### Issue 4: "Permission denied: ./run.sh"

**Error:**
```
bash: ./run.sh: Permission denied
```

**Solution:**
```bash
chmod +x run.sh
./run.sh --help
```

---

### Issue 5: Network file missing

**Error:**
```
Error loading network file: highway.net.xml
```

**Solution:**
```bash
# Build network manually
cd sumo-scenario/maps
netconvert --node-files=highway.nod.xml \
           --edge-files=highway.edg.xml \
           --output-file=highway.net.xml

# Or run setup
./run.sh --setup
```

---

### Issue 6: Matplotlib display issues

**Error:**
```
_tkinter.TclError: no display name and no $DISPLAY environment variable
```

**Solution:**
```bash
# Use non-interactive backend
export MPLBACKEND=Agg

# Or install TK
sudo apt-get install python3-tk
```

---

### Issue 7: Insufficient RAM

**Symptom:**
Simulation crashes or becomes very slow

**Solution:**
```bash
# Reduce simulation duration
./run.sh --simulate --duration 500

# Or reduce vehicle count
# Edit sumo-scenario/routes/traffic.rou.xml
# Lower the 'number' attributes in <flow> elements
```

---

## Verification Checklist

Run these commands to verify everything is working:

```bash
# 1. SUMO installed?
sumo --version
✓ Should show: Eclipse SUMO Version X.X.X

# 2. SUMO_HOME set?
echo $SUMO_HOME
✓ Should show path like: /usr/share/sumo

# 3. Python packages?
python3 -c "import numpy, pandas, sklearn, matplotlib; print('OK')"
✓ Should print: OK

# 4. TraCI available?
python3 -c "import traci; print('OK')"
✓ Should print: OK

# 5. Network file exists?
ls sumo-scenario/maps/highway.net.xml
✓ Should show the file

# 6. Run script executable?
./run.sh --help
✓ Should show help message
```

---

## Performance Optimization

### For Faster Simulation

1. **Disable GUI:**
   Edit `scripts/sumo_controller.py`:
   ```python
   sumo_cmd = ["sumo", "-c", self.sumo_config]  # Remove "-gui"
   ```

2. **Reduce Step Resolution:**
   Edit `sumo-scenario/simulation.sumocfg`:
   ```xml
   <step-length value="0.5"/>  <!-- Increase from 0.1 -->
   ```

3. **Limit Vehicles:**
   ```bash
   ./run.sh --simulate --duration 300  # Shorter simulation
   ```

---

## Advanced Configuration

### Custom RSU Placement

Edit `sumo-scenario/configs/rsu_locations.add.xml`:

```xml
<poi id="RSU_CUSTOM" x="3500.0" y="-50.0" color="0,255,0" type="rsu">
    <param key="coverage_radius" value="600"/>  <!-- Increase coverage -->
</poi>
```

### Adjust Detection Threshold

Edit `scripts/sumo_controller.py`:

```python
# In process_reports_at_rsus()
if trust_score < 0.3:  # Change threshold here
    self.detected_fake_reports.append(report)
```

### Custom ML Features

Edit `ml-detection/train_model.py`:

```python
def extract_features(self, report_data):
    # Add your features here
    custom_feature = report_data.get('your_metric', 0)
    features.append(custom_feature)
```

---

## Getting Help

If problems persist:

1. **Check Logs:**
   ```bash
   cat sumo-scenario/results/simulation_stats.csv
   ```

2. **Run in Debug Mode:**
   ```bash
   python3 -u scripts/sumo_controller.py 2>&1 | tee debug.log
   ```

3. **Verify SUMO Works:**
   ```bash
   cd sumo-scenario
   sumo-gui -c simulation.sumocfg
   ```

4. **Test Individual Components:**
   ```bash
   # Test ML only
   python3 ml-detection/train_model.py
   
   # Test analysis only
   python3 analysis/generate_reports.py
   ```

---

## System Requirements

### Minimum:
- CPU: 2 cores
- RAM: 4 GB
- Disk: 2 GB free
- OS: Linux/macOS/WSL

### Recommended:
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 5 GB free
- GPU: Not required

---

## Quick Fix Script

Save this as `fix_common_issues.sh`:

```bash
#!/bin/bash

echo "Fixing common IVIRS issues..."

# Fix permissions
chmod +x run.sh
chmod +x scripts/*.py
chmod +x ml-detection/*.py
chmod +x analysis/*.py

# Set SUMO_HOME
if [ -z "$SUMO_HOME" ]; then
    echo 'export SUMO_HOME=/usr/share/sumo' >> ~/.bashrc
    export SUMO_HOME=/usr/share/sumo
fi

# Add SUMO tools to PATH
if [ -d "$SUMO_HOME/tools" ]; then
    echo 'export PATH="$PATH:$SUMO_HOME/tools"' >> ~/.bashrc
    export PATH="$PATH:$SUMO_HOME/tools"
fi

# Install missing packages
pip3 install --user numpy pandas matplotlib seaborn scikit-learn 2>/dev/null

# Build network if missing
if [ ! -f "sumo-scenario/maps/highway.net.xml" ]; then
    cd sumo-scenario/maps
    netconvert --node-files=highway.nod.xml \
               --edge-files=highway.edg.xml \
               --output-file=highway.net.xml 2>/dev/null || echo "Install netconvert"
    cd ../..
fi

echo "Done! Run: source ~/.bashrc"
echo "Then try: ./run.sh --help"
```

Run it:
```bash
chmod +x fix_common_issues.sh
./fix_common_issues.sh
```

---

**Still stuck? Check README.md or review the code comments for more details.**
