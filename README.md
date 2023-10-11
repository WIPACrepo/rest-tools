<!--- Top of README Badges (automated) --->
[![PyPI](https://img.shields.io/pypi/v/wipac-rest-tools)](https://pypi.org/project/wipac-rest-tools/) [![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/WIPACrepo/rest-tools?include_prereleases)](https://github.com/WIPACrepo/rest-tools/) [![PyPI - License](https://img.shields.io/pypi/l/wipac-rest-tools)](https://github.com/WIPACrepo/rest-tools/blob/master/LICENSE) [![Lines of code](https://img.shields.io/tokei/lines/github/WIPACrepo/rest-tools)](https://github.com/WIPACrepo/rest-tools/) [![GitHub issues](https://img.shields.io/github/issues/WIPACrepo/rest-tools)](https://github.com/WIPACrepo/rest-tools/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/WIPACrepo/rest-tools)](https://github.com/WIPACrepo/rest-tools/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen) 
<!--- End of README Badges (automated) --->
# rest-tools

This project contains REST tools in python, as common code for multiple other
projects under https://github.com/WIPACrepo.

All code uses python [asyncio](https://docs.python.org/3/library/asyncio.html),
so is fully asyncronous.

Note that both the client and server assume starting the asyncio loop
happens elsewhere - they do not start the loop themselves.

## Client

A REST API client exists under `rest_tools.client`.  Use as:

```python
from rest_tools.client import RestClient

api = RestClient('http://my.site.here/api', token='XXXX')
ret = await api.request('GET', '/fruits/apple')
ret = await api.request('POST', '/fruits', {'name': 'banana'})
```

There are several variations of the client for OAuth2/OpenID support:

* [`OpenIDRestClient`](rest_tools/client/openid_client.py#L19) : A child of
  `RestClient` that supports OAuth2 token refresh using the OpenID Connect
  Discovery protocol for an authentication server.

* [`ClientCredentialsAuth`](rest_tools/client/client_credentials.py#L11) : Uses
  `OpenIDRestClient` in combination with OAuth2 client credentials (client ID
  and secret) for service-based auth. Use this for long-lived services that
  need to perform REST API calls.

* [`DeviceGrantAuth`](rest_tools/client/device_client.py#L125) /
  [`SavedDeviceGrantAuth`](rest_tools/client/device_client.py#L162) : Uses
  `OpenIDRestClient` to perform a "device" login for a user. Use this for
  user-based terminal applications that need to perform REST API calls.
  The `SavedDeviceGrantAuth` can save the refresh token to disk, allowing
  repeated application sessions without having to log in again.

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

### Handling Arguments Server-side

`server.ArgumentHandler` is a robust wrapper around `argparse.ArgumentParser`, extended for use in handling REST arguments, both query arguments and JSON-encoded body arguments. The intended design of this class is to follow the `argparse` pattern as closely as possible.


```python
from rest_tools.server import RestHandler, ArgumentHandler, ArgumentSource

class Fruits(RestHandler):

    def get(self):
        argo = ArgumentHandler(ArgumentSource.QUERY_ARGUMENTS, self)

        argo.add_argument('name', type=str)  # de-facto required
        argo.add_argument('alias', dest='other_names', type=str, nargs='*', default=[])  # list

        argo.add_argument('is-citrus', type=bool, default=False)
        argo.add_argument('amount', type=float, required=True)

        args = argo.parse_args()

        fruit = get_fruit(args.name, args.other_names, args.is_citrus, args.amount)

        ...

    def post(self):
        argo = ArgumentHandler(ArgumentSource.JSON_BODY_ARGUMENTS, self)

        argo.add_argument('name', type=str)  # de-facto required
        argo.add_argument('other-names', type=list, default=[])

        argo.add_argument('supply', type=dict, required=True)

        def _origin(val):
            try:
                return {'USA': 'United States of America', 'MEX': 'Mexico'}[val]
            except KeyError:
                # raise a ValueError or TypeError to propagate a 400 Error
                raise ValueError('Invalid origin')

        argo.add_argument('country_code', dest='origin', type=_origin, required=True)

        args = argo.parse_args()

        add_to_basket(args.name, args.other_names, args.supply, args.origin)

        ...

```