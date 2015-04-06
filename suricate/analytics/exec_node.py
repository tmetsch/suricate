
"""
Execution node - listens to messages and executes notebooks etc.
"""

import json
import thread
import pika
import uuid

from time import time

from suricate.analytics import wrapper
from suricate.analytics import proj_ntb_store


class ExecNode(object):
    """
    Implementation of an execution node - run per tenant.
    """

    wrappers = {}
    jobs = {}

    def __init__(self, mongo_uri, amqp_uri, sdk, uid):
        self.uid = uid
        self.uri = mongo_uri
        # store
        self.stor = proj_ntb_store.NotebookStore(self.uri, self.uid)

        # sdk
        self.sdk = sdk

        # connect to AMQP broker
        connection = pika.BlockingConnection(pika.URLParameters(amqp_uri))
        self.channel = connection.channel()
        self.channel.queue_declare(queue=uid)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.callback, queue=uid)
        self.channel.start_consuming()

    def callback(self, channel, method, props, body):
        """
        Handle incoming request for this tenant.

        :param channel: The channel used.
        :param method: The message method.
        :param props: The message properties.
        :param body: The message body.
        """
        tmp = json.loads(body)
        response = self._handle(tmp)

        # set uuid so the right requester get the answer:-)
        prop = pika.BasicProperties(correlation_id=props.correlation_id)
        channel.basic_publish(exchange='',
                              routing_key=props.reply_to,
                              properties=prop,
                              body=json.dumps(response))
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def _handle(self, body):
        """
        Handle the incoming requests.

        :param body: The message body.
        """
        uid = body['uid']
        token = body['token']
        call = body['call']
        try:
            proj = body['project_id']
            interpreter = self._get_interpreter(proj, uid, token)
        except KeyError:
            proj = None
            interpreter = None
        res = {}
        # interactions with interpreter
        if call == 'run_notebook':
            ntb_id = body['notebook_id']
            src = body['src']
            ntb = self.stor.retrieve_notebook(proj, ntb_id, uid, token)
            out, err = interpreter.run(src)
            ntb['src'] = src
            ntb['out'] = out
            ntb['err'] = err
            self.stor.update_notebook(proj, ntb_id, ntb, uid, token)
        elif call == 'interact':
            ntb_id = body['notebook_id']
            ntb = self.stor.retrieve_notebook(proj, ntb_id, uid, token)
            loc = body['loc']
            tmp, err = interpreter.interact(loc)
            out = ['# ' + loc]
            out.extend(tmp)
            ntb['out'].extend(out)
            ntb['err'] = err
            self.stor.update_notebook(proj, ntb_id, ntb, uid, token)
        # job handling
        elif call == 'run_job':
            ntb_id = body['notebook_id']
            src = body['src']
            thread.start_new_thread(self._run_job, (proj, ntb_id, src,
                                                    interpreter, uid, token))
        elif call == 'list_jobs':
            res['jobs'] = self.jobs
        elif call == 'clear_job_list':
            for item in self.jobs.keys():
                if self.jobs[item]['state'].find('done') == 0:
                    self.jobs.pop(item)
        # project - from here on interactions with the store not interpreter.
        elif call == 'list_projects':
            res['projects'] = self.stor.list_projects(uid, token)
        elif call == 'retrieve_project':
            res['project'] = self.stor.retrieve_project(proj, uid, token)
        elif call == 'delete_project':
            res['project'] = self.stor.delete_project(proj, uid, token)
        # notebooks
        elif call == 'create_notebook':
            ntb_id = body['notebook_id']
            ntb = body['notebook']
            self.stor.update_notebook(proj, ntb_id, ntb, uid, token)
        elif call == 'retrieve_notebook':
            ntb_id = body['notebook_id']
            res['notebook'] = self.stor.retrieve_notebook(proj, ntb_id, uid,
                                                          token)
        elif call == 'update_notebook':
            ntb_id = body['notebook_id']
            ntb = self.stor.retrieve_notebook(proj, ntb_id, uid, token)
            ntb['src'] = body['src']
            self.stor.update_notebook(proj, ntb_id, ntb, uid, token)
        elif call == 'delete_notebook':
            ntb_id = body['notebook_id']
            self.stor.delete_notebook(proj, ntb_id, uid, token)
        else:
            raise AttributeError('Cannot handle this action: ' + call)
        return res

    def _get_interpreter(self, project_id, uid, token):
        """
        Return the interpreter per project, or create a new one.
        """
        if project_id not in self.wrappers:
            # TODO: make type configurable (Python, Julia, R, ...)
            self.wrappers[project_id] = wrapper.PythonWrapper(uid,
                                                              token,
                                                              self.uri,
                                                              self.sdk)
        return self.wrappers[project_id]

    def _run_job(self, proj, ntb_id, src, interpreter, uid, token):
        """
        Run a notebook as a long running job.
        """
        iden = str(uuid.uuid4())
        ntb = self.stor.retrieve_notebook(proj, ntb_id, uid, token)
        self.jobs[iden] = {'state': 'running',
                           'project': proj,
                           'ntb_id': ntb_id,
                           'ntb_name': ntb['meta']['name']}
        time_0 = time()
        out, err = interpreter.run(src)
        ntb['src'] = src
        ntb['out'] = out
        ntb['err'] = err
        time_1 = time()
        self.stor.update_notebook(proj, ntb_id, ntb, uid, token)
        self.jobs[iden]['state'] = 'done in ' + \
                                   str(round(time_1 - time_0, 2)) + 's'
