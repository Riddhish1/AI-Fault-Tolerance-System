import os
import random
import subprocess
import psutil
import json
import sys
from comm import NodeCommunicator
import time

class FaultSimulator:
    def __init__(self):
        self.node_id = os.environ.get('NODE_ID', '1')
        self.communicator = NodeCommunicator(self.node_id)
        
    def simulate_cpu_stress(self, duration=30):
        """Simulate high CPU usage using stress-ng"""
        try:
            cores = psutil.cpu_count()
            subprocess.Popen(['stress-ng', '--cpu', str(cores), '--timeout', str(duration)])
            self.communicator.broadcast_message('FAULT', {
                'type': 'cpu_stress',
                'cores': cores,
                'duration': duration
            })
            print(f"Simulating CPU stress on node {self.node_id} for {duration} seconds")
        except Exception as e:
            print(f"Error simulating CPU stress: {e}")
            
    def simulate_memory_leak(self, size_mb=500, duration=30):
        """Simulate memory leak"""
        try:
            # Allocate memory in chunks
            chunk_size = size_mb * 1024 * 1024 // 10  # Convert to bytes
            data = []
            
            self.communicator.broadcast_message('FAULT', {
                'type': 'memory_leak',
                'size_mb': size_mb,
                'duration': duration
            })
            
            print(f"Simulating memory leak on node {self.node_id}: {size_mb}MB over {duration} seconds")
            for _ in range(10):
                data.append(bytearray(chunk_size))
                time.sleep(duration / 10)
                
            # Clean up
            del data
            
        except Exception as e:
            print(f"Error simulating memory leak: {e}")
            
    def kill_dummy_service(self):
        """Kill the dummy service process"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'python' in proc.info['name'] and 'dummy_service.py' in str(proc.info['cmdline']):
                    pid = proc.info['pid']
                    proc.kill()
                    self.communicator.broadcast_message('FAULT', {
                        'type': 'process_kill',
                        'pid': pid
                    })
                    print(f"Killed dummy service process {pid} on node {self.node_id}")
                    break
            else:
                print("No dummy service process found to kill")
        except Exception as e:
            print(f"Error killing dummy service: {e}")
    
    def simulate_node_failure(self):
        """Simulate a node failure (without actually crashing the container)"""
        try:
            # First, capture the current state to help with verification
            service_pids = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'python' in proc.info['name'] and 'dummy_service.py' in str(proc.info['cmdline']):
                    service_pids.append(proc.info['pid'])
            
            self.communicator.broadcast_message('FAULT', {
                'type': 'node_failure',
                'node_id': self.node_id,
                'service_pids': service_pids
            })
            
            # Kill all Python processes except this script
            current_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name']):
                if 'python' in proc.info['name'] and proc.info['pid'] != current_pid:
                    try:
                        proc.kill()
                        print(f"Killed process {proc.info['pid']} as part of node failure simulation")
                    except:
                        pass
            
            print(f"Simulated node failure on node {self.node_id}. Services will need to be migrated.")
            
        except Exception as e:
            print(f"Error simulating node failure: {e}")
    
    def force_service_migration(self):
        """Force a service migration"""
        try:
            # Find the dummy service
            dummy_service_pid = None
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'python' in proc.info['name'] and 'dummy_service.py' in str(proc.info['cmdline']):
                    dummy_service_pid = proc.info['pid']
                    break
            
            if not dummy_service_pid:
                print("No dummy service found to migrate")
                return
            
            # Tell the recovery manager to migrate this service
            self.communicator.broadcast_message('FAULT', {
                'type': 'force_migration',
                'pid': dummy_service_pid,
                'node_id': self.node_id
            })
            
            print(f"Requested migration of service with PID {dummy_service_pid} from node {self.node_id}")
            
        except Exception as e:
            print(f"Error forcing service migration: {e}")
            
    def simulate_random_fault(self):
        """Simulate a random fault"""
        fault_type = random.choice(['cpu', 'memory', 'kill', 'node_failure', 'migration'])
        
        if fault_type == 'cpu':
            self.simulate_cpu_stress(duration=random.randint(10, 30))
        elif fault_type == 'memory':
            self.simulate_memory_leak(size_mb=random.randint(100, 500))
        elif fault_type == 'kill':
            self.kill_dummy_service()
        elif fault_type == 'node_failure':
            self.simulate_node_failure()
        else:
            self.force_service_migration()
            
    def show_help(self):
        """Show available fault simulation options"""
        print("\nFault Simulation Options:")
        print("1. CPU Stress         - Simulates high CPU usage")
        print("2. Memory Leak        - Simulates memory pressure")
        print("3. Process Kill       - Kills the dummy service process")
        print("4. Node Failure       - Simulates a complete node failure")
        print("5. Force Migration    - Forces service migration using CRIU")
        print("6. Random Fault       - Randomly selects one of the above")
        print("0. Exit               - Exit this program")
        
    def interactive_mode(self):
        """Run in interactive mode"""
        self.show_help()
        
        while True:
            try:
                choice = input("\nEnter option (0-6, h for help): ").strip().lower()
                
                if choice == 'h':
                    self.show_help()
                elif choice == '0':
                    break
                elif choice == '1':
                    duration = int(input("Enter duration in seconds (10-60): "))
                    self.simulate_cpu_stress(duration=min(max(10, duration), 60))
                elif choice == '2':
                    size = int(input("Enter memory size in MB (100-1000): "))
                    self.simulate_memory_leak(size_mb=min(max(100, size), 1000))
                elif choice == '3':
                    self.kill_dummy_service()
                elif choice == '4':
                    self.simulate_node_failure()
                elif choice == '5':
                    self.force_service_migration()
                elif choice == '6':
                    self.simulate_random_fault()
                else:
                    print("Invalid option.")
            except Exception as e:
                print(f"Error: {e}")
            
    def cleanup(self):
        """Clean up resources"""
        self.communicator.close()

if __name__ == "__main__":
    simulator = FaultSimulator()
    try:
        if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
            simulator.interactive_mode()
        else:
            simulator.simulate_random_fault()
    finally:
        simulator.cleanup() 