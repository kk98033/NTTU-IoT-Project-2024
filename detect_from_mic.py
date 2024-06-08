# Imports
import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model
import argparse
import threading
import queue

# openwakeword.utils.download_models()

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

# Get microphone stream
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = args.chunk_size
audio = pyaudio.PyAudio()
mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

# Load pre-trained openwakeword models
if args.model_path != "":
    owwModel = Model(wakeword_models=[args.model_path], inference_framework=args.inference_framework)
else:
    owwModel = Model(inference_framework=args.inference_framework)

n_models = len(owwModel.models.keys())

# Queue for audio data
audio_queue = queue.Queue()

# Function to read from the microphone
def read_audio():
    while True:
        try:
            audio_data = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
            audio_queue.put(audio_data)
        except IOError as e:
            print(f"Error reading audio: {e}")

# Start the audio reading thread
audio_thread = threading.Thread(target=read_audio)
audio_thread.daemon = True
audio_thread.start()

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
            # audio_level = np.abs(audio_data).mean()
            # if audio_level > 1000:  # This threshold might need adjusting
            #     print(f"Audio level: {audio_level} (sound detected)")
            # else:
            #     print(f"Audio level: {audio_level} (silence)")

            # Feed to openWakeWord model
            prediction = owwModel.predict(audio_data)

            # Column titles
            n_spaces = 16
            output_string_header = """
                Model Name         | Score | Wakeword Status
                --------------------------------------
                """

            for mdl in owwModel.prediction_buffer.keys():
                # Add scores in formatted table
                scores = list(owwModel.prediction_buffer[mdl])
                curr_score = format(scores[-1], '.20f').replace("-", "")

                output_string_header += f"""{mdl}{" " * (n_spaces - len(mdl))}   | {curr_score[0:5]} | {"--" + " " * 20 if scores[-1] <= 0.5 else "Wakeword Detected!"}
                """

            # Print results table
            print("\033[F" * (4 * n_models + 1))
            print(output_string_header, "                             ", end='\r')
