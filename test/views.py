import os

from google.appengine.dist import use_library
use_library('django', '1.2')
os.environ['DJANGO_SETTINGS_MODULE'] = '__init__'

import webapp2 as webapp
from google.appengine.ext.webapp import template

from lib import receive


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

app = webapp.WSGIApplication(urls, debug=True)
