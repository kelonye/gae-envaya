import os
import webapp2 as webapp
from lib import receive
from google.appengine.ext.webapp import template


class ReceiveHandler(webapp.RequestHandler):

    @receive('254700111000', 't')
    def post(self):
        if self.request.get('action') == 'incoming':
            self.envaya.queue({
                'message': 'outgoing1'
            })
            self.envaya.queue({
                'to': '254700111444',
                'message': 'outgoing2'
            })

urls = [
    ('/receive/', ReceiveHandler),
]
