import json
import os
import time
from celery import Celery

from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response, abort
from flask_sqlalchemy import SQLAlchemy

from download_file_handler import Downloader
from rabbit_mq_connectors import RabbiMQConnectors

load_dotenv()

app = Flask(__name__)

# ------------------------------------------ database configuration ---------------------------------------------------
app.config.from_object("config.Config")
db = SQLAlchemy(app)


class DownloadInfo(db.Model):
    __tablename__ = "download_info"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_name = db.Column(db.String)
    report = db.Column(db.JSON)


# ------------------------------------------- celery configuration ----------------------------------------------------
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@celery.task
def download_file_task(file_link: str, queue_name: str, download_speed: int = 100):
    with app.app_context():
        download_data = None

        try:

            downloader = Downloader(file_link)
            download_data = downloader.get_download_info(max_speed=download_speed)

            # save download info to db
            if download_data:
                new_data = DownloadInfo(file_name=queue_name, report=download_data)
                db.session.add(new_data)
                db.session.commit()

        except Exception as err:
            print(f"Something went wrong when trying to download file : {err}")
        try:

            rabbit_connector = RabbiMQConnectors()
            rabbit_chanel = rabbit_connector.create_new_queue(queue_name=queue_name)
            if download_data:
                rabbit_chanel.basic_publish(exchange='',
                                            routing_key=queue_name,
                                            body=json.dumps(download_data))
            else:
                rabbit_chanel.basic_publish(exchange='',
                                            routing_key=queue_name,
                                            body=json.dumps({"error": "error_when downloading file"}))
            rabbit_connector.close_connection()
        except Exception as r_err:
            print(f"something went wrong when trying publish message to rabbit: {r_err}")


# ----------------------------------------------- app routes ---------------------------------------------------------


@app.route('/alive', methods=['GET'])
def health_check():
    return Response()


@app.route('/download', methods=['POST'])
def download_file():
    request_data = request.json
    file_link = request_data.get("file_link")
    download_speed = request_data.get("download_speed")

    if not file_link:
        abort(400, "Please provide link for the file")

    queue_name = f"{os.getenv('VPS_NAME')}_{time.strftime('%Y-%m-%d_%H:%M:%S')}"
    if download_speed:
        download_file_task.delay(file_link=file_link,
                                 queue_name=queue_name,
                                 download_speed=download_speed)
    else:
        download_file_task.delay(file_link=file_link,
                                 queue_name=queue_name)

    return jsonify({'queue_name': queue_name})


@app.route('/get-download-file-report/<queue_name>', methods=['GET'])
def get_scheduled_task_report(queue_name):
    report = db.session.query(DownloadInfo).filter_by(file_name=queue_name).first()
    if report:
        return jsonify(report.report)
    else:
        return jsonify({'error': 'Report not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0')
