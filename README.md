# YouTube Video Downloader (Educational Purposes Only)

This project is a simple web-based YouTube video downloader built with Python and Flask. It allows users to fetch available video/audio streams from a YouTube URL and download their selected stream. The backend uses `pytube` and `yt-dlp` for stream extraction and downloading.

**Disclaimer:**
> This project is for educational purposes only. Downloading YouTube videos may violate YouTube's Terms of Service. Use responsibly and only download content you have rights to.

## Features
- Fetch available video/audio streams from a YouTube URL
- Download selected stream (video or audio)
- Progress tracking for downloads
- Fallback to `yt-dlp` if `pytube` fails

## Setup Instructions

### Prerequisites
- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed and available in your PATH

### Installation
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd yt-download
   ```
2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Install yt-dlp:**
   ```bash
   pip install yt-dlp
   # or install system-wide
   # brew install yt-dlp  # on macOS
   # sudo apt install yt-dlp  # on Ubuntu/Debian
   ```

### Running the App
1. **Start the Flask server:**
   ```bash
   python run.py
   ```
2. **Open your browser and go to:**
   [http://127.0.0.1:5000](http://127.0.0.1:5000)

3. **Usage:**
   - Enter a YouTube video URL.
   - Select the desired stream from the list.
   - Click download and wait for the process to complete.

## Notes
- Downloads are saved in the `downloads/` directory.
- This app is for local/educational use only. Do not deploy publicly.

## License
This project is provided for educational purposes only and is not intended for commercial use.

