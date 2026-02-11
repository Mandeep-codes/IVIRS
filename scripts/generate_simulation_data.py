#!/usr/bin/env python3
"""
IVIRS Simulation Data Generator (SUMO-Independent)
Generates realistic simulation data without requiring SUMO to run
"""

import json
import csv
import random
import math
from datetime import datetime
import os

class SimulationDataGenerator:
    """Generate realistic vehicular incident data without SUMO"""
    
    def __init__(self, duration=1000, output_dir="sumo-scenario/results"):
        self.duration = duration
        self.output_dir = output_dir
        self.current_time = 0
        
        # Simulation parameters
        self.num_vehicles = 200
        self.num_rsus = 6
        self.fake_ratio = 0.3
        
        # Statistics
        self.stats = {
            'total_reports': 0,
            'fake_reports': 0,
            'real_incidents': 0,
            'detected_fakes': 0,
            'false_positives': 0,
            'emergency_dispatches': 0
        }
        
        # Report storage
        self.all_reports = []
        self.real_incidents = []
        self.fake_reports = []
        self.detected_fake_reports = []
        
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_vehicle_position(self):
        """Generate random vehicle position on highway"""
        x = random.uniform(0, 10000)  # 10km highway
        y = random.uniform(-50, 50)   # 4 lanes
        return (x, y)
    
    def find_nearest_rsu(self, position):
        """Find nearest RSU to position"""
        rsu_positions = [0, 2000, 4000, 6000, 8000, 10000]
        min_dist = float('inf')
        nearest = 0
        
        for i, rsu_x in enumerate(rsu_positions):
            dist = abs(position[0] - rsu_x)
            if dist < min_dist:
                min_dist = dist
                nearest = i
        
        return nearest
    
    def generate_real_incident(self, time):
        """Generate a real incident"""
        vehicle_id = f"incident_car_{random.randint(1, 100)}"
        incident_type = random.choice(["accident", "breakdown", "hazard"])
        location = self.generate_vehicle_position()
        
        # Generate witnesses (2-4 for real incidents)
        witness_count = random.randint(2, 4)
        witnesses = [f"witness_{random.randint(1, 1000)}" for _ in range(witness_count)]
        
        # High trust for real reports
        trust_score = random.uniform(0.7, 1.0)
        
        report = {
            'vehicle_id': vehicle_id,
            'report_type': incident_type,
            'location': location,
            'timestamp': time,
            'is_fake': False,
            'witnesses': witnesses,
            'rsu_id': self.find_nearest_rsu(location),
            'validated': True,
            'trust_score': trust_score
        }
        
        self.real_incidents.append(report)
        self.all_reports.append(report)
        self.stats['real_incidents'] += 1
        self.stats['total_reports'] += 1
        
        return report
    
    def generate_fake_report(self, time):
        """Generate a fake report"""
        vehicle_id = f"malicious_{random.randint(1, 100)}"
        report_type = random.choice(["accident", "breakdown", "hazard"])
        
        # Fake location (offset from reporter)
        actual_pos = self.generate_vehicle_position()
        fake_offset = random.uniform(100, 800)
        fake_location = (
            actual_pos[0] + random.choice([-1, 1]) * fake_offset,
            actual_pos[1] + random.uniform(-100, 100)
        )
        
        # Few or no witnesses for fake reports
        witness_count = 0 if random.random() < 0.7 else 1
        witnesses = [f"fake_witness_{random.randint(1, 100)}" for _ in range(witness_count)]
        
        # Low trust for fake reports
        trust_score = random.uniform(0.0, 0.4)
        
        report = {
            'vehicle_id': vehicle_id,
            'report_type': report_type,
            'location': fake_location,
            'timestamp': time,
            'is_fake': True,
            'witnesses': witnesses,
            'rsu_id': self.find_nearest_rsu(fake_location),
            'validated': True,
            'trust_score': trust_score
        }
        
        self.fake_reports.append(report)
        self.all_reports.append(report)
        self.stats['fake_reports'] += 1
        self.stats['total_reports'] += 1
        
        # Detection (92% accuracy)
        if trust_score < 0.3 or random.random() < 0.92:
            self.detected_fake_reports.append(report)
            self.stats['detected_fakes'] += 1
        
        return report
    
    def run_simulation(self):
        """Run the simulation and generate data"""
        print(f"[SIM] Generating {self.duration}s of simulation data...")
        print(f"[SIM] Target: ~{int(self.duration / 10)} incidents")
        
        stats_file = open(f"{self.output_dir}/simulation_stats.csv", "w")
        stats_writer = csv.writer(stats_file)
        stats_writer.writerow([
            "timestamp", "total_vehicles", "total_reports", 
            "fake_reports", "detected_fakes", "detection_accuracy"
        ])
        
        # Generate incidents throughout simulation
        incident_times = sorted([random.uniform(50, self.duration - 50) 
                                for _ in range(int(self.duration / 10))])
        
        for time in incident_times:
            if random.random() < self.fake_ratio:
                # Generate fake report
                report = self.generate_fake_report(time)
                print(f"[FAKE REPORT] {report['report_type']} at {report['location']} "
                      f"by {report['vehicle_id']} at time {time:.1f}s")
            else:
                # Generate real incident
                report = self.generate_real_incident(time)
                print(f"[REAL INCIDENT] {report['report_type']} at {report['location']} "
                      f"by {report['vehicle_id']} at time {time:.1f}s")
            
            # Emergency dispatch for validated reports with high trust
            if report['trust_score'] >= 0.7:
                self.stats['emergency_dispatches'] += 1
                print(f"[EMERGENCY DISPATCH] Response to {report['location']}")
            
            # Write statistics every 10 incidents
            if len(self.all_reports) % 10 == 0:
                accuracy = (self.stats['detected_fakes'] / self.stats['fake_reports'] 
                           if self.stats['fake_reports'] > 0 else 0)
                stats_writer.writerow([
                    time, self.num_vehicles, self.stats['total_reports'],
                    self.stats['fake_reports'], self.stats['detected_fakes'],
                    accuracy
                ])
                
                print(f"\n[STATS @ {time:.0f}s] Reports: {self.stats['total_reports']}, "
                      f"Fake: {self.stats['fake_reports']}, "
                      f"Detected: {self.stats['detected_fakes']}, "
                      f"Accuracy: {accuracy:.2%}\n")
        
        stats_file.close()
        
        # Save all reports to JSON
        reports_data = {
            'all_reports': self.all_reports,
            'real_incidents': self.real_incidents,
            'fake_reports': self.fake_reports,
            'detected_fake_reports': self.detected_fake_reports,
            'statistics': self.stats
        }
        
        with open(f"{self.output_dir}/incident_reports.json", "w") as f:
            json.dump(reports_data, f, indent=2)
        
        # Print final statistics
        print("\n" + "="*60)
        print("SIMULATION COMPLETED")
        print("="*60)
        print(f"Total Reports: {self.stats['total_reports']}")
        print(f"Real Incidents: {self.stats['real_incidents']}")
        print(f"Fake Reports: {self.stats['fake_reports']}")
        print(f"Detected Fake Reports: {self.stats['detected_fakes']}")
        
        if self.stats['fake_reports'] > 0:
            detection_rate = self.stats['detected_fakes'] / self.stats['fake_reports']
            print(f"Detection Rate: {detection_rate:.2%}")
        
        print(f"Emergency Dispatches: {self.stats['emergency_dispatches']}")
        print("="*60)
        
        print(f"\n[SIM] Data saved to {self.output_dir}/")
        print(f"  - incident_reports.json")
        print(f"  - simulation_stats.csv")

def main():
    print("="*60)
    print("IVIRS Simulation Data Generator")
    print("(SUMO-Independent Mode)")
    print("="*60)
    print()
    
    generator = SimulationDataGenerator(duration=1000)
    generator.run_simulation()
    
    print("\n✅ Simulation data generated successfully!")
    print("\nNext step: Run analysis")
    print("  python3 analysis/generate_reports.py")

if __name__ == "__main__":
    main()
