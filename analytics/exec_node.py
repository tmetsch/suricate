
import pika
import sys

class Node(object):

    def __init__(self, uri, queue):
        # connection = pika.BlockingConnection(pika.URLParameters(uri))
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

        self.channel = connection.channel()

        self.channel.queue_declare(queue=queue)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.on_request, queue=queue)

        print " [x] Awaiting RPC requests"
        self.channel.start_consuming()

    def on_request(self, ch, method, props, body):
        n = int(body)

        print " [.] fib(%s)"  % (n,)
        response = n * 2

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag = method.delivery_tag)

if __name__ == '__main__':
    Node('amqp://localhost:5672/%2F', sys.argv[1])