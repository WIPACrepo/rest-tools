"""Test script for config."""

# fmt:off
# pylint: skip-file

import logging
import os
import shutil
import tempfile
import unittest

# local imports
from rest_tools.utils import from_environment

logger = logging.getLogger('config_test')


class config_test(unittest.TestCase):
    def setUp(self):
        super(config_test,self).setUp()
        self.test_dir = tempfile.mkdtemp(dir=os.getcwd())

        def cleanup():
            shutil.rmtree(self.test_dir)

        self.addCleanup(cleanup)
        environ = os.environ.copy()

        def clean_env():
            for k in list(os.environ):
                if k not in environ:
                    del os.environ[k]

        self.addCleanup(clean_env)

    def test_01_from_environment(self):
        with self.assertRaises(OSError):
            from_environment({'FOO': None})

        os.environ['FOO'] = 'bar'
        config = from_environment({'FOO': None})
        self.assertEqual(config['FOO'], 'bar')

    def test_10_from_environment(self):
        os.environ['FOO'] = 'bar'
        with self.assertRaises(ValueError):
            from_environment({'FOO': 123})

        os.environ['FOO'] = '543'
        config = from_environment({'FOO': 123})
        self.assertEqual(config['FOO'], 543)

        os.environ['FOO'] = '543.'
        config = from_environment({'FOO': 123.})
        self.assertEqual(config['FOO'], 543.)

        os.environ['FOO'] = 't'
        config = from_environment({'FOO': False})
        self.assertEqual(config['FOO'], True)


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    alltests = loader.getTestCaseNames(config_test)
    suite.addTests(loader.loadTestsFromNames(alltests,config_test))
    return suite
