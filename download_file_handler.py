import time
import socket
import os
import requests
import ping3 as ping3


class Downloader:

    def __init__(self, file_link: str):
        self.file_link = file_link

    def get_download_info(self):
        return self.__start_downloading()

    def __start_downloading(self, max_speed: int = 100) -> dict:
        try:
            # Measure the network latency to the file host before the download
            host = requests.utils.urlparse(self.file_link).hostname
            # Get the IP address of the hostname
            ip_address = socket.gethostbyname(host)

            pre_latency = ping3.ping(host, unit="ms")

            # Download the file and measure the time taken
            start_time = time.time()
            response = requests.get(self.file_link, stream=True)
            file_name = f"download_file_{time.strftime('%Y-%m-%d_%H:%M:%S')}"

            max_speed_in_bytes = max_speed * 125829
            chunk_size = 8192
            delay = chunk_size / max_speed_in_bytes
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
                    time.sleep(delay)
            download_time = round(time.time() - start_time, 3)

            # Measure the network latency to the file host after the download
            post_latency = ping3.ping(host, unit="ms")

            # Calculate the average network latency
            avg_latency = round((pre_latency + post_latency) / 2, 3)

            # Measure the time-to-first-byte (TTFB)
            ttfb = response.elapsed.total_seconds()

            # Delete the downloaded file
            os.remove(file_name)

            # Return the download time in a JSON response
            return {'download_time': f'{download_time * 1000}',
                    'avg_latency': f'{avg_latency}',
                    'ttfb': f'{round(ttfb, 3)}',
                    'file_ip': ip_address}
        except (requests.exceptions.RequestException,) as e:
            # Return an error response if there's an exception during the download or network measurement
            return {'error': f'{type(e).__name__}: {str(e)}'}

        except (KeyError, TypeError) as e:
            # Return an error response if the JSON request data is invalid
            return {'error': f'Invalid request data: {str(e)}'}

        except Exception as e:
            # Return a generic error response for any other unexpected errors
            return {'error': f'Unexpected error: {type(e).__name__}: {str(e)}'}

