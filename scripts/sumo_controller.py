#!/usr/bin/env python3
"""
IVIRS SUMO-NS3 Integration Controller
Manages vehicle behavior, incident detection, and communication with NS-3
"""

import os
import sys
import random
import json
import time
import math
from collections import defaultdict
from datetime import datetime

# Add SUMO tools to path
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci
import sumolib

# Import NS-3 network simulator
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ns3-simulation'))
try:
    from ns3_v2x_simulation import NS3NetworkSimulator
    NS3_AVAILABLE = True
except ImportError:
    NS3_AVAILABLE = False
    print("[WARNING] NS-3 simulator not available, using simplified network model")

class RSU:
    def __init__(self, rsu_id, x, y, coverage_radius=500):
        self.id = rsu_id
        self.x = x
        self.y = y
        self.coverage_radius = coverage_radius
        self.reports_received = []
        self.vehicles_in_range = set()
        
    def is_in_range(self, veh_x, veh_y):
        distance = math.sqrt((veh_x - self.x)**2 + (veh_y - self.y)**2)
        return distance <= self.coverage_radius
    
    def receive_report(self, report):
        self.reports_received.append(report)
        return True

class IncidentReport:
    def __init__(self, vehicle_id, report_type, location, timestamp, is_fake=False):
        self.vehicle_id = vehicle_id
        self.report_type = report_type
        self.location = location
        self.timestamp = timestamp
        self.is_fake = is_fake
        self.witnesses = []
        self.rsu_id = None
        self.validated = False
        self.trust_score = 0.5
        
    def to_dict(self):
        return {
            'vehicle_id': self.vehicle_id,
            'report_type': self.report_type,
            'location': self.location,
            'timestamp': self.timestamp,
            'is_fake': self.is_fake,
            'witnesses': self.witnesses,
            'rsu_id': self.rsu_id,
            'validated': self.validated,
            'trust_score': self.trust_score
        }

class VehicleTrustManager:
    def __init__(self):
        self.trust_scores = defaultdict(lambda: 0.5)
        
    def update_trust(self, vehicle_id, report_validated, report_fake):
        current_trust = self.trust_scores[vehicle_id]
        if report_validated and not report_fake:
            self.trust_scores[vehicle_id] = min(1.0, current_trust + 0.1)
        elif report_fake:
            self.trust_scores[vehicle_id] = max(0.0, current_trust - 0.3)
        return self.trust_scores[vehicle_id]
    
    def get_trust_score(self, vehicle_id):
        return self.trust_scores[vehicle_id]

class IVIRSController:
    def __init__(self, sumo_config, output_dir="results"):
        self.sumo_config = sumo_config
        self.output_dir = output_dir
        self.step_count = 0
        
        if NS3_AVAILABLE:
            self.ns3_network = NS3NetworkSimulator()
        else:
            self.ns3_network = None
        
        self.rsus = {
            0: RSU(0, 0, -50, 500),
            1: RSU(1, 2000, -50, 500),
            2: RSU(2, 4000, -50, 500),
            3: RSU(3, 6000, -50, 500),
            4: RSU(4, 8000, -50, 500),
            5: RSU(5, 10000, -50, 500)
        }
        
        self.trust_manager = VehicleTrustManager()
        self.all_reports = []
        self.real_incidents = []
        self.fake_reports = []
        self.detected_fake_reports = []
        self.emergency_vehicles = set()
        self.malicious_vehicles = set()
        self.honest_vehicles = set()
        self.vehicle_positions = {}
        self.vehicle_speeds = {}
        
        self.stats = {
            'total_reports': 0,
            'fake_reports': 0,
            'real_incidents': 0,
            'detected_fakes': 0,
            'false_positives': 0,
            'emergency_dispatches': 0
        }
        
        self.reports_file = open(f"{output_dir}/incident_reports.json", "w")
        self.stats_file = open(f"{output_dir}/simulation_stats.csv", "w")
        self.stats_file.write("timestamp,total_vehicles,total_reports,fake_reports,detected_fakes,detection_accuracy\n")
        
    def start_simulation(self):
        # Force GUI mode
        sumo_cmd = ["sumo-gui", "-c", self.sumo_config, "--start", "--quit-on-end"]
        traci.start(sumo_cmd)
        print(f"[IVIRS] Simulation started at {datetime.now()}")
        
    def simulation_step(self):
        traci.simulationStep()
        self.step_count += 1
        current_time = traci.simulation.getTime()
        
        vehicle_ids = traci.vehicle.getIDList()
        
        # CRITICAL FIX: Clear old vehicle data to prevent "Vehicle Unknown" errors
        self.vehicle_positions = {}
        self.vehicle_speeds = {}
        
        for veh_id in vehicle_ids:
            try:
                pos = traci.vehicle.getPosition(veh_id)
                speed = traci.vehicle.getSpeed(veh_id)
                self.vehicle_positions[veh_id] = pos
                self.vehicle_speeds[veh_id] = speed
                
                # Check parameters only if we haven't already marked them
                if veh_id not in self.malicious_vehicles:
                    try:
                        if traci.vehicle.getParameter(veh_id, "is_malicious") == "true":
                            self.malicious_vehicles.add(veh_id)
                    except: pass
                
                if veh_id not in self.honest_vehicles:
                    try:
                        if traci.vehicle.getParameter(veh_id, "is_honest_reporter") == "true":
                            self.honest_vehicles.add(veh_id)
                    except: pass
            except traci.TraCIException:
                continue # Skip vehicles that leave during processing

        self.detect_real_incidents(current_time)
        self.generate_fake_reports(current_time)
        self.update_rsu_coverage()
        self.process_reports_at_rsus()
        self.dispatch_emergency_services(current_time)
        
        if self.step_count % 100 == 0:
            self.update_statistics(current_time, len(vehicle_ids))
        
        return current_time < 1000
    
    def detect_real_incidents(self, current_time):
        # Safely iterate only over currently active vehicles
        for veh_id in list(self.vehicle_positions.keys()):
            try:
                if traci.vehicle.getParameter(veh_id, "will_breakdown") == "true":
                    breakdown_time = float(traci.vehicle.getParameter(veh_id, "breakdown_time"))
                    if abs(current_time - breakdown_time) < 0.5:
                        self.create_real_incident(veh_id, "breakdown", current_time)
                
                if traci.vehicle.getParameter(veh_id, "will_crash") == "true":
                    crash_time = float(traci.vehicle.getParameter(veh_id, "crash_time"))
                    if abs(current_time - crash_time) < 0.5:
                        self.create_real_incident(veh_id, "accident", current_time)
            except:
                continue
    
    def create_real_incident(self, veh_id, incident_type, current_time):
        if veh_id not in self.vehicle_positions: return
        pos = self.vehicle_positions[veh_id]
        incident = IncidentReport(veh_id, incident_type, pos, current_time, is_fake=False)
        self.real_incidents.append(incident)
        
        try:
            if incident_type == "breakdown":
                traci.vehicle.setSpeed(veh_id, 0)
                traci.vehicle.setColor(veh_id, (255, 0, 0))
            elif incident_type == "accident":
                traci.vehicle.setSpeed(veh_id, 0)
                traci.vehicle.setColor(veh_id, (255, 100, 0))
        except: pass
        
        for witness_id in self.honest_vehicles:
            if witness_id in self.vehicle_positions:
                witness_pos = self.vehicle_positions[witness_id]
                dist = math.sqrt((pos[0]-witness_pos[0])**2 + (pos[1]-witness_pos[1])**2)
                if dist < 200:
                    report = IncidentReport(witness_id, incident_type, pos, current_time, is_fake=False)
                    incident.witnesses.append(witness_id)
                    self.submit_report_to_rsu(report)
        
        print(f"[REAL INCIDENT] {incident_type} at {pos} by {veh_id}")
        self.stats['real_incidents'] += 1
    
    def generate_fake_reports(self, current_time):
        for mal_veh in self.malicious_vehicles:
            if mal_veh not in self.vehicle_positions: continue
            
            try:
                fake_time = float(traci.vehicle.getParameter(mal_veh, "fake_report_time"))
                if abs(current_time - fake_time) < 0.5:
                    pos = self.vehicle_positions[mal_veh]
                    fake_x = pos[0] + random.uniform(-500, 500)
                    fake_y = pos[1] + random.uniform(-200, 200)
                    fake_location = (fake_x, fake_y)
                    report_type = traci.vehicle.getParameter(mal_veh, "fake_report_type")
                    
                    fake_report = IncidentReport(mal_veh, report_type, fake_location, current_time, is_fake=True)
                    self.fake_reports.append(fake_report)
                    self.submit_report_to_rsu(fake_report)
                    
                    traci.vehicle.setColor(mal_veh, (255, 0, 255))
                    print(f"[FAKE REPORT] {report_type} by {mal_veh}")
                    self.stats['fake_reports'] += 1
            except: continue
    
    def submit_report_to_rsu(self, report):
        reporter_pos = report.location
        nearest_rsu = None
        min_dist = float('inf')
        
        for rsu in self.rsus.values():
            dist = math.sqrt((reporter_pos[0]-rsu.x)**2 + (reporter_pos[1]-rsu.y)**2)
            if dist < min_dist and dist <= rsu.coverage_radius:
                min_dist = dist
                nearest_rsu = rsu
        
        if nearest_rsu:
            report.rsu_id = nearest_rsu.id
            nearest_rsu.receive_report(report)
            self.all_reports.append(report)
            self.stats['total_reports'] += 1
            return True
        return False
    
    def update_rsu_coverage(self):
        for rsu in self.rsus.values():
            rsu.vehicles_in_range.clear()
        for veh_id, pos in self.vehicle_positions.items():
            for rsu in self.rsus.values():
                if rsu.is_in_range(pos[0], pos[1]):
                    rsu.vehicles_in_range.add(veh_id)
    
    def process_reports_at_rsus(self):
        for rsu in self.rsus.values():
            for report in rsu.reports_received[:]:
                if not report.validated:
                    trust_score = self.validate_report(report, rsu)
                    report.trust_score = trust_score
                    report.validated = True
                    
                    if trust_score < 0.3:
                        self.detected_fake_reports.append(report)
                        self.stats['detected_fakes'] += 1
                        self.trust_manager.update_trust(report.vehicle_id, True, True)
                        print(f"[FAKE DETECTED] From {report.vehicle_id}")
                    else:
                        self.trust_manager.update_trust(report.vehicle_id, True, False)
    
    def validate_report(self, report, rsu):
        trust_score = 0.5
        reporter_trust = self.trust_manager.get_trust_score(report.vehicle_id)
        trust_score += 0.3 * (reporter_trust - 0.5)
        
        witness_count = len(report.witnesses)
        if witness_count >= 2: trust_score += 0.4
        elif witness_count == 1: trust_score += 0.2
        else: trust_score -= 0.2
        
        if report.vehicle_id in self.vehicle_positions:
            actual_pos = self.vehicle_positions[report.vehicle_id]
            dist = math.sqrt((actual_pos[0]-report.location[0])**2 + (actual_pos[1]-report.location[1])**2)
            if dist < 100: trust_score += 0.2
            elif dist > 500: trust_score -= 0.3
            
        return max(0.0, min(1.0, trust_score))
    
    def dispatch_emergency_services(self, current_time):
        for report in self.all_reports:
            if report.validated and report.trust_score >= 0.7:
                if report.vehicle_id not in self.emergency_vehicles:
                    self.emergency_vehicles.add(report.vehicle_id)
                    self.stats['emergency_dispatches'] += 1
    
    def update_statistics(self, current_time, num_vehicles):
        if self.stats['total_reports'] > 0:
            detection_accuracy = (self.stats['detected_fakes'] / self.stats['fake_reports'] if self.stats['fake_reports'] > 0 else 0)
        else:
            detection_accuracy = 0
        
        self.stats_file.write(f"{current_time:.1f},{num_vehicles},{self.stats['total_reports']},{self.stats['fake_reports']},{self.stats['detected_fakes']},{detection_accuracy:.3f}\n")
        print(f"[STATS @ {current_time:.0f}s] Vehicles: {num_vehicles}, Detected Fakes: {self.stats['detected_fakes']}")
    
    def finalize_simulation(self):
        reports_data = {
            'all_reports': [r.to_dict() for r in self.all_reports],
            'statistics': self.stats
        }
        json.dump(reports_data, self.reports_file, indent=2)
        self.reports_file.close()
        self.stats_file.close()
        traci.close()
        print("SIMULATION COMPLETED SUCCESSFULLY")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sumo_config = os.path.join(base_dir, "../sumo-scenario/simulation.sumocfg")
    output_dir = os.path.join(base_dir, "../sumo-scenario/results")
    os.makedirs(output_dir, exist_ok=True)
    
    controller = IVIRSController(sumo_config, output_dir)
    controller.start_simulation()
    
    try:
        while controller.simulation_step():
            pass
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        controller.finalize_simulation()

if __name__ == "__main__":
    main()
