import time
import os
import psutil
import random
from datetime import datetime
import socket
import json

class DummyService:
    def __init__(self):
        self.node_id = os.environ.get('NODE_ID', '0')
        self.pid = os.getpid()
        self.start_time = datetime.now()
        
        # State that should persist across migrations
        self.processed_items = 0
        self.work_queue = [f"task_{i}" for i in range(100)]
        self.completed_tasks = []
        self.transaction_log = []
        
        # Record migration history
        self.migration_history = []
        self.original_node = self.node_id
        
        # Create state file to track our existence
        self.state_file = f"/tmp/dummy_service_state_{self.pid}.json"
        self.save_state()
        
    def save_state(self):
        """Save state to a file"""
        state = {
            'pid': self.pid,
            'node_id': self.node_id,
            'original_node': self.original_node,
            'start_time': self.start_time.isoformat(),
            'processed_items': self.processed_items,
            'remaining_tasks': len(self.work_queue),
            'completed_tasks': len(self.completed_tasks),
            'migration_history': self.migration_history,
            'hostname': socket.gethostname()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f)
            
    def process_task(self):
        """Process a task from the queue"""
        if not self.work_queue:
            return "No tasks available"
            
        task = self.work_queue.pop(0)
        
        # Simulate CPU work
        for _ in range(random.randint(1000000, 2000000)):
            _ = random.random() ** 2
            
        # Simulate memory allocation
        temp_list = [1] * random.randint(100, 1000)
        
        # Record completion
        self.completed_tasks.append(task)
        self.processed_items += 1
        
        # Log the transaction
        transaction = {
            'task': task,
            'timestamp': datetime.now().isoformat(),
            'node_id': self.node_id,
            'pid': self.pid
        }
        self.transaction_log.append(transaction)
        
        return f"Processed {task}"
        
    def do_work(self):
        """Simulates work with varying CPU and memory usage"""
        result = self.process_task()
        
        # Update state file periodically
        if self.processed_items % 10 == 0:
            self.save_state()
            
        # Detect if we've been migrated
        current_node = os.environ.get('NODE_ID', '0')
        current_hostname = socket.gethostname()
        
        if current_node != self.node_id:
            print(f"Migration detected! From node {self.node_id} to {current_node}")
            self.migration_history.append({
                'from_node': self.node_id,
                'to_node': current_node,
                'timestamp': datetime.now().isoformat(),
                'processed_items_before_migration': self.processed_items
            })
            self.node_id = current_node
            self.save_state()
        
        time.sleep(0.1)
        return result
        
    def run(self):
        print(f"Starting dummy service on node {self.node_id} with PID {self.pid}")
        print(f"State file location: {self.state_file}")
        
        while True:
            try:
                result = self.do_work()
                
                # Log some metrics
                cpu_percent = psutil.Process(self.pid).cpu_percent()
                mem_info = psutil.Process(self.pid).memory_info()
                
                print(f"Node {self.node_id} - PID {self.pid} - CPU: {cpu_percent}% MEM: {mem_info.rss / 1024 / 1024:.2f}MB - Tasks: {len(self.completed_tasks)}/{self.processed_items + len(self.work_queue)} - Result: {result}")
                
            except Exception as e:
                print(f"Error in dummy service: {e}")
                time.sleep(1)

if __name__ == "__main__":
    service = DummyService()
    service.run() 