import threading
import time
import uuid

from flask import Flask, request, send_file, render_template_string, jsonify
from pytube import YouTube

app = Flask(__name__)

progress_data = {}

HTML_FORM = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube Downloader</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-md-8">
      <div class="card shadow-sm">
        <div class="card-body">
          <h1 class="mb-4">YouTube Downloader</h1>
          <form id="download-form">
            <div class="mb-3">
              <input type="text" class="form-control" name="url" id="url" placeholder="YouTube URL" required>
            </div>
            <button type="submit" class="btn btn-primary">Download</button>
          </form>
          <div id="progress-section" class="mt-4" style="display:none;">
            <div class="progress mb-2">
              <div id="progress-bar" class="progress-bar" role="progressbar" style="width: 0%;">0%</div>
            </div>
            <div id="eta" class="text-muted small"></div>
          </div>
          <div id="error-message" class="alert alert-danger mt-3 d-none"></div>
        </div>
      </div>
    </div>
  </div>
</div>
<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script>
$(function() {
  $('#download-form').on('submit', function(e) {
    e.preventDefault();
    $('#progress-section').show();
    $('#progress-bar').css('width', '0%').text('0%');
    $('#eta').text('');
    $('#error-message').addClass('d-none').text('');
    $.post('/start_download', {url: $('#url').val()}, function(data) {
      if (data.task_id) {
        pollProgress(data.task_id);
      } else if (data.error) {
        $('#error-message').removeClass('d-none').text(data.error);
      }
    });
  });

  function pollProgress(task_id) {
    $.get('/progress/' + task_id, function(data) {
      if (data.error) {
        $('#error-message').removeClass('d-none').text(data.error);
        $('#progress-section').hide();
        return;
      }
      let percent = Math.round(data.progress * 100);
      $('#progress-bar').css('width', percent + '%').text(percent + '%');
      $('#eta').text(data.eta ? 'ETA: ' + data.eta : '');
      if (data.status === 'done') {
        window.location = '/download/' + task_id;
      } else if (data.status === 'error') {
        $('#error-message').removeClass('d-none').text(data.error);
        $('#progress-section').hide();
      } else {
        setTimeout(function() { pollProgress(task_id); }, 1000);
      }
    });
  }
});
</script>
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def download_video():
    error = None
    if request.method == 'POST':
        url = request.form['url']
        task_id = str(uuid.uuid4())
        progress_data[task_id] = {'progress': 0, 'status': 'pending', 'eta': ''}

        def run_download(url, task_id):
            try:
                yt = YouTube(url)
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                if not stream:
                    progress_data[task_id]['status'] = 'error'
                    progress_data[task_id][
                        'error'] = 'No downloadable video stream found. The video may be private, age-restricted, or not available in MP4 format.'
                else:
                    filename = stream.default_filename
                    stream.download(filename=filename,
                                    on_progress_callback=lambda s, f, p: progress_hook(s, f, p, task_id))
                    progress_data[task_id]['status'] = 'done'
                    progress_data[task_id]['filename'] = filename
            except Exception as e:
                progress_data[task_id]['status'] = 'error'
                progress_data[task_id]['error'] = str(e)

        threading.Thread(target=run_download, args=(url, task_id)).start()
        return jsonify({'task_id': task_id})
    return render_template_string(HTML_FORM + (f'<p style="color:red">{error}</p>' if error else ''))


@app.route('/progress/<task_id>', methods=['GET'])
def progress(task_id):
    data = progress_data.get(task_id, None)
    if data:
        return jsonify(data)
    return jsonify({'error': 'Invalid task ID'}), 400


@app.route('/download/<task_id>', methods=['GET'])
def download_file(task_id):
    data = progress_data.get(task_id, None)
    if data and data['status'] == 'done':
        filename = data['filename']
        # Clean up progress data
        del progress_data[task_id]
        return send_file(filename, as_attachment=True)
    return jsonify({'error': 'File not found or download not complete'}), 404


def progress_hook(stream, file_handle, bytes_remaining, task_id):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percent = bytes_downloaded / total_size
    eta = ''
    if percent > 0:
        elapsed_time = time.time() - stream.start_time
        speed = bytes_downloaded / elapsed_time
        eta_seconds = bytes_remaining / speed
        eta = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
    progress_data[task_id]['progress'] = percent
    progress_data[task_id]['eta'] = eta


if __name__ == '__main__':
    app.run(debug=True)
