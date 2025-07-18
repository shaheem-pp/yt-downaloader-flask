from flask import render_template, request, jsonify, send_file
from yt_download import app
from yt_download.services import start_download, get_progress, get_filename, get_streams, download_stream
import threading

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/start_download', methods=['POST'])
def start_download_route():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    task_id = start_download(url)
    return jsonify({'task_id': task_id})

@app.route('/streams/<task_id>', methods=['GET'])
def streams_route(task_id):
    data = get_streams(task_id)
    if data:
        return jsonify(data)
    return jsonify({'error': 'Invalid task ID'}), 400

@app.route('/download_selected', methods=['POST'])
def download_selected_route():
    url = request.form.get('url')
    itag = request.form.get('itag')
    task_id = request.form.get('task_id')
    if not url or not itag or not task_id:
        return jsonify({'error': 'Missing parameters'}), 400
    thread = threading.Thread(target=download_stream, args=(url, itag, task_id))
    thread.start()
    return jsonify({'task_id': task_id})

@app.route('/progress/<task_id>', methods=['GET'])
def progress_route(task_id):
    data = get_progress(task_id)
    if data:
        return jsonify(data)
    return jsonify({'error': 'Invalid task ID'}), 400

@app.route('/download/<task_id>', methods=['GET'])
def download_route(task_id):
    filename = get_filename(task_id)
    if filename:
        return send_file(filename, as_attachment=True)
    return jsonify({'error': 'File not found or download not complete'}), 404
