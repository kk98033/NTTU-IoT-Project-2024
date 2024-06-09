import socket
import threading
import base64
import hashlib
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_SIZE = 256

# WebSocket 握手
def handshake(conn):
    request = conn.recv(1024).decode('utf-8')
    headers = request.split('\r\n')
    for header in headers:
        if header.startswith('Sec-WebSocket-Key'):
            key = header.split(': ')[1]
            break

    accept = base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode('utf-8')).digest()).decode('utf-8')
    response = (
        'HTTP/1.1 101 Switching Protocols\r\n'
        'Upgrade: websocket\r\n'
        'Connection: Upgrade\r\n'
        f'Sec-WebSocket-Accept: {accept}\r\n\r\n'
    )
    conn.send(response.encode('utf-8'))

# 解析 WebSocket 負載數據
def decode_frame(data):
    payload_length = data[1] & 127
    if payload_length == 126:
        mask = data[4:8]
        payload = data[8:]
    elif payload_length == 127:
        mask = data[10:14]
        payload = data[14:]
    else:
        mask = data[2:6]
        payload = data[6:]

    decoded = bytearray([payload[i] ^ mask[i % 4] for i in range(len(payload))])
    return decoded

# 處理客戶端連接
def handle_client(conn, addr, stream):
    print(f"New connection: {addr}")
    handshake(conn)
    audio_buffer = bytearray()
    
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            decoded_data = decode_frame(data)
            audio_buffer.extend(decoded_data)
            
            # 如果累積的數據超過一定長度，播放音頻
            if len(audio_buffer) >= BUFFER_SIZE * 2:
                audio_data = np.frombuffer(audio_buffer[:BUFFER_SIZE * 2], dtype=np.int16)
                audio_buffer = audio_buffer[BUFFER_SIZE * 2:]  # 清空已處理部分的緩衝區
                print(f"Playing audio data of length: {len(audio_data)}")
                print(f"Audio data: {audio_data[:10]}")
                audio_data = audio_data.astype(np.int16)
                stream.write(audio_data)
        except Exception as e:
            print(f"Error: {e}")
            break
    conn.close()
    print(f"Connection closed: {addr}")

def start_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server listening on {host}:{port}")

    # 使用 sounddevice 創建持續流
    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16') as stream:
        while True:
            conn, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, stream))
            client_thread.start()

if __name__ == "__main__":
    start_server('0.0.0.0', 5000)
