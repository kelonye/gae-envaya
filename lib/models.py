#!/usr/bin/env python
from google.appengine.ext import ndb
from google.appengine._internal.django.utils import simplejson as json


ACTIONS = {
    1 : 'incoming',
    2: 'outgoing',
    3: 'send_status',
    4: 'device_status',
    5: 'amqp_started',
    6: 'forward_sent',
    7: 'test'
}


class EnvayaInboxMessage(ndb.Model):
    date_received = ndb.DateTimeProperty(
        auto_now_add=True
    )
    frm = ndb.StringProperty(
        required=True
    )
    message = ndb.TextProperty(
        required=True
    )
    def __unicode__(self):
        return '%s: %s' % (
            self.date_received, self.action
        )


class EnvayaOutboxMessage(ndb.Model):
    date_sent = ndb.DateTimeProperty(
        auto_now_add=True
    )
    to = ndb.StringProperty(
        required=True
    )
    message = ndb.TextProperty(
        required=True
    )
    send_status = ndb.StringProperty(
        default='queued',
        choices=['queued', 'failed', 'cancelled', 'sent']
    )
    send_error = ndb.TextProperty(
        default=''
    )

    def __unicode__(self):
        return '%s: %s' % (
            self.date_sent, self.to
        )

    @property
    def toDICT(self):
        return {
            'id': str(self.key.id()),
            'to': self.to,
            'message': self.message
        }
