from flask import Flask, send_from_directory, render_template_string, request
from flask_socketio import SocketIO, emit
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>WebSocket Music Player</title>
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#000000">
        <link rel="icon" href="/path/to/icon.png">
      </head>
      <body>
        <h1>Music Player</h1>
        <audio id="audioPlayer" controls>
          <source id="audioSource" src="/speech.mp3" type="audio/mpeg">
          Your browser does not support the audio element.
        </audio>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.min.js"></script>
        <script>
          var socket = io.connect('http://' + document.domain + ':' + location.port);
          var silentAudio = '/silent.mp3'; // 無聲音頻的路徑

          socket.on('connect', function() {
            console.log('WebSocket connection established');
          });

          socket.on('new_audio', function(data) {
            console.log('New audio file available');
            var audioPlayer = document.getElementById('audioPlayer');
            var audioSource = document.getElementById('audioSource');
            audioSource.src = data.file + '?rand=' + Math.random(); // 防止緩存
            audioPlayer.load();
            audioPlayer.play().then(() => {
              console.log('Audio playing');
            }).catch(error => {
              console.error('Error playing audio:', error);
            });
          });

          // 當音頻播放結束後，播放無聲音頻
          document.getElementById('audioPlayer').addEventListener('ended', function() {
            var audioPlayer = document.getElementById('audioPlayer');
            var audioSource = document.getElementById('audioSource');
            audioSource.src = silentAudio;
            audioPlayer.load();
            audioPlayer.play().then(() => {
              console.log('Silent audio playing');
            }).catch(error => {
              console.error('Error playing silent audio:', error);
            });
          });

          if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
              navigator.serviceWorker.register('/service-worker.js').then(function(registration) {
                console.log('Service Worker registered with scope:', registration.scope);
              }, function(err) {
                console.log('Service Worker registration failed:', err);
              });
            });
          }
        </script>
      </body>
    </html>
    ''')

@app.route('/<filename>')
def get_audio(filename):
    return send_from_directory('.', filename)

@app.route('/switch_audio', methods=['POST'])
def switch_audio():
    file = request.json.get('file')
    if file:
        notify_new_audio(file)
        return 'OK', 200
    else:
        return 'Bad Request', 400


def notify_new_audio(file):
    with app.app_context():
        print(f"Notifying clients of new audio file: {file}")
        socketio.emit('new_audio', {'file': file})

def audio_switcher():
    files = ["speech.mp3", "output.mp3"]
    while True:
        for file in files:
            time.sleep(10)  # 切換音頻文件的間隔時間
            notify_new_audio(file)

if __name__ == '__main__':
    # threading.Thread(target=audio_switcher, daemon=True).start()
    print("Starting Flask server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
