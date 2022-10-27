import json, datetime
import logging, os, pika
from decouple import config


def json_dump_default(o):
    if isinstance(o, datetime):
        return o.isoformat()
    else:
        return str(o)


class Publisher:
    def __init__(self):
        self.interface_address = config('COUPON_ADDRESS')
        self._sending_method = config('COUPON_METHOD')
        QUEUE_SIZE = 500000
        credentials = pika.PlainCredentials(config('RQ_USER'), config('RQ_PASS'))
        parameters = pika.ConnectionParameters(config('RQ_HOST'),
                                    config('RQ_PORT'),
                                    '/',
                                    credentials)
        connection = pika.BlockingConnection(parameters)
        self.channel = connection.channel()
        self.channel.queue_declare(queue=config('COUPON_QUEUE'), durable=True ,arguments={'x-max-length': QUEUE_SIZE})
        self.properties = pika.BasicProperties(self._sending_method, delivery_mode=2)

    def process_item(self, item):
        b = json.dumps(item, ensure_ascii=False, default=json_dump_default)
        data = json.loads(b)
        if data:
            self.publish(data)
        return data

    
    def publish(self, body):
        # print(body)
        #properties = pika.BasicProperties(method, delivery_mode=2, arguments={'x-max-length': QUEUE_SIZE})
        self.channel.basic_publish(exchange='', routing_key=config('COUPON_ROUTING_KEY'),
                            body=json.dumps(body), properties=self.properties)

