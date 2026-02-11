# IVIRS Quick Reference Card

## 🚀 Essential Commands

### First Time Setup
```bash
./run.sh --setup
```

### Run Complete Pipeline
```bash
./run.sh --full
```

### Individual Steps
```bash
./run.sh --train-ml      # Train ML models
./run.sh --simulate      # Run SUMO simulation
./run.sh --analyze       # Generate reports
```

### With Custom Parameters
```bash
./run.sh --simulate --duration 500 --fake-ratio 0.4
```

---

## 📂 Important File Locations

| File | Purpose |
|------|---------|
| `analysis/reports/research_report.txt` | Main PhD report |
| `analysis/visualizations/*.png` | All plots |
| `analysis/reports/metrics.json` | Performance metrics |
| `sumo-scenario/results/incident_reports.json` | Raw report data |
| `ml-detection/models/*.pkl` | Trained models |

---

## 🔧 Configuration Files

### Simulation Settings
**File:** `sumo-scenario/simulation.sumocfg`
```xml
<time>
    <begin value="0"/>
    <end value="1000"/>        <!-- Change duration here -->
</time>
```

### Detection Threshold
**File:** `scripts/sumo_controller.py`
```python
if trust_score < 0.3:  # Line ~450, adjust threshold
```

### ML Parameters
**File:** `ml-detection/train_model.py`
```python
n_estimators=200,      # Line ~120, RF trees
learning_rate=0.1,     # Line ~150, GB rate
hidden_layers=(64,32)  # Line ~180, NN architecture
```

---

## 📊 Understanding Output

### Console Output During Simulation

```
[REAL INCIDENT] accident at (4500.0, 0.0) by incident_car_1 at time 250.0s
  ↳ Real incident detected, witness reports generated

[FAKE REPORT] breakdown at (2300.0, -100.0) by malicious_1 at time 180.0s
  ↳ Malicious vehicle sent fake report

[FAKE DETECTED] Report from malicious_1 detected as FAKE (trust: 0.18)
  ↳ System successfully identified fake

[STATS @ 500s] Vehicles: 180, Reports: 45, Fake: 18, Detected: 16, Accuracy: 88.89%
  ↳ Periodic statistics
```

### Key Metrics Explained

- **Detection Rate (Recall)**: % of fake reports caught
- **Precision**: % of detected fakes that are actually fake
- **F1-Score**: Harmonic mean of precision & recall
- **Accuracy**: Overall correct classifications

---

## 🎯 Common Tasks

### Change Simulation Duration
```bash
./run.sh --simulate --duration 2000  # 2000 seconds
```

### Adjust Fake Report Ratio
Edit `sumo-scenario/routes/traffic.rou.xml`:
```xml
<flow id="flow_malicious_fake_reporters" ... number="30"/>
  ↑ Change this number to adjust fake vehicles
```

### Add More RSUs
Edit `sumo-scenario/configs/rsu_locations.add.xml`:
```xml
<poi id="RSU_NEW" x="1000.0" y="-50.0" type="rsu">
    <param key="coverage_radius" value="500"/>
</poi>
```

### Retrain ML Models
```bash
./run.sh --train-ml
```

### Regenerate Reports Only
```bash
./run.sh --analyze
```

---

## 🔍 Debugging

### Check Simulation Logs
```bash
cat sumo-scenario/results/simulation_stats.csv
```

### View All Reports
```bash
cat sumo-scenario/results/incident_reports.json | python3 -m json.tool
```

### Test SUMO Manually
```bash
cd sumo-scenario
sumo-gui -c simulation.sumocfg
```

### Verify Network
```bash
cd sumo-scenario/maps
ls -lh highway.net.xml  # Should exist and be >10KB
```

---

## 📈 Performance Tips

### Faster Simulation
1. Use `sumo` instead of `sumo-gui` (edit `scripts/sumo_controller.py`)
2. Increase step length in `simulation.sumocfg`
3. Reduce vehicle count in `traffic.rou.xml`

### Better Detection
1. Lower threshold in `sumo_controller.py` (line ~450)
2. Increase RSU coverage radius
3. Add more witness validation weight

### More Realistic Traffic
1. Add more vehicle types in `traffic.rou.xml`
2. Increase traffic flows during rush hours
3. Add construction zones or incidents

---

## 🎨 Visualization Outputs

After running analysis, view these files:

```
analysis/visualizations/
├── detection_over_time.png         # Temporal performance
├── accuracy_evolution.png          # Learning over time  
├── performance_metrics.png         # Precision/Recall/F1 bars
├── confusion_matrix.png            # Classification matrix
├── trust_score_distribution.png   # Real vs Fake patterns
└── feature_importance.png          # ML feature weights
```

---

## 🧪 Research Workflow

### Typical PhD Research Cycle

1. **Hypothesis**: "Increasing witness weight improves precision"

2. **Modify Code**:
   ```python
   # In scripts/sumo_controller.py
   if witness_count >= 2:
       trust_score += 0.5  # Increased from 0.4
   ```

3. **Run Experiment**:
   ```bash
   ./run.sh --simulate --duration 1000
   ```

4. **Analyze Results**:
   ```bash
   ./run.sh --analyze
   cat analysis/reports/metrics.json
   ```

5. **Compare**:
   - Check precision/recall trade-off
   - Review visualizations
   - Document in research report

6. **Iterate**: Repeat with different parameters

---

## 📦 Project Components

```
┌─────────────────────────────────────┐
│   Traffic Simulation (SUMO)        │  Generates realistic vehicle behavior
├─────────────────────────────────────┤
│   TraCI Controller (Python)        │  Bridges SUMO ↔ Detection logic
├─────────────────────────────────────┤
│   ML Detection (scikit-learn)      │  Random Forest + Neural Network
├─────────────────────────────────────┤
│   Trust Manager                     │  Reputation scoring system
├─────────────────────────────────────┤
│   RSU Network                       │  6 roadside units, 500m coverage
├─────────────────────────────────────┤
│   Analysis Engine                   │  Metrics + Visualizations + Reports
└─────────────────────────────────────┘
```

---

## 🎓 For Your Thesis

### Include These Sections

1. **Introduction**: Use README.md overview
2. **Related Work**: See docs/REFERENCES.md
3. **Methodology**: From research_report.txt
4. **Results**: All plots from analysis/visualizations/
5. **Discussion**: Metrics interpretation
6. **Conclusion**: From research_report.txt

### Citation
```bibtex
@inproceedings{ivirs2025,
  title={IVIRS: Intelligent Vehicular Incident Reporting System},
  author={Your Name},
  booktitle={IEEE Vehicular Networking Conference},
  year={2025}
}
```

---

## 🆘 Help Commands

```bash
./run.sh --help           # Show all options
cat README.md             # Full documentation
cat docs/INSTALLATION.md  # Setup guide
python3 scripts/sumo_controller.py --help  # Controller options
```

---

## 📞 Quick Fixes

| Problem | Solution |
|---------|----------|
| SUMO not found | `export SUMO_HOME=/usr/share/sumo` |
| Network missing | `./run.sh --setup` |
| Permission denied | `chmod +x run.sh` |
| Python errors | `pip3 install numpy pandas sklearn matplotlib` |
| No visualization | `export MPLBACKEND=Agg` |

---

**Remember**: Every simulation run generates new data. Save important results before re-running!

**Pro Tip**: Create a `results_archive/` folder to backup different experimental runs.

---

*Happy Researching!* 🎓🚗📊
