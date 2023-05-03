import os
import time

import ping3 as ping3
import requests
from flask import Flask, request, jsonify, Response

app = Flask(__name__)


@app.route('/alive', methods=['GET'])
def health_check():
    return Response()


@app.route('/download', methods=['POST'])
def download_file():
    # Get the file link from the request data
    file_link = request.json['file_link']

    # Measure the network latency to the file host before the download
    host = requests.utils.urlparse(file_link).hostname
    pre_latency = ping3.ping(host, unit="ms")

    # Download the file and measure the time taken
    start_time = time.time()
    response = requests.get(file_link, stream=True)
    with open('downloaded_file', 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    download_time = round(time.time() - start_time, 3)

    # Measure the network latency to the file host after the download
    post_latency = ping3.ping(host, unit="ms")

    # Calculate the average network latency
    avg_latency = round((pre_latency + post_latency) / 2, 3)

    # Measure the time-to-first-byte (TTFB)
    ttfb = response.elapsed.total_seconds()

    # Delete the downloaded file
    os.remove('downloaded_file')

    # Return the download time in a JSON response
    return jsonify({'download_time': f'{download_time} sec.',
                    'avg_latency': f'{avg_latency} ms.',
                    'ttfb': f'{round(ttfb, 3)} sec.'})


if __name__ == '__main__':
    app.run()
