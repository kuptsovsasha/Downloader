import json
import os
import time
from celery import Celery

from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response

from download_file_handler import Downloader
from rabbit_mq_connectors import RabbiMQConnectors

load_dotenv()

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@app.route('/alive', methods=['GET'])
def health_check():
    return Response()


@celery.task
def download_file_task(file_link, queue_name):
    rabbit_connector = RabbiMQConnectors()
    rabbit_chanel = rabbit_connector.create_new_queue(queue_name=queue_name)

    downloader = Downloader(file_link)
    download_data = downloader.get_download_info()

    rabbit_chanel.basic_publish(exchange='',
                                routing_key=queue_name,
                                body=json.dumps(download_data))
    rabbit_connector.close_connection()


@app.route('/download', methods=['POST'])
def download_file():
    file_link = request.json['file_link']

    queue_name = f"{os.getenv('VPS_NAME')}_{time.strftime('%Y-%m-%d_%H:%M:%S')}"

    download_file_task.delay(file_link, queue_name)

    return jsonify({'queue_name': queue_name})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
