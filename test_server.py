import pyaudio
import socket

TCP_IP = "0.0.0.0"
TCP_PORT = 8888

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((TCP_IP, TCP_PORT))

serversocket.listen(1)

print(f"Server listening on {TCP_IP}:{TCP_PORT}")
connection, client_address = serversocket.accept()

p = pyaudio.PyAudio()
stream = p.open(format=32, channels=1, rate=8000, output=True)

try:
    while True:
        data = connection.recv(800)
        stream.write(data)

except KeyboardInterrupt:
    print("Finalizado com Ctrl+C")
    stream.stop_stream()
    stream.close()
    p.terminate()
