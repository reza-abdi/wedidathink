from gevent import monkey
monkey.patch_all()  # Patch the standard library for gevent to work properly

import asyncio
from muselsl import stream, list_muses
from multiprocessing import Process, Queue
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random
import time

# Initialize Flask and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='gevent')

def discover_muses(queue):
    """Function to discover Muse headsets and put the results in a queue."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        muses = loop.run_until_complete(list_muses())
        queue.put(muses)
    except Exception as e:
        print(f"Error during Muse discovery: {e}")
        queue.put([])

def muse_data_stream():
    """Function to start the Muse data stream."""
    queue = Queue()
    process = Process(target=discover_muses, args=(queue,))
    process.start()
    process.join()  # Wait for the process to finish
    muses = queue.get()

    if not muses:
        print("No Muse headsets found.")
        return
    print(f"Connecting to Muse: {muses[0]['name']}")
    stream(muses[0]['address'])

@app.route('/')
def index():
    return render_template('index.html')

# Function to emit EEG data
@socketio.on('start_recording')
def handle_start_recording(message):
    duration = int(message['duration'])
    start_time = time.time()

    # Start a process for the Muse data stream to prevent blocking the event loop
    muse_process = Process(target=muse_data_stream)
    muse_process.start()

    # Emit fake EEG data for demonstration purposes
    while (time.time() - start_time) < duration:
        data_point = random.uniform(0, 100)  # Replace with actual EEG data
        socketio.emit('new_eeg_data', {'data': data_point})
        socketio.sleep(0.5)  # Emit data every 0.5 seconds

    muse_process.join()  # Ensure the process ends correctly

# Start the Flask server
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5005, debug=False)
