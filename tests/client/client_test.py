"""
Test script for RestClient
"""

import logging
logger = logging.getLogger('rest_client')

import os, sys, time
import tempfile
import shutil
import random
import string

import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
import requests_mock
from requests.exceptions import Timeout, SSLError

import rest_tools.client


class rest_client_test(unittest.TestCase):
    def setUp(self):
        super(rest_client_test,self).setUp()

        curdir = os.getcwd()
        self.test_dir = tempfile.mkdtemp(dir=curdir)
        os.symlink(os.path.join(curdir, 'rest_tools'),
                   os.path.join(self.test_dir, 'rest_tools'))
        os.chdir(self.test_dir)
        def cleanup():
            os.chdir(curdir)
            shutil.rmtree(self.test_dir)
        self.addCleanup(cleanup)

    @requests_mock.mock()
    def test_01_init(self, mock):
        """Test init"""
        address = 'http://test'
        auth_key = 'passkey'
        rpc = rest_tools.client.RestClient(address, auth_key)
        rpc.close()

    @requests_mock.mock()
    async def test_10_request(self, mock):
        """Test request"""
        address = 'http://test'
        auth_key = 'passkey'
        result = {'result':'the result'}

        rpc = rest_tools.client.RestClient(address, auth_key, timeout=0.1)

        def response(req, ctx):
            body = rest_tools.client.json_decode(req.body)
            return rest_tools.client.json_encode(result).encode('utf-8')
        mock.post('/test', content=response)

        ret = await rpc.request('POST','test',{})

        self.assertTrue(mock.called)
        self.assertEqual(ret, result)

        result2 = {'result2':'the result 2'}
        def response(req, ctx):
            body = rest_tools.client.json_decode(req.body)
            return rest_tools.client.json_encode(result2).encode('utf-8')
        mock.post('/test2', content=response)
        ret = await rpc.request('POST','/test2')

        self.assertTrue(mock.called)
        self.assertEqual(ret, result2)

    @requests_mock.mock()
    async def test_11_request(self, mock):
        """Test request"""
        address = 'http://test'
        auth_key = 'passkey'
        result = ''

        rpc = rest_tools.client.RestClient(address, auth_key, timeout=0.1)

        mock.get('/test', content=b'')

        ret = await rpc.request('GET','test',{})

        self.assertTrue(mock.called)
        self.assertIs(ret, None)

    @requests_mock.mock()
    async def test_20_timeout(self, mock):
        """Test timeout"""
        address = 'http://test'
        auth_key = 'passkey'
        result = 'the result'

        rpc = rest_tools.client.RestClient(address, auth_key, timeout=0.1, backoff=False)

        mock.post('/test', exc=Timeout)

        with self.assertRaises(Timeout):
            ret = await rpc.request('POST','test',{})

    @requests_mock.mock()
    async def test_21_ssl_error(self, mock):
        """Test ssl error"""
        address = 'http://test'
        auth_key = 'passkey'
        result = 'the result'

        rpc = rest_tools.client.RestClient(address, auth_key, timeout=0.1, backoff=False)

        mock.post('/test', exc=SSLError)

        with self.assertRaises(SSLError):
            ret = await rpc.request('POST','test',{})

    @requests_mock.mock()
    async def test_22_request(self, mock):
        """Test request"""
        address = 'http://test'
        auth_key = 'passkey'
        result = ''

        rpc = rest_tools.client.RestClient(address, auth_key, timeout=0.1)

        mock.get('/test', content=b'{"foo"}')

        with self.assertRaises(Exception):
            ret = await rpc.request('GET','test',{})

    @requests_mock.mock()
    def test_90_request(self, mock):
        """Test request"""
        address = 'http://test'
        auth_key = 'passkey'
        result = {'result':'the result'}

        rpc = rest_tools.client.RestClient(address, auth_key, timeout=0.1)

        def response(req, ctx):
            body = rest_tools.client.json_decode(req.body)
            return rest_tools.client.json_encode(result).encode('utf-8')
        mock.post('/test', content=response)

        ret = rpc.request_seq('POST','test',{})

        self.assertTrue(mock.called)
        self.assertEqual(ret, result)

    @requests_mock.mock()
    async def test_91_request(self, mock):
        """Test request"""
        address = 'http://test'
        auth_key = 'passkey'
        result = {'result':'the result'}

        rpc = rest_tools.client.RestClient(address, auth_key, timeout=0.1)

        def response(req, ctx):
            body = rest_tools.client.json_decode(req.body)
            return rest_tools.client.json_encode(result).encode('utf-8')
        mock.post('/test', content=response)

        ret = rpc.request_seq('POST','test',{})

        self.assertTrue(mock.called)
        self.assertEqual(ret, result)

    @requests_mock.mock()
    async def test_92_request(self, mock):
        """Test request"""
        address = 'http://test'
        auth_key = 'passkey'
        result = {'result':'the result'}

        rpc = rest_tools.client.RestClient(address, auth_key, timeout=0.1)

        def response(req, ctx):
            raise Exception()
        mock.post('/test', content=response)

        with self.assertRaises(Exception):
            rpc.request_seq('POST','test',{})

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    alltests = loader.getTestCaseNames(rest_client_test)
    suite.addTests(loader.loadTestsFromNames(alltests,rest_client_test))
    return suite
