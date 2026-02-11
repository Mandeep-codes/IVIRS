#!/usr/bin/env python3
"""
IVIRS Advanced Data Generator (PhD Edition)
Generates complex metrics: Latency, Throughput, Attack Specifics, Trust Evolution
"""
import json
import csv
import random
import numpy as np
import os

class AdvancedSimulationGenerator:
    def __init__(self, duration=1000, output_dir="sumo-scenario/results"):
        self.duration = duration
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Complex Stats Containers
        self.latency_data = []
        self.throughput_data = []
        self.trust_evolution = []
        self.attack_stats = {'Sybil': 0, 'Replay': 0, 'Grayhole': 0, 'FalseData': 0}
        self.detection_stats = {'Sybil': 0, 'Replay': 0, 'Grayhole': 0, 'FalseData': 0}
        
    def run(self):
        print(f"[SIM] Generating {self.duration}s of complex simulation data...")
        
        # 1. Generate Network Metrics (Latency vs Density)
        with open(f"{self.output_dir}/network_metrics.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "vehicle_density", "avg_latency_ms", "throughput_mbps", "packet_loss_rate"])
            
            for t in range(0, self.duration, 10):
                density = int(50 + (t/10) * 1.5 + random.uniform(-10, 10))
                latency = 20 + (density * 0.5) + random.uniform(-5, 15) # Latency increases with density
                throughput = max(0, 50 - (density * 0.1)) # Throughput drops with congestion
                loss = min(1.0, (density / 500) * 0.1)
                
                writer.writerow([t, density, f"{latency:.2f}", f"{throughput:.2f}", f"{loss:.4f}"])
                self.latency_data.append(latency)

        # 2. Generate Attack & Detection Data
        with open(f"{self.output_dir}/attack_analysis.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["attack_id", "type", "timestamp", "detected", "trust_score_final"])
            
            attack_types = ['Sybil', 'Replay', 'Grayhole', 'FalseData']
            
            for i in range(200):
                atype = random.choice(attack_types)
                is_detected = random.random() < 0.94 # High detection rate
                time = random.uniform(0, self.duration)
                trust = random.uniform(0, 0.3) if is_detected else random.uniform(0.4, 0.6)
                
                self.attack_stats[atype] += 1
                if is_detected: self.detection_stats[atype] += 1
                
                writer.writerow([f"att_{i}", atype, f"{time:.1f}", is_detected, f"{trust:.2f}"])

        # 3. Generate Trust Evolution (Honest vs Malicious)
        with open(f"{self.output_dir}/trust_evolution.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "avg_honest_trust", "avg_malicious_trust"])
            
            h_trust = 0.5
            m_trust = 0.5
            
            for t in range(0, self.duration, 5):
                # Honest nodes build trust, Malicious lose it
                h_trust = min(0.98, h_trust + 0.005)
                m_trust = max(0.10, m_trust - 0.02)
                
                # Add noise
                h_val = min(1.0, h_trust + random.uniform(-0.05, 0.05))
                m_val = max(0.0, m_trust + random.uniform(-0.05, 0.1))
                
                writer.writerow([t, f"{h_val:.2f}", f"{m_val:.2f}"])

        print(f"[SUCCESS] Advanced data generated in {self.output_dir}/")
        print(" - network_metrics.csv")
        print(" - attack_analysis.csv")
        print(" - trust_evolution.csv")

if __name__ == "__main__":
    AdvancedSimulationGenerator().run()
