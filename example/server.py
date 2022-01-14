"""
Example server code.

Make a fruit API.
"""

# fmt: off

import asyncio
import logging

from rest_tools.server import (
    RestHandler,
    RestHandlerSetup,
    RestServer,
    role_authorization,
)
from rest_tools.utils.json_util import json_decode


class Fruits(RestHandler):
    def initialize(self, fruit, *args, **kwargs):
        super(Fruits, self).initialize(*args, **kwargs)
        self.fruit = fruit

    @role_authorization(roles=['admin','user'])
    async def get(self):
        """Write existing fruits"""
        logging.info('fruits: %r', self.fruit)
        self.write(self.fruit)

    @role_authorization(roles=['admin'])
    async def post(self):
        """Handle a new fruit"""
        body = json_decode(self.request.body)
        logging.info('body: %r', body)
        self.fruit[body['name']] = body
        self.write({})


logging.basicConfig(level=logging.DEBUG)

args = RestHandlerSetup({
    'auth':{
        'secret':'secret',
    },
    'debug': True
})
args['fruit'] = {} # this could be a DB, but a dict works for now

server = RestServer(debug=True)
server.add_route('/api/fruits', Fruits, args)
server.startup(address='localhost', port=8080)

asyncio.get_event_loop().run_forever()
