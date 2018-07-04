
from setuptools import setup

setup(
    name='cloudify-ecosystem-test',
    version='2.0',
    license='LICENSE',
    packages=[
        'ecosystem_tests',
    ],
    description='Stuff that Ecosystem Tests Use',
    install_requires=[
        'testtools',
        'cloudify-rest-client>=3.4.1'
    ]
)
