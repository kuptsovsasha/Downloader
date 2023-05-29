import time
import socket
import os
import requests
import ping3 as ping3


class Downloader:

    def __init__(self, file_link: str):
        self.file_link = file_link

    def get_download_info(self, max_speed: int):
        return self.__start_downloading(max_speed=max_speed)

    def __start_downloading(self, max_speed: int) -> dict:
        try:
            # Measure the network latency to the file host before the download
            host = requests.utils.urlparse(self.file_link).hostname
            # Get the IP address of the hostname
            ip_address = socket.gethostbyname(host)

            pre_latency = ping3.ping(host, unit="ms")

            # Download the file and measure the time taken
            start_time = time.time()
            response = requests.get(self.file_link, stream=True)

            chunk_size = 1024 * 1024  # 1MB
            delay = self.__get_delay_time(max_speed=max_speed, chunk_size=chunk_size)
            for chunk in response.iter_content(chunk_size=chunk_size):
                time.sleep(delay)
            download_time = round(time.time() - start_time, 3)

            # Measure the network latency to the file host after the download
            post_latency = ping3.ping(host, unit="ms")

            # Calculate the average network latency
            avg_latency = round((pre_latency + post_latency) / 2, 3)

            # Measure the time-to-first-byte (TTFB)
            ttfb = response.elapsed.total_seconds()

            # Return the download time in a JSON response
            return {'download_time': f'{download_time * 1000}',
                    'avg_latency': f'{avg_latency}',
                    'ttfb': f'{round((ttfb * 1000), 3)}',
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

    @staticmethod
    def __get_delay_time(max_speed: int, chunk_size: int):
        delay_value_mapper = {
            100: 2.5,
            200: 2,
            1000: 0
        }
        speed_value = max_speed * delay_value_mapper.get(max_speed)
        max_speed_in_bytes = speed_value * 131072
        delay = chunk_size / max_speed_in_bytes if max_speed_in_bytes > 0 else 0
        return delay


