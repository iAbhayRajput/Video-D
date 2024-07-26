from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import re
import requests
import tempfile
import os

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

@app.route('/download', methods=['POST'])
def download_video():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 415

    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # Basic URL validation
    if not re.match(r'https?://(?:www\.)?linkedin\.com/.*', url):
        return jsonify({'error': 'Invalid LinkedIn URL'}), 400

    ydl_opts = {
        'format': 'best',
    }

    temp_file = None
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'url' not in info:
                return jsonify({'error': 'Could not extract video URL'}), 500

            video_url = info['url']
            filename = f"{info.get('title', 'linkedin_video')}.{info.get('ext', 'mp4')}"

            # Download the file to a temporary location
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            with temp_file:
                response = requests.get(video_url, stream=True)
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)

            # Send the file
            return send_file(temp_file.name, as_attachment=True, download_name=filename)

    except Exception as e:
        print(f"Error processing URL: {str(e)}")
        return jsonify({'error': f'Error processing URL: {str(e)}'}), 500

    finally:
        # Clean up the temporary file
        if temp_file:
            temp_file.close()
            try:
                os.unlink(temp_file.name)
            except PermissionError:
                print(f"Could not delete temporary file: {temp_file.name}")

if __name__ == '__main__':
    app.run(debug=True)