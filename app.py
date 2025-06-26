from flask import Flask, render_template_string, send_file, request,url_for,redirect
import os
from urllib.parse import quote, unquote
import platform
import os
import re
app = Flask(__name__)

# Video file extensions
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ogv'}

def is_video_file(filename):
    """Check if file is a video file based on extension."""
    return os.path.splitext(filename.lower())[1] in VIDEO_EXTENSIONS

def natural_key(s):
    """Sort helper that sorts strings in human order."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def get_directory_contents(path):
    """Get folders and video files in the given directory, sorted naturally."""
    try:
        items = os.listdir(path)
        folders = []
        videos = []
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folders.append(item)
            elif os.path.isfile(item_path) and is_video_file(item):
                videos.append(item)
        folders.sort(key=natural_key)
        videos.sort(key=natural_key)
        return folders, videos
    except PermissionError:
        return [], []


def get_available_drives():
    """
    On Windows: return list of available drive letters.
    On non-Windows: return the current working directory.
    """
    if platform.system() == 'Windows':
        from ctypes import windll
        import string
        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(f'{letter}:\\')
            bitmask >>= 1
        return drives



@app.route('/')
def index():
    """Redirect to /browse if not Windows, else list drives."""
    if platform.system() != 'Windows':
        # Redirect to /browse/, which defaults to os.getcwd()
        return redirect(url_for('browse_directory'))
    
    # Windows: Show drives
    drives = get_available_drives()
    return render_template_string("""
    <h1>Available Drives</h1>
    <ul>
        {% for drive in drives %}
            <li><a href="{{ url_for('browse_directory', subpath=drive|urlencode) }}">{{ drive }}</a></li>
        {% endfor %}
    </ul>
    """, drives=drives)


@app.route('/browse/', defaults={'subpath': ''})
@app.route('/browse/<path:subpath>')
def browse_directory(subpath=''):
    """Browse directory and show folders and videos."""
    current_path = unquote(subpath) if subpath else os.getcwd()

    if not os.path.exists(current_path) or not os.path.isdir(current_path):
        return "Invalid directory path", 404

    folders, videos = get_directory_contents(current_path)

    # Create breadcrumb navigation
    breadcrumbs = []
    if subpath:
        parts = subpath.replace('\\', '/').split('/')
        current_breadcrumb = ''
        for part in parts:
            current_breadcrumb = os.path.join(current_breadcrumb, part) if current_breadcrumb else part
            breadcrumbs.append({
                'name': part,
                'path': current_breadcrumb
            })

    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Player</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 20px; 
                background-color: #f5f5f5;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .breadcrumb {
                margin-bottom: 20px;
                padding: 10px;
                background-color: #e9ecef;
                border-radius: 4px;
            }
            .breadcrumb a {
                color: #007bff;
                text-decoration: none;
                margin-right: 5px;
            }
            .breadcrumb a:hover {
                text-decoration: underline;
            }
            .folder-list, .video-list { 
                margin-bottom: 30px; 
            }
            .folder-list h2, .video-list h2 {
                color: #333;
                border-bottom: 2px solid #007bff;
                padding-bottom: 10px;
            }
            .item {
                display: inline-block;
                margin: 10px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
                background: white;
                min-width: 200px;
                text-align: center;
            }
            .item:hover {
                background-color: #f8f9fa;
                border-color: #007bff;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
            }

            .folder {
                background-color: #fff3cd;
                border-color: #ffeaa7;
            }
            .folder:hover {
                background-color: #ffeaa7;
            }
            .video {
                background-color: #d1ecf1;
                border-color: #bee5eb;
            }
            .video:hover {
                background-color: #bee5eb;
            }
            .icon {
                font-size: 24px;
                margin-bottom: 10px;
            }
            .video-player {
                margin-top: 30px;
                text-align: center;
            }
            video {
                max-width: 100%;
                max-height: 500px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .current-video {
                margin-top: 20px;
                padding: 15px;
                background-color: #e8f5e8;
                border-radius: 8px;
                border: 1px solid #c3e6c3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Video Player</h1>
            
            <!-- Breadcrumb Navigation -->
            <div class="breadcrumb">
                <a href="/">🏠 Home</a>
                {% for crumb in breadcrumbs %}
                    / <a href="/browse/{{ crumb.path }}">{{ crumb.name }}</a>
                {% endfor %}
            </div>
            
            <!-- Current Path -->
            <p><strong>Current Path:</strong> {{ current_path }}</p>
            
            <!-- Folders -->
            {% if folders %}
            <div class="folder-list">
                <h2>📁 Folders</h2>
                <div class="grid">
                {% for folder in folders %}
                <div class="item folder" onclick="navigateToFolder('{{ folder }}')">
                    <div class="icon">📁</div>
                    <div>{{ folder }}</div>
                </div>
                {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <!-- Videos -->
            {% if videos %}
            <div class="video-list">
                <h2>🎥 Videos</h2>
                <div class="grid">
                {% for video in videos %}
                <div class="item video" onclick="playVideo('{{ video }}')">
                    <div class="icon">🎬</div>
                    <div>{{ video }}</div>
                </div>
                {% endfor %}
                </div>
            </div>
            {% endif %}
            
            {% if not folders and not videos %}
            <p style="text-align: center; color: #666; font-style: italic;">
                No folders or video files found in this directory.
            </p>
            {% endif %}
            
            <!-- Video Player -->
            <div class="video-player" id="videoPlayer" style="display: none;">
                <div class="current-video">
                    <h3>Now Playing: <span id="currentVideoName"></span></h3>
                </div>
                <video id="videoElement" controls>
                    Your browser does not support the video tag.
                </video>
                <div style="margin: 20px;">
                <button id="prevBtn">⏮️ Prev</button>
                <button id="nextBtn">⏭️ Next</button>
                </div>
            </div>
        </div>
        
        <script>
            function navigateToFolder(folderName) {
                const currentPath = '{{ subpath }}';
                const newPath = currentPath ? currentPath + '/' + folderName : folderName;
                window.location.href = '/browse/' + encodeURIComponent(newPath);
            }
            
            function playVideo(videoName) {
                const currentPath = '{{ subpath }}';
                const videoPath = currentPath ? currentPath + '/' + videoName : videoName;
                const videoUrl = '/video/' + encodeURIComponent(videoPath);
                
                const videoPlayer = document.getElementById('videoPlayer');
                const videoElement = document.getElementById('videoElement');
                const currentVideoName = document.getElementById('currentVideoName');
                
                videoElement.src = videoUrl;
                currentVideoName.textContent = videoName;
                videoPlayer.style.display = 'block';
                
                // Scroll to video player
                videoPlayer.scrollIntoView({ behavior: 'smooth' });
            }
           
            const videoList = [{% for video in videos %}'{{ video }}',{% endfor %}];
            let currentVideoIndex = -1;

            function navigateToFolder(folderName) {
                const currentPath = '{{ subpath }}';
                const newPath = currentPath ? currentPath + '/' + folderName : folderName;
                window.location.href = '/browse/' + encodeURIComponent(newPath);
            }

            function playVideo(videoName) {
                const currentPath = '{{ subpath }}';
                const videoPath = currentPath ? currentPath + '/' + videoName : videoName;

                currentVideoIndex = videoList.indexOf(videoName);
                const videoUrl = '/video/' + encodeURIComponent(videoPath);

                const videoPlayer = document.getElementById('videoPlayer');
                const videoElement = document.getElementById('videoElement');
                const currentVideoName = document.getElementById('currentVideoName');

                videoElement.src = videoUrl;
                currentVideoName.textContent = videoName;
                videoPlayer.style.display = 'block';
                videoPlayer.scrollIntoView({ behavior: 'smooth' });
            }

            document.getElementById('prevBtn')?.addEventListener('click', function() {
                if (currentVideoIndex > 0) {
                    playVideo(videoList[currentVideoIndex - 1]);
                }
            });
            document.getElementById('nextBtn')?.addEventListener('click', function() {
                if (currentVideoIndex < videoList.length - 1) {
                    playVideo(videoList[currentVideoIndex + 1]);
                }
            });


        </script>
    </body>
    </html>
    """
    return render_template_string(template,
                                  folders=folders,
                                  videos=videos,
                                  subpath=subpath,
                                  current_path=current_path,
                                  breadcrumbs=breadcrumbs)

@app.route('/video/<path:video_path>')
def serve_video(video_path):
    """Serve video files."""
    video_path = unquote(video_path)

    if not os.path.exists(video_path) or not is_video_file(video_path):
        return "Video not found", 404

    return send_file(video_path)

if __name__ == '__main__':
    print("Starting Video Player Web App...")
    app.run(debug=True, host='0.0.0.0', port=5000)