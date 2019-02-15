#!/usr/bin/env python3
from distutils.core import setup

setup(
    name="a38",
    version="0.1.0",
    description="parse and generate Italian Fattura Elettronica",
    author="Enrico Zini",
    author_email="enrico@truelite.it",
    url="https://github.com/Truelite/python-a38/blob/master/a38/fattura.py",
    license="https://www.apache.org/licenses/LICENSE-2.0.html",
    packages=["a38"],
    install_requires=["dateutil", "pytz", "asn1crypto"],
    test_requires=["dateutil", "pytz", "asn1crypto"],
)
