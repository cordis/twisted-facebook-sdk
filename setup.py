#!/usr/bin/env python
from setuptools import setup

setup(
    name='twisted-facebook-sdk',
    version='0.10.0-alpha1',
    description='This client library is designed to support the Facebook '
                'Graph API and the official Facebook JavaScript SDK, which '
                'is the canonical way to implement Facebook authentication.',
    author='Facebook',
    maintainer='Sergey Yushkeev',
    maintainer_email='saint.cordis@gmail.com',
    url='https://github.com/cordis/twisted-facebook-sdk',
    license='Apache',
    packages=['txfacebook'],
    long_description=open('README.rst').read(),
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=[
        'treq',
        'pyOpenSSL',
        'service_identity',
    ],
)
