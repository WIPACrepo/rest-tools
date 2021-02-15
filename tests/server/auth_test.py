"""Test script for auth."""

# fmt:off
# mypy: ignore-errors
# pylint: skip-file

import logging
import os
import shutil
import tempfile
import time
import unittest

import jwt

# local imports
from rest_tools.server import auth

logger = logging.getLogger('auth_test')


class auth_test(unittest.TestCase):
    def setUp(self):
        super(auth_test,self).setUp()
        self.test_dir = tempfile.mkdtemp(dir=os.getcwd())
        def cleanup():
            shutil.rmtree(self.test_dir)
        self.addCleanup(cleanup)

    def test_01_create_token(self):
        a = auth.Auth('secret')
        now = time.time()
        tok = a.create_token('subj', expiration=20, type='foo')

        data = jwt.decode(tok, 'secret', algorithms=['HS512'])
        self.assertEqual(data['sub'], 'subj')
        self.assertEqual(data['type'], 'foo')
        self.assertLess(data['exp'], now+21)
        self.assertGreater(data['nbf'], now-1)

    def test_10_validate(self):
        a = auth.Auth('secret')
        now = time.time()
        tok = a.create_token('subj', expiration=20, type='foo')
        data = a.validate(tok)
        self.assertEqual(data['sub'], 'subj')
        self.assertEqual(data['type'], 'foo')

        tok = jwt.encode({'sub':'subj','exp':now-1}, 'secret', algorithm='HS512')
        with self.assertRaises(Exception):
            a.validate(tok)


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    alltests = loader.getTestCaseNames(auth_test)
    suite.addTests(loader.loadTestsFromNames(alltests,auth_test))
    return suite
