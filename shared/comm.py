import zmq
import json
import threading
import time
import os
from datetime import datetime

class NodeCommunicator:
    def __init__(self, node_id, peers=None):
        self.node_id = str(node_id)
        self.peers = peers or [f"node{i}" for i in range(1, 4) if str(i) != self.node_id]
        self.context = zmq.Context()
        
        # Publisher for broadcasting messages
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(f"tcp://*:555{self.node_id}")
        
        # Subscriber for receiving messages
        self.subscriber = self.context.socket(zmq.SUB)
        for peer in self.peers:
            peer_id = peer[-1]
            self.subscriber.connect(f"tcp://{peer}:555{peer_id}")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Callback registry for message handling
        self.callbacks = {
            'FAULT': [],
            'RECOVERY': [],
            'MIGRATION': []
        }
        
        # Start listener thread
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen)
        self.listener_thread.daemon = True
        self.listener_thread.start()
    
    def register_callback(self, message_type, callback_func):
        """Register a callback function for a specific message type"""
        if message_type in self.callbacks:
            self.callbacks[message_type].append(callback_func)
        else:
            self.callbacks[message_type] = [callback_func]
    
    def broadcast_message(self, message_type, data):
        """Broadcast a message to all peers"""
        message = {
            'type': message_type,
            'source': self.node_id,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self.publisher.send_json(message)
        return message
    
    def _listen(self):
        """Listen for messages from other nodes"""
        while self.running:
            try:
                message = self.subscriber.recv_json()
                self._handle_message(message)
            except Exception as e:
                print(f"Error in listener: {e}")
                time.sleep(0.1)
    
    def _handle_message(self, message):
        """Handle incoming messages"""
        if message['source'] == self.node_id:
            return
            
        print(f"Node {self.node_id} received message: {message}")
        
        message_type = message['type']
        
        # Default handlers
        if message_type == 'FAULT':
            print(f"Fault detected on node {message['source']}: {message['data']}")
            
            # Special handling for migration requests
            if message['data'].get('type') == 'force_migration':
                self._handle_migration_request(message)
                
        elif message_type == 'RECOVERY':
            print(f"Recovery action from node {message['source']}: {message['data']}")
            
            # Special handling for checkpoint operations
            action = message['data'].get('action')
            if action == 'checkpoint_created':
                print(f"Checkpoint created on node {message['source']} at {message['data'].get('location')}")
            elif action == 'checkpoint_transferred':
                print(f"Checkpoint transferred from node {message['data'].get('source_node')} to {message['data'].get('target_node')}")
            elif action == 'service_restored':
                print(f"Service restored on node {message['source']} from checkpoint {message['data'].get('checkpoint_dir')}")
        
        # Execute registered callbacks
        if message_type in self.callbacks:
            for callback in self.callbacks[message_type]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"Error in callback: {e}")
    
    def _handle_migration_request(self, message):
        """Handle a request to migrate a process"""
        # This is a placeholder - actual migration is handled by the recovery manager
        # but we log the request here for visibility
        print(f"Migration request received for process on node {message['data'].get('node_id')}")
    
    def close(self):
        """Clean shutdown"""
        self.running = False
        time.sleep(0.5)  # Allow time for thread to close
        self.publisher.close()
        self.subscriber.close()
        self.context.term()

if __name__ == "__main__":
    # Test code
    import os
    node_id = os.environ.get('NODE_ID', '1')
    comm = NodeCommunicator(node_id)
    
    def on_fault(message):
        print(f"FAULT CALLBACK: {message}")
    
    def on_recovery(message):
        print(f"RECOVERY CALLBACK: {message}")
    
    comm.register_callback('FAULT', on_fault)
    comm.register_callback('RECOVERY', on_recovery)
    
    try:
        while True:
            comm.broadcast_message('HEARTBEAT', {'status': 'alive'})
            time.sleep(5)
    except KeyboardInterrupt:
        comm.close() 