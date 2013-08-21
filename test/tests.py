from google.appengine._internal.django.utils import simplejson as json
from lib.models import EnvayaInboxMessage, EnvayaOutboxMessage
from google.appengine.api import memcache
from google.appengine.ext import testbed
from google.appengine.api import users
from google.appengine.ext import ndb
from test import app
import unittest
import webtest
import logging


logger = logging.getLogger(__name__)


class TestCase(unittest.TestCase):

    uri = '/receive/'

    def setUp(self):
        self.app = webtest.TestApp(app)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.setup_env(
            test = 'true',
            overwrite = True
        )

    def tearDown(self):
        self.testbed.deactivate()


class RequestTestCase(TestCase):

    def test_must_have_required_props(self):
        data = {
        }
        res = self.app.post(self.uri, data, expect_errors=True)
        self.assertEqual(res.status_int, 400)

    def test_must_be_from_the_specified_no(self):
        data = {
              'phone_number': '254700111001'
            , 'password': 't'
            , 'action': 'incoming'
        }
        res = self.app.post(self.uri, data, expect_errors=True)
        self.assertEqual(res.status_int, 403)


class TestRequestTestCase(TestCase):

    def test_must_return_ok(self):
        data = {
            'phone_number': '254700111000',
            'action': 'test'
        }
        res = self.app.post(self.uri, data)
        self.assertEqual(res.body, 'OK')


class IncomingRequestTestCase(TestCase):

    def setUp(self):
        super(IncomingRequestTestCase, self).setUp()
        def POST(uri, data):
            data.setdefault('phone_number', '254700111000')
            data.setdefault('action', 'incoming')
            return self.app.post(uri, data, expect_errors=True)
        self.POST = POST

    def test_should_have_required_props(self):
        data = {
        }
        res = self.POST(self.uri, data)
        self.assertEqual(res.status_int, 400)

    def test_response(self):
        data = {
              'from': '254700111999'
            , 'message_type': ''
            , 'message': ''
            , 'timestamp': ''
        }
        res = self.POST(self.uri, data)
        self.assertEqual(res.status_int, 200)
        #
        # assert req was logged
        msgs = EnvayaInboxMessage.query()
        assert msgs.count(3) == 1
        msg = msgs.get()
        assert msg.action == 'incoming'
        assert msg.frm == '254700111999'
        
        # res data
        data = res.json
        # assert can send to sender
        assert data['events']
        event = data['events'][0]
        assert event['event'] == 'send'
        msg = event['messages'][0]
        assert msg['to'] == '254700111999'
        assert msg['message'] == 'outgoing1'
        # assert can send to other
        msg = event['messages'][1]
        assert msg['to'] == '254700111444'
        assert msg['message'] == 'outgoing2'


class OutgoingRequestTestCase(TestCase):

    def setUp(self):
        super(OutgoingRequestTestCase, self).setUp()
        def POST(uri, data):
            data.setdefault('phone_number', '254700111000')
            data.setdefault('action', 'outgoing')
            return self.app.post(uri, data)
        self.POST = POST

    def test_response(self):
        send_status = EnvayaInboxMessage(
            dump=''
        )
        send_status.put()
        EnvayaOutboxMessage(
              to='254700111888'
            , message='outgoing'
            , send_status=send_status.key
        ).put()
        EnvayaOutboxMessage(
              to='254700111999'
            , message='outgoing'
        ).put()
        data = {
        }
        res = self.POST(self.uri, data)
        self.assertEqual(res.status_int, 200)
        #
        # assert req was logged
        send_status.key.delete()
        msgs = EnvayaInboxMessage.query()
        assert msgs.count() == 1
        msg = msgs.get()
        assert msg.action == 'outgoing'
        #
        # res data
        data = res.json
        # assert message is queued
        assert data['events']
        event = data['events'][0]
        assert event['event'] == 'send'
        # assert queued up only 1 unsent msg
        assert len(event['messages']) == 1
        msg = event['messages'][0]
        assert msg['to'] == '254700111999'
        assert msg['message'] == 'outgoing'


class SendstatusRequestTestCase(TestCase):

    def setUp(self):
        super(SendstatusRequestTestCase, self).setUp()
        def POST(uri, data):
            data.setdefault('phone_number', '254700111000')
            data.setdefault('action', 'send_status')
            return self.app.post(uri, data, expect_errors=True)
        self.POST = POST

    def test_should_have_required_props(self):
        data = {
        }
        res = self.POST(self.uri, data)
        self.assertEqual(res.status_int, 400)

    def test_response(self):
        outboxmsg = EnvayaOutboxMessage(
              to='254700111999'
            , message='outgoing'
        )
        outboxmsg.put()
        data = {
              'id': str(outboxmsg.key.id())
            , 'status': 'failed'
            , 'error': 'invalid receipient phone number'
        }
        res = self.POST(self.uri, data)
        self.assertEqual(res.status_int, 200)
        #
        # assert req was logged
        msgs = EnvayaInboxMessage.query()
        assert msgs.count() == 1
        msg = msgs.get()
        assert msg.action == 'send_status'
        #
        outboxmsg = outboxmsg.key.get()
        assert outboxmsg.send_status == msg.key