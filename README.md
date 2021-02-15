# rest-tools

This project contains REST tools in python, as common code for multiple other
projects under https://github.com/WIPACrepo.

All code uses python [asyncio](https://docs.python.org/3/library/asyncio.html),
so is fully asyncronous.

Note that both the client and server assume starting the asyncio loop
happens elsewhere - they do not start the loop themselves.

[![CircleCI](https://circleci.com/gh/WIPACrepo/rest-tools/tree/master.svg?style=shield)](https://circleci.com/gh/WIPACrepo/rest-tools/tree/master) <sup>(master branch)</sup>

## Client

A REST API client exists under `rest_tools.client`.  Use as:

```python
    from rest_tools.client import RestClient

    api = RestClient('http://my.site.here/api', token='XXXX')
    ret = await api.request('GET', '/fruits/apple')
    ret = await api.request('POST', '/fruits', {'name': 'banana'})
```

## Server

A REST API server exists under `rest_tools.server`. Use as:

```python
    import asyncio
    from rest_tools.server import RestServer, RestHandler

    class Fruits(RestHandler):
        def post(self):
            # handle a new fruit
            self.write({})

    server = RestServer()
    server.add_route('/fruits', Fruits)
    server.startup(address='my.site.here', port=8080)
    asyncio.get_event_loop().run_forever()
```

The server uses [Tornado](https://tornado.readthedocs.io) to handle HTTP
connections. It is recommended to use Apache or Nginx as a front-facing proxy,
to handle TLS sessions and non-standard HTTP requests in production.