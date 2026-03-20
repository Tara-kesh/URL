from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import os
import subprocess

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
PRIVATE_FOLDER = "private"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(PRIVATE_FOLDER, exist_ok=True)

SECRET_PASSWORD = "1234"

progress_data = {
    "status": "",
    "percent": "0%",
    "filename": ""
}

def get_video_type(filepath):
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            filepath
        ]
        result = subprocess.check_output(cmd).decode().strip()
        w, h = map(int, result.split('x'))
        return "short" if h > w else "wide"
    except:
        return "wide"

def progress_hook(d):
    if d['status'] == 'downloading':
        progress_data["status"] = "Downloading..."
        progress_data["percent"] = d.get('_percent_str', '0%')
        progress_data["filename"] = os.path.basename(d.get('filename', ''))
    elif d['status'] == 'finished':
        progress_data["status"] = "Merging..."
        progress_data["percent"] = "100%"

@app.route("/")
def index():
    files = os.listdir(DOWNLOAD_FOLDER)

    videos = []
    for f in files:
        path = os.path.join(DOWNLOAD_FOLDER, f)
        videos.append({
            "name": f,
            "type": get_video_type(path)
        })

    return render_template("index.html", videos=videos)

@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'noplaylist': True,
        'concurrent_fragment_downloads': 10,
        'retries': 3,
        'fragment_retries': 3,
        'postprocessor_args': ['-preset', 'ultrafast'],
        'progress_hooks': [progress_hook],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    progress_data["status"] = "Completed ✅"
    return "Done"

@app.route("/progress")
def progress():
    return jsonify(progress_data)

@app.route("/delete/<filename>", methods=["POST"])
def delete_video(filename):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return "Deleted"
    return "Error"

@app.route("/move_to_private/<filename>", methods=["POST"])
def move_to_private(filename):
    src = os.path.join(DOWNLOAD_FOLDER, filename)
    dest = os.path.join(PRIVATE_FOLDER, filename)

    if os.path.exists(src):
        os.rename(src, dest)
        return "Moved"
    return "Error"

# 🔥 NEW: MOVE BACK TO PUBLIC
@app.route("/move_to_public/<filename>", methods=["POST"])
def move_to_public(filename):
    src = os.path.join(PRIVATE_FOLDER, filename)
    dest = os.path.join(DOWNLOAD_FOLDER, filename)

    if os.path.exists(src):
        os.rename(src, dest)
        return "Moved Back"
    return "Error"

# 🔥 NEW: DELETE PRIVATE VIDEO
@app.route("/delete_private/<filename>", methods=["POST"])
def delete_private(filename):
    path = os.path.join(PRIVATE_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return "Deleted"
    return "Error"

@app.route("/private", methods=["POST"])
def private_access():
    password = request.form.get("password")

    if password == SECRET_PASSWORD:
        files = os.listdir(PRIVATE_FOLDER)
        return jsonify({"status": "success", "files": files})
    else:
        return jsonify({"status": "error"})

@app.route('/video/<filename>')
def video(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

@app.route('/private_video/<filename>')
def private_video(filename):
    return send_from_directory(PRIVATE_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)