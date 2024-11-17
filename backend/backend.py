from gevent import monkey
monkey.patch_all()

import logging
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import time
import datetime
import pylsl
import threading
import subprocess
import os

# Suppress verbose logging from libraries
logging.getLogger('bleak').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.ERROR)

# Initialize Flask and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")

# Function to log messages with timestamps
def log_message(message):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {message}")

# Function to handle the Muse data stream
def muse_data_stream(duration, sid):
    log_message("Starting Muse data stream...")
    try:
        # Use the full path to muselsl
        muselsl_path = '/opt/anaconda3/bin/muselsl'

        # Start the muselsl stream process
        stream_process = subprocess.Popen(
            [muselsl_path, 'stream'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()  # Copy the environment variables
        )
        log_message("Started muselsl stream process.")

        # Read and log the output from muselsl stream process
        def log_stream_output(process):
            for line in process.stdout:
                log_message(f"[muselsl stream] {line.strip()}")

        # Start a thread to read stdout
        stdout_thread = threading.Thread(target=log_stream_output, args=(stream_process,))
        stdout_thread.start()

        # Give the stream some time to initialize
        time.sleep(5)

        # Connect to the LSL stream
        streams = pylsl.resolve_byprop('type', 'EEG', timeout=15)
        if not streams:
            log_message("No EEG stream available.")
            # Terminate the stream process
            stream_process.terminate()
            stream_process.wait()
            socketio.emit('muse_connection_error', {'error': 'No EEG stream available.'}, to=sid)
            return

        inlet = pylsl.StreamInlet(streams[0])
        log_message("Connected to EEG stream.")
        socketio.emit('muse_connected', {}, to=sid)
        log_message("Emitted 'muse_connected' event to client.")

        # Start timing after Muse is connected
        start_time = time.time()
        while (time.time() - start_time) < duration:
            sample, timestamp = inlet.pull_sample()
            socketio.emit('new_eeg_data', {'data': sample}, to=sid)
            log_message(f"Emitted 'new_eeg_data' event: {sample}")
            socketio.sleep(0.01)  # Yield to the event loop

        log_message("Data streaming completed.")

        # Terminate the stream process
        stream_process.terminate()
        stream_process.wait()
        socketio.emit('recording_finished', {}, to=sid)
        log_message("Emitted 'recording_finished' event to client.")

    except Exception as e:
        log_message(f"Error during Muse streaming: {e}")
        socketio.emit('muse_connection_error', {'error': str(e)}, to=sid)

# Function to handle start recording event
@socketio.on('start_recording')
def handle_start_recording(message):
    duration = int(message['duration'])
    log_message(f"Received start recording command for duration: {duration} seconds")
    sid = request.sid
    log_message(f"Client SID: {sid}")

    # Start the Muse data stream in a background task
    socketio.start_background_task(target=muse_data_stream, duration=duration, sid=sid)
    log_message("Started Muse data stream in background task.")

# Define a route to serve the index page
@app.route('/')
def index():
    log_message("Serving the index page...")
    return render_template('index.html')

# Start the Flask server
if __name__ == '__main__':
    log_message("Starting the Flask server on port 5001...")
    try:
        socketio.run(app, host='0.0.0.0', port=5001, debug=False)
    except Exception as e:
        log_message(f"Error while starting the server: {e}")
