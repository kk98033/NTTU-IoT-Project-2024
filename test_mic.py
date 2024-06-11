import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model
import argparse
import threading
import queue
import socket
import os
import time

# Print the current directory
current_directory = os.getcwd()
print(f"Current Directory: {current_directory}")

# Change to the desired directory
os.chdir('NTTU-IoT-Project-2024')
new_directory = os.getcwd()
print(f"New Directory: {new_directory}")

# Parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--chunk_size",
    help="How much audio (in number of samples) to predict on at once",
    type=int,
    default=1280,
    required=False
)
parser.add_argument(
    "--model_path",
    help="The path of a specific model to load",
    type=str,
    default="model/hey_Hikari.onnx",  # Set the default model path to your model
    required=False
)
parser.add_argument(
    "--inference_framework",
    help="The inference framework to use (either 'onnx' or 'tflite')",
    type=str,
    default='onnx',  # Set the default inference framework to 'onnx'
    required=False
)

args = parser.parse_args()

# Load pre-trained openwakeword models
if args.model_path != "":
    owwModel = Model(wakeword_models=[args.model_path], inference_framework=args.inference_framework)
else:
    owwModel = Model(inference_framework=args.inference_framework)

n_models = len(owwModel.models.keys())

# Queue for audio data
audio_queue = queue.Queue()

# Function to read from the ESP32
def read_esp32_audio():
    TCP_IP = "0.0.0.0"
    TCP_PORT = 8888
    BUFFER_SIZE = args.chunk_size  # Make sure this matches with ESP32's buffer size

    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((TCP_IP, TCP_PORT))
    serversocket.listen(1)
    connection, client_address = serversocket.accept()
    print(f"Connection from {client_address}")

    while True:
        try:
            data = connection.recv(BUFFER_SIZE)
            if not data:
                break
            audio_data = np.frombuffer(data, dtype=np.int16)
            audio_queue.put(audio_data)
        except IOError as e:
            print(f"Error reading audio: {e}")
            break
    connection.close()
    serversocket.close()

# Start the ESP32 audio reading thread
audio_thread = threading.Thread(target=read_esp32_audio)
audio_thread.daemon = True
audio_thread.start()

# Setup PyAudio for playback
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True)

# Run capture loop continuously, checking for wakewords
if __name__ == "__main__":
    # Generate output string header
    print("\n\n")
    print("#" * 100)
    print("Listening for wakewords...")
    print("#" * 100)
    print("\n" * (n_models * 3))

    while True:
        # Get audio from the queue
        if not audio_queue.empty():
            audio_data = audio_queue.get()

            # Debug: Check if there is sound
            audio_level = np.abs(audio_data).mean()

            # Play audio data
            # stream.write(audio_data.tobytes())

            # Feed to openWakeWord model
            prediction = owwModel.predict(audio_data)

            # Column titles
            n_spaces = 16
            output_string_header = f"""
Model Name         | Score | Wakeword Status | Audio Level
-----------------------------------------------------------
Audio Level        |       |                 | {audio_level:.2f}
"""

            for mdl in owwModel.prediction_buffer.keys():
                # Add scores in formatted table
                scores = list(owwModel.prediction_buffer[mdl])
                curr_score = format(scores[-1], '.20f').replace("-", "")

                output_string_header += f"""{mdl}{" " * (n_spaces - len(mdl))}   | {curr_score[0:5]} | {"--" + " " * 20 if scores[-1] <= 0.5 else "Wakeword Detected!"}
"""

            # Print results table
            print("\033c", end='')  # Clear the console
            print(output_string_header)
            time.sleep(1)  # Adjust sleep time as needed

# Cleanup PyAudio
stream.stop_stream()
stream.close()
p.terminate()
