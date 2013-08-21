import re
import sys
import sha
import hashlib
import logging
import webapp2 as webapp
from google.appengine.ext import ndb
from models import EnvayaInboxMessage, EnvayaOutboxMessage
from google.appengine._internal.django.utils import simplejson as json


logger = logging.getLogger(__name__)


class Envaya(list):

    def __init__(self, req):
        super(Envaya, self).__init__()
        self.req = req
        dump = {}
        for k in req.request.arguments():
            v = req.request.get(k)
            dump[k] = v
        self.msg = EnvayaInboxMessage(
            dump=json.dumps(dump)
        )
        self.msg.put()
        if self.msg.action == self.msg.ACTIONS[1]: #incoming
            pass
        elif self.msg.action == self.msg.ACTIONS[2]: #outgoing
            self.queue_unsent_messages()
        elif self.msg.action == self.msg.ACTIONS[3]: #send_status
            self.mark_send_status()

    def queue_unsent_messages(self):
        unsent_messages = EnvayaOutboxMessage.gql(
            'WHERE send_status=:1', None
        )
        for msg in unsent_messages.fetch(1000):
            msg = msg.toDICT
            msg['event'] = 'send'
            self.append(msg)

    def mark_send_status(self):
        msg = self.msg.outbox_message
        msg.send_status = self.msg.key
        msg.put()

    def queue(self, message):
        frm = self.msg.phone_number
        if self.msg.action == self.msg.ACTIONS[1]:
            frm = self.msg.frm
        message.setdefault('event', 'send')
        message.setdefault('to', frm)
        outboxMsg = EnvayaOutboxMessage(
              to=message['to']
            , message=message['message']
        )
        outboxMsg.put()
        message['id'] = str(outboxMsg.key.id())
        self.append(message)

    def send(self):
        if len(self) != 0:
            logger.info('SENDING')
        res = {}
        for message in self:
            logger.info(message)
            event = message['event']
            res.setdefault(event, [])
            del message['event']
            res[event].append(message)
        events = [{'event': k, 'messages': v} for k, v in res.iteritems()]
        content = {
            'events': events
        }
        json_content = json.dumps(content)
        self.req.response.headers['Content-Type'] = 'application/json'
        self.req.response.out.write(json_content)
        return


def validate(self, attr):
    if self.request.get(attr, None) == None:
        e = 'invalid request ' + attr
        raise Exception(e)


def validate_req(phone_number, password):
    def wrapper(view):
        def func(self):
            self.auth_params = {
                  'phone_number': phone_number
                , 'password': password
            }
            for attr in [
                  'phone_number'
                , 'action'
            ]:
                try:
                    validate(self, attr)
                except Exception, e:
                    self.response.clear()
                    self.response.set_status(400, e)
                    return
            if self.request.get('action') not in EnvayaInboxMessage.ACTIONS.values():
                e = 'invalid request action'
                self.response.clear()
                self.response.set_status(400, e)
                return
            if phone_number != self.request.get('phone_number'):
                e = 'request is from a forbiddened number'
                self.response.clear()
                self.response.set_status(403, e)
                return
            return view(self)
        func.func_name = view.func_name
        return func
    return wrapper


def auth_req(view):
    def wrapper(self):
        if len(sys.argv) > 1 and 'nosetests' in sys.argv[0]:
            return view(self)
        data = self.request.copy()
        data_string = self.request.url
        data_keys = [k for k in sorted(self.request.arguments())]
        for k in data_keys:
            v = data.get(k)
            data_string += ',%s=%s' % (k, v)
        data_string += ',' + self.auth_params['password']
        sig = self.request.headers.get('X-Request-Signature')
        generated_sig = sha.new(data_string).digest().encode('base64')
        if sig.strip() != generated_sig.strip():
            e = 'wrong phone/password combination'
            self.response.clear()
            self.response.set_status(403, e)
            return
        return view(self)
    return wrapper


def handle_test_req(view):
    def wrapper(self):
        if self.request.get('action') == 'test':
            self.response.out.write('OK')
            return
        return view(self)
    return wrapper


def validate_incoming_req(view):
    def wrapper(self):
        if self.request.get('action') == EnvayaInboxMessage.ACTIONS[1]:
            for attr in [
                  'from'
                , 'message_type'
                , 'message'
                , 'timestamp'
            ]:  
                try:
                    validate(self, attr)
                except Exception, e:
                    self.response.clear()
                    self.response.set_status(400, e)
                    return
        return view(self)
    return wrapper


def validate_outgoing_req(view):
    def wrapper(self):
        if self.request.get('action') == EnvayaInboxMessage.ACTIONS[2]:
            pass
        return view(self)
    return wrapper


def validate_send_status_req(view):
    def wrapper(self):
        if self.request.get('action') == EnvayaInboxMessage.ACTIONS[3]:
            for attr in [
                  'id'
                , 'status'
                , 'error'
            ]:
                try:
                    validate(self, attr)
                except Exception, e:
                    self.response.clear()
                    self.response.set_status(400, e)
                    return
        return view(self)
    return wrapper


def log(view):
    def wrapper(self):
        logger.info('RECEIVING')
        for k in self.request.arguments():
            v = self.request.get(k)
            logger.info('%s: %s' % (k, v))
        return view(self)
    return wrapper


def receive(phone_number, password):
    def wrapper(view):
        @validate_req(phone_number, password)
        @auth_req
        @handle_test_req
        @validate_incoming_req
        @validate_outgoing_req
        @validate_send_status_req
        @log
        def func(self):
            envaya = Envaya(self)
            self.envaya = envaya
            view(self)
            envaya.send()
            return
        func.func_name = view.func_name
        return func
    return wrapper