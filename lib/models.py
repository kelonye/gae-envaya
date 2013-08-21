#!/usr/bin/env python
from google.appengine.ext import ndb
from google.appengine._internal.django.utils import simplejson as json

# model to represent:
#  - incoming messages
#  - outgoing messages status notifications
#  - change in device notifications
class EnvayaInboxMessage(ndb.Model):

    ACTIONS = {
          1 : 'incoming'
        , 2: 'outgoing'
        , 3: 'send_status'
        , 4: 'device_status'
        , 5: 'amqp_started'
        , 6: 'forward_sent'
        , 7: 'test'
    }
    date_received = ndb.DateTimeProperty(
        auto_now_add=True
    )
    dump = ndb.TextProperty(
    )

    def __unicode__(self):
        return '%s: %s' % (
              self.date_received
            , self.action
        )

    @property
    def toJSON(self):
        return json.loads(self.dump)

    def get(self, attr):
        return self.toJSON.get(attr, '')

    @property
    def phone_number(self):
        return self.get('phone_number')

    @property
    def action(self):
        return self.get('action')

    # action=incoming properties
    @property
    def frm(self):
        return self.get('from')

    @property
    def message_type(self):
        return self.get('message_type')

    @property
    def message(self):
        return self.get('message')

    @property
    def timestamp(self):
        return self.get('timestamp')

    # action=outgoing properties

    # action=send_status properties
    @property
    def outbox_message(self):
        id = self.get('id')
        if id:
            return ndb.Key(EnvayaOutboxMessage, int(id)).get()
        return

    @property
    def status(self):
        return self.get('status')

    @property
    def error(self):
        return self.get('error')

    # action=device_status properties

    # action=forward_sent properties

    # action=amqp_started properties


# model to represent a `send` event message
# we won't be saving cancel, cancel_all, log and settings events
# we also won't be prioritizing outgoing send events
class EnvayaOutboxMessage(ndb.Model):
    date_sent = ndb.DateTimeProperty(
        auto_now_add=True
    )
    to = ndb.StringProperty(
    )
    message = ndb.TextProperty(
    )
    # send status inbox message
    send_status = ndb.KeyProperty(
        kind=EnvayaInboxMessage
    )

    def __unicode__(self):
        return '%s: %s' % (
              self.date_sent
            , self.to
        )

    @property
    def toDICT(self):
        return {
              'id': str(self.key.id())
            , 'to': self.to
            , 'message': self.message
        }
