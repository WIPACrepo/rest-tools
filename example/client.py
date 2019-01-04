"""
Example client code.

Add some fruit to the server, then read them back.
"""

import asyncio
import logging

from rest_tools.client import RestClient
from rest_tools.server import Auth

async def main():
    admin_token = Auth('secret').create_token('foo', payload={'role': 'admin'}).decode('utf-8')
    user_token = Auth('secret').create_token('foo', payload={'role': 'user'}).decode('utf-8')

    api = RestClient('http://localhost:8080/api', token=admin_token)
    await api.request('POST', '/fruits', {'name': 'apple'})
    await api.request('POST', '/fruits', {'name': 'banana'})

    api = RestClient('http://localhost:8080/api', token=user_token)
    ret = await api.request('GET', '/fruits')
    if ret != {'apple': {'name': 'apple'}, 'banana': {'name': 'banana'}}:
        print(ret)
        print('FAIL')
    else:
        print('OK')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()