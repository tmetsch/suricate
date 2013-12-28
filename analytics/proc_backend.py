
import subprocess
import sys
import pika
import uuid

# cgexec -g cpu:group1 <command>

CMD=sys.executable

class Master(object):

    nodes = {}

    def __init__(self):
        self.nodes['123'] = None

        # TODO start exec node pre notebook per user...
        for node in self.nodes.keys():
            args = [CMD, 'exec_node.py', node]
            p = subprocess.Popen(args)

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key='123',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=str(n))
        while self.response is None:
            self.connection.process_data_events()
        return int(self.response)

if __name__ == '__main__':
    Master().call(6)