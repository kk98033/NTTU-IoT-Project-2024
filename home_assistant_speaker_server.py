from flask import Flask, send_from_directory, render_template_string, request
from flask_socketio import SocketIO, emit
import threading
import time
import re

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
        <link rel="stylesheet" href="https://cdn.plyr.io/3.6.8/plyr.css" />
      </head>
      <body>
        <h1>Music Player</h1>
        <audio id="audioPlayer" controls>
          <source id="audioSource" src="/speech.mp3" type="audio/mpeg">
          Your browser does not support the audio element.
        </audio>
        <div id="youtubePlayer" style="display:none;">
          <video id="youtubeIframe" playsinline controls></video>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.min.js"></script>
        <script src="https://cdn.plyr.io/3.6.8/plyr.polyfilled.js"></script>
        <script>
          var socket = io.connect('http://' + document.domain + ':' + location.port);
          var silentAudio = '/silent.mp3'; // 無聲音頻的路徑
          var player;

          document.addEventListener('DOMContentLoaded', () => {
            player = new Plyr('#youtubeIframe', {
              autoplay: true,
              controls: ['play', 'progress', 'volume', 'fullscreen']
            });

            player.on('ended', function() {
              console.log('Video ended, playing silent audio');
              var audioPlayer = document.getElementById('audioPlayer');
              var audioSource = document.getElementById('audioSource');
              var youtubePlayer = document.getElementById('youtubePlayer');
              youtubePlayer.style.display = 'none';
              audioSource.src = silentAudio;
              audioPlayer.style.display = 'block';
              audioPlayer.load();
              audioPlayer.play().then(() => {
                console.log('Silent audio playing');
              }).catch(error => {
                console.error('Error playing silent audio:', error);
              });
            });
          });

          socket.on('connect', function() {
            console.log('WebSocket connection established');
          });

          socket.on('new_audio', function(data) {
            console.log('New audio file available');
            var audioPlayer = document.getElementById('audioPlayer');
            var audioSource = document.getElementById('audioSource');
            var youtubePlayer = document.getElementById('youtubePlayer');

            if (data.type === 'mp3') {
              if (player) {
                player.stop();
              }
              youtubePlayer.style.display = 'none';
              audioSource.src = data.file + '?rand=' + Math.random(); // 防止緩存
              audioPlayer.style.display = 'block';
              audioPlayer.load();
              audioPlayer.play().then(() => {
                console.log('Audio playing');
              }).catch(error => {
                console.error('Error playing audio:', error);
              });
            } else if (data.type === 'youtube') {
              audioPlayer.pause();
              audioPlayer.style.display = 'none';
              youtubePlayer.style.display = 'block';
              player.source = {
                type: 'video',
                sources: [{
                  src: data.videoId,
                  provider: 'youtube',
                }]
              };
              player.muted = false;
              player.play().then(() => {
                console.log('YouTube video playing');
              }).catch(error => {
                console.error('Error playing YouTube video:', error);
              });
            }
          });

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
    type = request.json.get('type')
    if file and type in ['mp3', 'youtube']:
        notify_new_audio(file, type)
        return 'OK', 200
    else:
        return 'Bad Request', 400

def notify_new_audio(file, type):
    with app.app_context():
        if type == 'mp3':
            print(f"Notifying clients of new audio file: {file}")
            socketio.emit('new_audio', {'file': file, 'type': type})
        elif type == 'youtube':
            video_id = extract_video_id(file)
            print(f"Notifying clients of new YouTube video: {video_id}")
            socketio.emit('new_audio', {'videoId': video_id, 'type': type})

def extract_video_id(url):
    # 使用正則表達式提取 YouTube 影片的 ID
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else url

if __name__ == '__main__':
    print("Starting Flask server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
