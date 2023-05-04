import os
import socket
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
    try:
        # Get the file link from the request data
        file_link = request.json['file_link']

        # Measure the network latency to the file host before the download
        host = requests.utils.urlparse(file_link).hostname
        # Get the IP address of the hostname
        ip_address = socket.gethostbyname(host)

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
                        'ttfb': f'{round(ttfb, 3)} sec.',
                        'file_ip': ip_address})

    except (requests.exceptions.RequestException, ping3.exceptions.PingError) as e:
        # Return an error response if there's an exception during the download or network measurement
        return jsonify({'error': f'{type(e).__name__}: {str(e)}'}), 500

    except (KeyError, TypeError) as e:
        # Return an error response if the JSON request data is invalid
        return jsonify({'error': f'Invalid request data: {str(e)}'}), 400

    except Exception as e:
        # Return a generic error response for any other unexpected errors
        return jsonify({'error': f'Unexpected error: {type(e).__name__}: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0')
