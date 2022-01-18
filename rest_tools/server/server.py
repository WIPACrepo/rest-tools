"""
Helpers for setting up `Tornado <http://tornado.readthedocs.io>`_ servers.
"""

# fmt:off
# pylint: skip-file

import binascii
import logging
import socket

import tornado.web
from tornado.platform.asyncio import AsyncIOMainLoop

AsyncIOMainLoop().install()


def tornado_logger(handler):
    """Log tornado messages to our logger"""
    if handler.get_status() < 400:
        log_method = logging.debug
    elif handler.get_status() < 500:
        log_method = logging.warning
    else:
        log_method = logging.error
    request_time = 1000.0 * handler.request.request_time()
    log_method("%d %s %.2fms", handler.get_status(), handler._request_summary(), request_time)


class RestServer:
    def __init__(self, log_function=None, cookie_secret=None, max_body_size=None, **kwargs):
        self.routes = []
        self.http_server = None
        self.max_body_size = None
        self.app_args = dict(kwargs)

        if log_function:
            self.app_args['log_function'] = log_function
        else:
            self.app_args['log_function'] = tornado_logger

        if cookie_secret:
            self.app_args['xsrf_cookies'] = True
            self.app_args['cookie_secret'] = binascii.unhexlify(cookie_secret)

    def add_route(self, *args):
        self.routes.append(tuple(args))

    def startup(self, address='localhost', port=8080):
        """
        Start up a Tornado server.

        Note that after calling this method you still need to call
        :code:`IOLoop.current().start()` to start the server.

        Args:
            app (:py:class:`tornado.web.Application`): Tornado application
            address (str): bind address
            port (int): bind port
        """
        logging.warning('tornado bound to %s:%d', address, port)

        app = tornado.web.Application(self.routes, **self.app_args)

        if self.http_server:
            self.http_server.stop()
        self.http_server = tornado.httpserver.HTTPServer(app, xheaders=True, max_body_size=self.max_body_size)
        self.http_server.bind(port, address=address, family=socket.AF_INET)
        self.http_server.start()

    async def stop(self):
        self.http_server.stop()
        await self.http_server.close_all_connections()
