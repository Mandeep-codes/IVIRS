#!/usr/bin/env python3
"""
IVIRS NS-3 Network Simulation
V2X Communication with RSU infrastructure
"""

import os
import sys
import json
import random
import math

class NS3NetworkSimulator:
    """
    Simulates V2X network communication for IVIRS
    Models vehicle-to-RSU communication with realistic parameters
    """
    
    def __init__(self):
        self.rsu_positions = [
            (0, -50), (2000, -50), (4000, -50),
            (6000, -50), (8000, -50), (10000, -50)
        ]
        self.rsu_coverage = 500  # meters
        self.v2x_frequency = 5.9  # GHz (DSRC/ITS-G5)
        self.transmission_power = 20  # dBm
        
        # Network performance metrics
        self.packet_delivery_ratio = []
        self.latencies = []
        self.throughputs = []
        
    def calculate_distance(self, pos1, pos2):
        """Calculate Euclidean distance"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def calculate_path_loss(self, distance):
        """
        Calculate path loss using free space model
        PL(d) = 20*log10(d) + 20*log10(f) + 20*log10(4π/c)
        """
        if distance < 1:
            distance = 1
        freq_mhz = self.v2x_frequency * 1000
        path_loss = 20 * math.log10(distance) + 20 * math.log10(freq_mhz) + 32.44
        return path_loss
    
    def calculate_received_power(self, distance):
        """Calculate received signal power"""
        path_loss = self.calculate_path_loss(distance)
        received_power = self.transmission_power - path_loss
        return received_power
    
    def calculate_snr(self, distance):
        """Calculate Signal-to-Noise Ratio"""
        noise_floor = -95  # dBm (typical for DSRC)
        received_power = self.calculate_received_power(distance)
        snr = received_power - noise_floor
        return max(0, snr)
    
    def calculate_packet_success_rate(self, snr):
        """Calculate packet delivery success based on SNR"""
        # Simplified model: higher SNR = higher success rate
        if snr > 20:
            return 0.99
        elif snr > 15:
            return 0.95
        elif snr > 10:
            return 0.85
        elif snr > 5:
            return 0.70
        else:
            return 0.50
    
    def simulate_transmission(self, vehicle_pos, report_data):
        """
        Simulate V2X transmission from vehicle to nearest RSU
        Returns transmission metrics
        """
        # Find nearest RSU
        nearest_rsu = None
        min_distance = float('inf')
        
        for i, rsu_pos in enumerate(self.rsu_positions):
            distance = self.calculate_distance(vehicle_pos, rsu_pos)
            if distance < min_distance:
                min_distance = distance
                nearest_rsu = i
        
        # Check if in coverage
        in_coverage = min_distance <= self.rsu_coverage
        
        if not in_coverage:
            return {
                'success': False,
                'reason': 'out_of_coverage',
                'distance': min_distance,
                'rsu_id': nearest_rsu
            }
        
        # Calculate network metrics
        snr = self.calculate_snr(min_distance)
        packet_success = self.calculate_packet_success_rate(snr)
        
        # Simulate transmission
        success = random.random() < packet_success
        
        # Calculate latency (1-way)
        # Propagation delay + processing delay
        propagation_delay = min_distance / 3e8 * 1000  # ms (speed of light)
        processing_delay = random.uniform(2, 5)  # ms
        latency = propagation_delay + processing_delay
        
        # Calculate throughput (simplified)
        # DSRC can support up to 27 Mbps, but effective is lower
        if snr > 20:
            throughput = random.uniform(15, 20)  # Mbps
        elif snr > 15:
            throughput = random.uniform(10, 15)
        elif snr > 10:
            throughput = random.uniform(5, 10)
        else:
            throughput = random.uniform(1, 5)
        
        # Store metrics
        if success:
            self.packet_delivery_ratio.append(1)
            self.latencies.append(latency)
            self.throughputs.append(throughput)
        else:
            self.packet_delivery_ratio.append(0)
        
        return {
            'success': success,
            'rsu_id': nearest_rsu,
            'distance': min_distance,
            'snr': snr,
            'latency_ms': latency,
            'throughput_mbps': throughput,
            'packet_success_rate': packet_success,
            'received_power_dbm': self.calculate_received_power(min_distance)
        }
    
    def get_network_statistics(self):
        """Get overall network performance statistics"""
        if not self.packet_delivery_ratio:
            return None
        
        avg_pdr = sum(self.packet_delivery_ratio) / len(self.packet_delivery_ratio)
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        avg_throughput = sum(self.throughputs) / len(self.throughputs) if self.throughputs else 0
        
        return {
            'packet_delivery_ratio': avg_pdr,
            'average_latency_ms': avg_latency,
            'average_throughput_mbps': avg_throughput,
            'total_transmissions': len(self.packet_delivery_ratio),
            'successful_transmissions': sum(self.packet_delivery_ratio)
        }
    
    def save_results(self, output_file="ns3-simulation/results/network_metrics.json"):
        """Save network simulation results"""
        stats = self.get_network_statistics()
        
        if stats:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"[NS-3] Network statistics saved to {output_file}")
            print(f"[NS-3] PDR: {stats['packet_delivery_ratio']:.2%}")
            print(f"[NS-3] Avg Latency: {stats['average_latency_ms']:.2f} ms")
            print(f"[NS-3] Avg Throughput: {stats['average_throughput_mbps']:.2f} Mbps")

def main():
    """Standalone NS-3 simulation"""
    print("="*60)
    print("IVIRS NS-3 Network Simulation")
    print("="*60)
    
    ns3_sim = NS3NetworkSimulator()
    
    # Simulate some transmissions
    print("\nSimulating V2X transmissions...")
    
    for i in range(100):
        # Random vehicle position
        veh_x = random.uniform(0, 10000)
        veh_y = random.uniform(-50, 50)
        
        result = ns3_sim.simulate_transmission((veh_x, veh_y), {})
        
        if result['success']:
            print(f"✓ Transmission {i+1}: RSU-{result['rsu_id']}, "
                  f"SNR={result['snr']:.1f}dB, Latency={result['latency_ms']:.2f}ms")
        else:
            print(f"✗ Transmission {i+1}: Failed ({result.get('reason', 'poor_signal')})")
    
    print()
    ns3_sim.save_results()
    
    print("\n✅ NS-3 simulation completed")

if __name__ == "__main__":
    main()
