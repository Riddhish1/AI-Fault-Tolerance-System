import os
import subprocess
import psutil
import zmq
import json
import tarfile
import io
import base64
import shutil
from comm import NodeCommunicator
import time
import threading

class RecoveryManager:
    def __init__(self):
        self.node_id = os.environ.get('NODE_ID', '1')
        self.communicator = NodeCommunicator(self.node_id)
        self.context = zmq.Context()
        
        # Socket for direct file transfers
        self.transfer_socket = self.context.socket(zmq.REP)
        self.transfer_socket.bind(f"tcp://*:666{self.node_id}")
        
        # Start transfer listener thread
        self.transfer_thread = threading.Thread(target=self._handle_transfers)
        self.transfer_thread.daemon = True
        self.transfer_thread.start()
        
    def simulate_checkpoint(self, pid):
        """Simulate creating a checkpoint of the process (no CRIU)"""
        try:
            checkpoint_dir = f"/tmp/checkpoint_{self.node_id}_{pid}"
            os.makedirs(checkpoint_dir, exist_ok=True)
            
            # Save process info to the checkpoint
            process = psutil.Process(pid)
            process_info = {
                'pid': pid,
                'node_id': self.node_id,
                'creation_time': process.create_time(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'cmdline': process.cmdline(),
                'checkpoint_time': time.time()
            }
            
            with open(f"{checkpoint_dir}/process_info.json", 'w') as f:
                json.dump(process_info, f)
            
            self.communicator.broadcast_message('RECOVERY', {
                'action': 'checkpoint_created',
                'pid': pid,
                'location': checkpoint_dir
            })
            
            return checkpoint_dir
        except Exception as e:
            print(f"Error creating checkpoint: {e}")
            return None
            
    def simulate_restore(self, checkpoint_dir):
        """Simulate restoring a process from checkpoint (no CRIU)"""
        try:
            # Read the process info
            with open(f"{checkpoint_dir}/process_info.json", 'r') as f:
                process_info = json.load(f)
            
            # Start a new dummy service process
            subprocess.Popen(['python3', '/app/shared/dummy_service.py'])
            
            self.communicator.broadcast_message('RECOVERY', {
                'action': 'service_restored',
                'checkpoint_dir': checkpoint_dir
            })
            
            return True
        except Exception as e:
            print(f"Error restoring service: {e}")
            return False
            
    def restart_service(self):
        """Restart the dummy service"""
        try:
            subprocess.Popen(['python3', '/app/shared/dummy_service.py'])
            
            self.communicator.broadcast_message('RECOVERY', {
                'action': 'service_restarted'
            })
            
            return True
        except Exception as e:
            print(f"Error restarting service: {e}")
            return False
    
    def transfer_checkpoint_to_node(self, checkpoint_dir, target_node):
        """Transfer a checkpoint to another node"""
        try:
            # Create a tarfile of the checkpoint directory
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
                tar.add(checkpoint_dir, arcname=os.path.basename(checkpoint_dir))
            
            # Connect to the target node's transfer socket
            socket = self.context.socket(zmq.REQ)
            socket.connect(f"tcp://{target_node}:666{target_node[-1]}")
            
            # Send the tarfile
            tar_data = tar_buffer.getvalue()
            encoded_data = base64.b64encode(tar_data).decode('utf-8')
            
            socket.send_json({
                'action': 'transfer_checkpoint',
                'source_node': self.node_id,
                'checkpoint_name': os.path.basename(checkpoint_dir),
                'data': encoded_data
            })
            
            # Wait for response
            response = socket.recv_json()
            socket.close()
            
            self.communicator.broadcast_message('RECOVERY', {
                'action': 'checkpoint_transferred',
                'source_node': self.node_id,
                'target_node': target_node,
                'checkpoint_dir': checkpoint_dir,
                'success': response.get('success', False)
            })
            
            return response.get('success', False)
        except Exception as e:
            print(f"Error transferring checkpoint: {e}")
            return False
    
    def _handle_transfers(self):
        """Handle incoming checkpoint transfers"""
        while True:
            try:
                message = self.transfer_socket.recv_json()
                
                if message.get('action') == 'transfer_checkpoint':
                    # Extract the checkpoint data
                    encoded_data = message.get('data', '')
                    checkpoint_name = message.get('checkpoint_name', '')
                    source_node = message.get('source_node', '')
                    
                    # Decode the data
                    tar_data = base64.b64decode(encoded_data)
                    tar_buffer = io.BytesIO(tar_data)
                    
                    # Extract to local directory
                    checkpoint_dir = f"/tmp/{checkpoint_name}"
                    os.makedirs(checkpoint_dir, exist_ok=True)
                    with tarfile.open(fileobj=tar_buffer, mode='r:gz') as tar:
                        tar.extractall(path="/tmp")
                    
                    self.transfer_socket.send_json({
                        'success': True,
                        'checkpoint_dir': checkpoint_dir
                    })
                    
                    # Automatically restore the service
                    self.simulate_restore(checkpoint_dir)
                else:
                    self.transfer_socket.send_json({'success': False, 'error': 'Unknown action'})
            except Exception as e:
                print(f"Error in transfer handler: {e}")
                try:
                    self.transfer_socket.send_json({'success': False, 'error': str(e)})
                except:
                    pass
    
    def get_available_nodes(self):
        """Get a list of available nodes based on resource usage"""
        available_nodes = []
        
        # Check each node except this one
        for i in range(1, 4):
            if str(i) == self.node_id:
                continue
                
            node_name = f"node{i}"
            # We could implement a more sophisticated check here, but for now we'll
            # just assume all other nodes are available
            available_nodes.append(node_name)
            
        return available_nodes
            
    def monitor_and_recover(self):
        """Monitor the dummy service and recover if needed"""
        while True:
            try:
                # Find dummy service process
                dummy_service_pid = None
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    if 'python' in proc.info['name'] and 'dummy_service.py' in str(proc.info['cmdline']):
                        dummy_service_pid = proc.info['pid']
                        break
                
                if not dummy_service_pid:
                    print("Dummy service not found, restarting...")
                    self.restart_service()
                else:
                    # Check resource usage
                    process = psutil.Process(dummy_service_pid)
                    cpu_percent = process.cpu_percent(interval=1)
                    mem_percent = process.memory_percent()
                    
                    if cpu_percent > 90 or mem_percent > 90:
                        print(f"High resource usage detected: CPU={cpu_percent}%, MEM={mem_percent}%")
                        
                        # Create a simulated checkpoint of the current process
                        checkpoint_dir = self.simulate_checkpoint(dummy_service_pid)
                        
                        if checkpoint_dir:
                            # Find an available node to transfer the process to
                            available_nodes = self.get_available_nodes()
                            
                            if available_nodes:
                                # Transfer the checkpoint to the first available node
                                target_node = available_nodes[0]
                                print(f"Transferring process to {target_node}...")
                                
                                # Kill the process on this node
                                process.kill()
                                
                                # Transfer the checkpoint
                                success = self.transfer_checkpoint_to_node(checkpoint_dir, target_node)
                                
                                if success:
                                    print(f"Successfully transferred process to {target_node}")
                                else:
                                    print(f"Failed to transfer process, restoring locally")
                                    self.simulate_restore(checkpoint_dir)
                            else:
                                print("No available nodes found, restoring locally")
                                self.simulate_restore(checkpoint_dir)
                
            except Exception as e:
                print(f"Error in monitor_and_recover: {e}")
            
            time.sleep(5)
    
    def cleanup(self):
        """Clean up resources"""
        self.communicator.close()
        self.transfer_socket.close()
        self.context.term()

if __name__ == "__main__":
    recovery = RecoveryManager()
    try:
        recovery.monitor_and_recover()
    except KeyboardInterrupt:
        recovery.cleanup() 