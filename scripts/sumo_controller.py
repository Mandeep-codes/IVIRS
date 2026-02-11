#!/usr/bin/env python3
"""
IVIRS SUMO Controller
Features: Emergency Dispatch, Visual Markers, Truck Error Fixes
"""
import os
import sys
import random
import json
import time
import math
from collections import defaultdict
from datetime import datetime

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci

class RSU:
    def __init__(self, rsu_id, x, y, coverage_radius=500):
        self.id = rsu_id
        self.x = x
        self.y = y
        self.coverage_radius = coverage_radius
        self.reports_received = []
        self.vehicles_in_range = set()
    def is_in_range(self, veh_x, veh_y):
        return math.sqrt((veh_x - self.x)**2 + (veh_y - self.y)**2) <= self.coverage_radius
    def receive_report(self, report):
        self.reports_received.append(report)

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
            'vehicle_id': self.vehicle_id, 'report_type': self.report_type,
            'location': self.location, 'timestamp': self.timestamp,
            'is_fake': self.is_fake, 'witnesses': self.witnesses,
            'rsu_id': self.rsu_id, 'validated': self.validated,
            'trust_score': self.trust_score
        }

class VehicleTrustManager:
    def __init__(self):
        self.trust_scores = defaultdict(lambda: 0.5)
    def update_trust(self, vehicle_id, report_validated, report_fake):
        current = self.trust_scores[vehicle_id]
        if report_validated and not report_fake:
            self.trust_scores[vehicle_id] = min(1.0, current + 0.1)
        elif report_fake:
            self.trust_scores[vehicle_id] = max(0.0, current - 0.3)
        return self.trust_scores[vehicle_id]
    def get_trust_score(self, vehicle_id):
        return self.trust_scores[vehicle_id]

class IVIRSController:
    def __init__(self, output_dir="results"):
        self.output_dir = output_dir
        self.step_count = 0
        self.rsus = {
            0: RSU(0, 0, -50, 500), 1: RSU(1, 2000, -50, 500),
            2: RSU(2, 4000, -50, 500), 3: RSU(3, 6000, -50, 500),
            4: RSU(4, 8000, -50, 500), 5: RSU(5, 10000, -50, 500)
        }
        self.trust_manager = VehicleTrustManager()
        self.all_reports = []
        self.real_incidents = []
        self.fake_reports = []
        self.detected_fake_reports = []
        self.emergency_vehicles = set()
        self.spawned_emergency_ids = set()
        
        self.malicious_vehicles = set()
        self.honest_vehicles = set()
        self.vehicle_positions = {}
        
        self.stats = {'total_reports': 0, 'fake_reports': 0, 'real_incidents': 0, 'detected_fakes': 0, 'emergency_dispatches': 0}
        self.reports_file = open(f"{output_dir}/incident_reports.json", "w")
        self.stats_file = open(f"{output_dir}/simulation_stats.csv", "w")
        self.stats_file.write("timestamp,total_vehicles,total_reports,fake_reports,detected_fakes\n")

    def start_simulation(self):
        print("[IVIRS] Connecting to SUMO on port 8813...")
        traci.init(port=8813)
        print(f"[IVIRS] Connected! Simulation starting...")

    def simulation_step(self):
        try:
            traci.simulationStep()
        except traci.TraCIException:
            return False

        self.step_count += 1
        current_time = traci.simulation.getTime()
        
        # --- CRITICAL FIX: CLEANUP STALE VEHICLES ---
        vehicle_ids = set(traci.vehicle.getIDList())
        self.malicious_vehicles.intersection_update(vehicle_ids)
        self.honest_vehicles.intersection_update(vehicle_ids)
        self.vehicle_positions.clear()
        
        for veh_id in vehicle_ids:
            try:
                self.vehicle_positions[veh_id] = traci.vehicle.getPosition(veh_id)
                if veh_id not in self.malicious_vehicles and veh_id not in self.honest_vehicles:
                    if traci.vehicle.getParameter(veh_id, "is_malicious") == "true":
                        self.malicious_vehicles.add(veh_id)
                    elif traci.vehicle.getParameter(veh_id, "is_honest_reporter") == "true":
                        self.honest_vehicles.add(veh_id)
            except: continue

        self.detect_real_incidents(current_time)
        self.generate_fake_reports(current_time)
        self.update_rsu_coverage()
        self.process_reports_at_rsus()
        self.dispatch_emergency_services(current_time)
        
        if self.step_count % 100 == 0:
            self.update_statistics(current_time, len(vehicle_ids))
        return current_time < 1000

    def detect_real_incidents(self, current_time):
        for veh_id in list(self.vehicle_positions.keys()):
            try:
                if traci.vehicle.getParameter(veh_id, "will_breakdown") == "true":
                    if abs(current_time - float(traci.vehicle.getParameter(veh_id, "breakdown_time"))) < 0.5:
                        self.create_real_incident(veh_id, "breakdown", current_time)
                if traci.vehicle.getParameter(veh_id, "will_crash") == "true":
                    if abs(current_time - float(traci.vehicle.getParameter(veh_id, "crash_time"))) < 0.5:
                        self.create_real_incident(veh_id, "accident", current_time)
            except: continue

    def create_real_incident(self, veh_id, type, time):
        if veh_id not in self.vehicle_positions: return
        pos = self.vehicle_positions[veh_id]
        incident = IncidentReport(veh_id, type, pos, time, False)
        self.real_incidents.append(incident)
        
        try:
            traci.vehicle.setSpeed(veh_id, 0)
            color = (255, 0, 0) if type == "breakdown" else (255, 100, 0)
            traci.vehicle.setColor(veh_id, color)
        except: pass
        
        # Create Visual Marker
        self.create_incident_marker(pos, type)
        
        for wit in self.honest_vehicles:
            if wit in self.vehicle_positions:
                dist = math.sqrt((pos[0]-self.vehicle_positions[wit][0])**2 + (pos[1]-self.vehicle_positions[wit][1])**2)
                if dist < 200:
                    report = IncidentReport(wit, type, pos, time, False)
                    incident.witnesses.append(wit)
                    self.submit_report(report)
        print(f"🚨 [REAL INCIDENT] {type} at {pos}")
        self.stats['real_incidents'] += 1

    def create_incident_marker(self, location, type):
        color = (255, 0, 0, 255) if type == "accident" else (255, 165, 0, 255)
        try:
            traci.poi.add(f"inc_{int(traci.simulation.getTime())}", location[0], location[1], color, "circle", 200, 40, 40)
        except: pass

    def generate_fake_reports(self, current_time):
        for mal in list(self.malicious_vehicles):
            if mal not in self.vehicle_positions: continue
            try:
                if abs(current_time - float(traci.vehicle.getParameter(mal, "fake_report_time"))) < 0.5:
                    pos = self.vehicle_positions[mal]
                    fake_pos = (pos[0] + random.uniform(-500,500), pos[1] + random.uniform(-200,200))
                    type = traci.vehicle.getParameter(mal, "fake_report_type")
                    report = IncidentReport(mal, type, fake_pos, current_time, True)
                    self.fake_reports.append(report)
                    self.submit_report(report)
                    traci.vehicle.setColor(mal, (255, 0, 255))
                    print(f"⚠️  [FAKE REPORT] {type} injected by {mal}")
                    self.stats['fake_reports'] += 1
            except: continue

    def submit_report(self, report):
        best_rsu = None
        min_dist = float('inf')
        for rsu in self.rsus.values():
            dist = math.sqrt((report.location[0]-rsu.x)**2 + (report.location[1]-rsu.y)**2)
            if dist < min_dist and dist <= rsu.coverage_radius:
                min_dist = dist
                best_rsu = rsu
        if best_rsu:
            report.rsu_id = best_rsu.id
            best_rsu.receive_report(report)
            self.all_reports.append(report)
            self.stats['total_reports'] += 1

    def update_rsu_coverage(self):
        for rsu in self.rsus.values(): rsu.vehicles_in_range.clear()
        for vid, pos in self.vehicle_positions.items():
            for rsu in self.rsus.values():
                if rsu.is_in_range(pos[0], pos[1]): rsu.vehicles_in_range.add(vid)

    def process_reports_at_rsus(self):
        for rsu in self.rsus.values():
            for rep in rsu.reports_received:
                if not rep.validated:
                    trust = self.validate(rep)
                    rep.trust_score = trust
                    rep.validated = True
                    if trust < 0.3:
                        self.detected_fake_reports.append(rep)
                        self.stats['detected_fakes'] += 1
                        self.trust_manager.update_trust(rep.vehicle_id, True, True)
                        print(f"❌ [FAKE DETECTED] Blocked report from {rep.vehicle_id}")
                    else:
                        self.trust_manager.update_trust(rep.vehicle_id, True, False)

    def validate(self, rep):
        score = 0.5 + 0.3 * (self.trust_manager.get_trust_score(rep.vehicle_id) - 0.5)
        score += 0.4 if len(rep.witnesses) >= 2 else (0.2 if len(rep.witnesses) == 1 else -0.2)
        if rep.vehicle_id in self.vehicle_positions:
            dist = math.sqrt((self.vehicle_positions[rep.vehicle_id][0]-rep.location[0])**2 + (self.vehicle_positions[rep.vehicle_id][1]-rep.location[1])**2)
            score += 0.2 if dist < 100 else (-0.3 if dist > 500 else 0)
        return max(0.0, min(1.0, score))

    def dispatch_emergency_services(self, time):
        for rep in self.all_reports:
            if rep.validated and rep.trust_score >= 0.7:
                key = f"{rep.vehicle_id}_{rep.timestamp}"
                if key not in self.emergency_vehicles:
                    self.emergency_vehicles.add(key)
                    self.stats['emergency_dispatches'] += 1
                    print(f"🚑 [DISPATCH] Emergency sent to {rep.location}")

    def update_statistics(self, time, count):
        print(f"[STATS @ {time:.0f}s] Vehicles: {count}, Reports: {self.stats['total_reports']}, Detected Fakes: {self.stats['detected_fakes']}")
        self.stats_file.write(f"{time},{count},{self.stats['total_reports']},{self.stats['fake_reports']},{self.stats['detected_fakes']}\n")

    def finalize(self):
        json.dump({'reports': [r.to_dict() for r in self.all_reports]}, self.reports_file, indent=2)
        self.reports_file.close()
        self.stats_file.close()
        traci.close()
        print("SIMULATION FINISHED.")

def main():
    os.makedirs("results", exist_ok=True)
    c = IVIRSController("results")
    c.start_simulation()
    try:
        while c.simulation_step(): pass
    except KeyboardInterrupt: print("Stopped.")
    finally: c.finalize()

if __name__ == "__main__":
    main()
