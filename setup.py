#!/usr/bin/env python
"""Setup."""


import glob
import os
import subprocess

from setuptools import setup  # type: ignore[import]

subprocess.run(
    "pip install git+https://github.com/WIPACrepo/wipac-dev-tools.git".split(),
    check=True,
)
from wipac_dev_tools import SetupShop  # noqa: E402  # pylint: disable=C0413

shop = SetupShop(
    "rest_tools",
    os.path.abspath(os.path.dirname(__file__)),
    ((3, 6), (3, 8)),
    "REST Tools in Python - Common Utilities for Client and Server",
)

setup(
    scripts=glob.glob("bin/*"),
    url="https://github.com/WIPACrepo/rest-tools",
    # package_data={shop.name: ["py.typed"]},
    **shop.get_kwargs(
        subpackages=["client", "server", "utils"],
        other_classifiers=[
            "Operating System :: POSIX :: Linux",
            "Topic :: Internet :: WWW/HTTP",
            "Topic :: System :: Distributed Computing",
            "Topic :: Software Development :: Libraries",
            "Topic :: Utilities",
            "Programming Language :: Python :: Implementation :: CPython",
        ],
    ),
    zip_safe=False,
    name="bug"
)
