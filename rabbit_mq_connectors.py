import os

import pika


class RabbiMQConnectors:
    def __init__(self):
        self.url = os.getenv('RABBIT_MQ_URL')
        self.connection = self.__connect_to_rabbit_service()

    def __connect_to_rabbit_service(self):
        pika_url = self.url + "?heartbeat=360"
        connection = pika.BlockingConnection(pika.URLParameters(pika_url))
        return connection

    def create_new_queue(self, queue_name: str):
        channel = self.connection.channel()
        channel.queue_declare(queue=queue_name)
        return channel

    def close_connection(self):
        self.connection.close()
