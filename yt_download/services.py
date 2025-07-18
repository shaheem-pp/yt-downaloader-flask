import threading
import time
import uuid
import os
from pytube import YouTube
import subprocess

progress_data = {}

def start_download(url):
    task_id = str(uuid.uuid4())
    progress_data[task_id] = {'status': 'pending', 'streams': [], 'error': None}
    thread = threading.Thread(target=_fetch_streams, args=(url, task_id))
    thread.start()
    return task_id

def _fetch_streams(url, task_id):
    try:
        yt = YouTube(url)
        streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
        stream_list = []
        for s in streams:
            stream_list.append({
                'itag': s.itag,
                'resolution': s.resolution,
                'mime_type': s.mime_type,
                'filesize': s.filesize,
                'abr': getattr(s, 'abr', None),
                'type': s.type
            })
        progress_data[task_id]['streams'] = stream_list
        progress_data[task_id]['status'] = 'ready'
        progress_data[task_id]['title'] = yt.title
    except Exception as e:
        # Fallback to yt-dlp if pytube fails
        try:
            import json
            cmd = [
                'yt-dlp',
                '-J',
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            stream_list = []
            for f in info.get('formats', []):
                if f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none' and f.get('ext') == 'mp4':
                    stream_list.append({
                        'itag': f['format_id'],
                        'resolution': f.get('resolution') or f.get('height', ''),
                        'mime_type': f.get('mime_type', ''),
                        'filesize': f.get('filesize') or 0,
                        'abr': f.get('abr', None),
                        'type': 'video'
                    })
            progress_data[task_id]['streams'] = stream_list
            progress_data[task_id]['status'] = 'ready'
            progress_data[task_id]['title'] = info.get('title', 'video')
            progress_data[task_id]['use_ytdlp'] = True
        except Exception as ytdlp_e:
            progress_data[task_id]['status'] = 'error'
            progress_data[task_id]['error'] = f"pytube error: {str(e)}; yt-dlp error: {str(ytdlp_e)}"

def download_stream(url, itag, task_id):
    # Check if yt-dlp should be used
    use_ytdlp = progress_data.get(task_id, {}).get('use_ytdlp', False)
    progress_data[task_id] = {'progress': 0, 'status': 'downloading', 'eta': '', 'filename': None, 'error': None}
    if use_ytdlp:
        try:
            # Get title for folder organization
            title = progress_data.get(task_id, {}).get('title', 'video')
            safe_title = ''.join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
            base_dir = os.path.abspath(os.path.join(os.getcwd(), 'downloads', safe_title))
            os.makedirs(base_dir, exist_ok=True)
            output_template = os.path.join(base_dir, '%(title)s.%(ext)s')
            cmd = [
                'yt-dlp',
                '-f', str(itag),
                '-o', output_template,
                url
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            filename = None
            for line in process.stdout:
                if '[download] Destination:' in line:
                    filename = line.split('Destination:')[1].strip()
                if '%' in line:
                    import re
                    match = re.search(r'(\d{1,3}\.\d)%.*?ETA (\d{2}:\d{2})', line)
                    if match:
                        percent = float(match.group(1)) / 100.0
                        eta = match.group(2)
                        progress_data[task_id]['progress'] = percent
                        progress_data[task_id]['eta'] = eta
            process.wait()
            if process.returncode == 0 and filename and os.path.exists(filename):
                progress_data[task_id]['filename'] = filename
                progress_data[task_id]['status'] = 'done'
            else:
                progress_data[task_id]['status'] = 'error'
                progress_data[task_id]['error'] = f"yt-dlp failed: {line.strip() if 'line' in locals() else 'Unknown error'}"
        except Exception as e:
            progress_data[task_id]['status'] = 'error'
            progress_data[task_id]['error'] = f"yt-dlp error: {str(e)}"
    else:
        try:
            yt = YouTube(url, on_progress_callback=lambda s, c, r: progress_hook(s, c, r, task_id))
            stream = yt.streams.get_by_itag(itag)
            if not stream:
                raise Exception('Selected stream not found.')
            safe_title = ''.join(c for c in yt.title if c.isalnum() or c in (' ', '_', '-')).rstrip()
            base_dir = os.path.abspath(os.path.join(os.getcwd(), 'downloads', safe_title))
            os.makedirs(base_dir, exist_ok=True)
            filename = stream.default_filename
            abs_filename = os.path.join(base_dir, filename)
            progress_data[task_id]['filename'] = abs_filename
            stream.download(output_path=base_dir, filename=filename)
            progress_data[task_id]['status'] = 'done'
        except Exception as e:
            progress_data[task_id]['status'] = 'error'
            progress_data[task_id]['error'] = str(e)

def progress_hook(stream, chunk, bytes_remaining, task_id):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percent = bytes_downloaded / total_size
    progress_data[task_id]['progress'] = percent
    # Estimate ETA
    if percent > 0:
        elapsed = getattr(stream, 'start_time', None)
        if not elapsed:
            stream.start_time = time.time()
            elapsed = stream.start_time
        elapsed_time = time.time() - stream.start_time
        speed = bytes_downloaded / elapsed_time if elapsed_time > 0 else 0
        eta_seconds = bytes_remaining / speed if speed > 0 else 0
        progress_data[task_id]['eta'] = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
    else:
        progress_data[task_id]['eta'] = ''

def get_progress(task_id):
    return progress_data.get(task_id)

def get_filename(task_id):
    data = progress_data.get(task_id)
    if data and data['status'] == 'done' and data['filename']:
        return data['filename']
    return None

def get_streams(task_id):
    return progress_data.get(task_id)
