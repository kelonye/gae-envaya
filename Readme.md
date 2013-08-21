Install
---

    $ pip install gae-envaya

Use
---

```python

from gae_envaya import receive

class ReceiveHandler(webapp.RequestHandler):

    @receive('--phone-number--', '--password--')
    def post(self):
        if self.request.get('action') == 'incoming':
            self.envaya.queue({
                'message': 'outgoing1'
            })
            self.envaya.queue({
                'to': '254700111444',
                'message': 'outgoing2'
            })

```
Example
---
    $ make deps example

Test
---

    $ make deps test