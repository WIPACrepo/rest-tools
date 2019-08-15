#!/usr/bin/env python

import os
import sys
import glob

if sys.version_info < (3, 6):
    print('ERROR: rest_tools requires at least Python 3.6+ to run.')
    sys.exit(1)

try:
    # Use setuptools if available, for install_requires (among other things).
    import setuptools
    from setuptools import setup
except ImportError:
    setuptools = None
    from distutils.core import setup

kwargs = {}

current_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(current_path,'rest_tools','__init__.py')) as f:
    for line in f.readlines():
        if '__version__' in line:
            kwargs['version'] = line.split('=')[-1].split('\'')[1]
            break
    else:
        raise Exception('cannot find __version__')

with open(os.path.join(current_path,'README.md')) as f:
    kwargs['long_description'] = f.read()
    kwargs['long_description_content_type'] = 'text/markdown'

if setuptools is not None:
    # If setuptools is not available, you're on your own for dependencies.
    install_requires = ['tornado>=5.1', 'requests',
                        'requests_toolbelt', 'requests-futures',
                        'sphinx>=1.4', 'coverage>=4.4.2', 'requests-mock',
                        'PyJWT', 'cryptography',
                       ]
    kwargs['install_requires'] = install_requires
    kwargs['zip_safe'] = False

setup(
    name='rest_tools',
    scripts=glob.glob('bin/*'),
    packages=['rest_tools', 'rest_tools.client', 'rest_tools.server'],
    package_data={
        # data files need to be listed both here (which determines what gets
        # installed) and in MANIFEST.in (which determines what gets included
        # in the sdist tarball)
        #'rest_utils.server':['data/etc/*','data/www/*','data/www_templates/*'],
        },
    author="IceCube Collaboration",
    author_email="developers@icecube.wisc.edu",
    url="https://github.com/WIPACrepo/rest-tools",
    license="https://github.com/WIPACrepo/rest-tools/blob/master/LICENSE",
    description="REST tools in python - common code for client and server ",
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        'Operating System :: POSIX :: Linux',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: System :: Distributed Computing',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',

        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        ],
    **kwargs
)
